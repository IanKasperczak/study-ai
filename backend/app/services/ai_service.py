from app.core.config import get_settings

settings = get_settings()


class AIService:
    async def generate_study_output(self, action: str, instruction: str, context: str) -> str:
        prompt = (
            f"{instruction}\n\n"
            "Usa solamente el contexto provisto. Si falta informacion, dilo con claridad.\n\n"
            f"Contexto:\n{context}"
        )
        fallback = self._fallback_study_output(action=action, context=context)
        return await self._complete(prompt=prompt, fallback=fallback, max_tokens=1536)

    async def answer_question(self, question: str, context: str) -> str:
        prompt = (
            "Responde la pregunta usando solamente el contexto provisto. "
            "Si la respuesta no esta en el contexto, di que no aparece en los documentos.\n\n"
            f"Pregunta: {question}\n\nContexto:\n{context}"
        )
        fallback = self._fallback_chat_answer(question=question, context=context)
        return await self._complete(prompt=prompt, fallback=fallback, max_tokens=900)

    async def refine_topic_titles(
        self, titles: list[str], document_excerpt: str
    ) -> list[tuple[str, str]] | None:
        """Polish heuristic topic titles/descriptions with the AI.

        Returns (title, description) pairs in the SAME order/count as titles, or
        None when the provider is unavailable or the reply is not usable JSON.
        """
        if not titles:
            return None

        numbered = "\n".join(f"{index + 1}. {title}" for index, title in enumerate(titles))
        prompt = (
            "Recibiras las secciones de un documento y un fragmento de su inicio.\n"
            "Reescribe cada seccion con un titulo natural y breve, y una descripcion "
            "de una frase sobre su contenido.\n"
            "Debes devolver EXACTAMENTE el mismo numero de secciones, en el mismo orden.\n"
            'Responde SOLO con JSON: {"topics": [{"title": "...", "description": "..."}]}\n\n'
            f"Secciones:\n{numbered}\n\n"
            f"Fragmento del documento:\n{document_excerpt[:2000]}\n"
        )

        payload = await self._complete_json(prompt)
        if payload is None:
            return None

        tree = _parse_topic_tree(payload)
        if tree is None or len(tree.topics) != len(titles):
            return None

        return [
            (topic.title or titles[index], topic.description)
            for index, topic in enumerate(tree.topics)
        ]

    async def filter_valid_topics(self, titles: list[str]) -> list[bool] | None:
        """Ask the AI which heuristically-detected section titles are real
        study topics versus noise the font-size heuristic mistakenly picked
        up (author names, cover/title-page text, repeated headers or
        footers, sentence fragments cut in half by the PDF extractor).

        Returns booleans in the SAME order/count as titles, or None when the
        provider is unavailable or the reply is not usable. Kept as a
        separate, lightweight call from refine_topic_titles: rewriting every
        title/description already strains the output budget on large
        documents, and asking for a true/false per topic doesn't help --
        tested against a real 136-topic batch, that shape made the model
        loop past the input length repeating "true" without ever emitting a
        closing brace. Asking for just the indices that are noise keeps the
        reply tiny (most topics are valid) and lets it terminate naturally.
        """
        if not titles:
            return None

        numbered = "\n".join(f"{index + 1}. {title}" for index, title in enumerate(titles))
        prompt = (
            "Estos titulos de seccion fueron detectados automaticamente por tamano "
            "de fuente en un documento de estudio. La mayoria son temas de "
            "contenido real (capitulos, secciones, subsecciones); algunos son "
            "ruido, por ejemplo nombres de autores o profesores, titulos de "
            "tapa/portada o el titulo general del documento/compendio, secciones "
            "que no son contenido de estudio en si mismas (bibliografia, "
            "referencias, indice, glosario, apendice, anexos), encabezados o "
            "pies de pagina repetidos, o fragmentos de una oracion cortados a "
            "la mitad.\n"
            "Responde SOLO con los numeros de los titulos que son ruido (no "
            "temas reales), como JSON compacto, sin explicaciones. Si ninguno "
            "es ruido, devolve una lista vacia.\n"
            'Formato: {"invalid_indices": [3, 12, 45]}\n\n'
            f"Titulos:\n{numbered}\n"
        )

        payload = await self._complete_json(prompt, max_tokens=1024)
        if payload is None:
            return None

        indices = _parse_invalid_indices(payload)
        if indices is None:
            return None

        valid = [True] * len(titles)
        for index in indices:
            if isinstance(index, int) and 1 <= index <= len(titles):
                valid[index - 1] = False
        return valid

    async def generate_quiz(self, context: str, num_questions: int = 5) -> list[dict] | None:
        """Generate a multiple-choice quiz from a Subtema's context (the same
        chunk context assembled by rag_service.build_context for summaries
        and chat). Returns a list of {question, options, correct_index,
        explanation} dicts, or None when the provider is unavailable or the
        reply isn't usable JSON -- callers decide the user-facing fallback.
        """
        num_questions = max(1, min(num_questions, 10))
        prompt = (
            f"Genera {num_questions} preguntas de opcion multiple para estudiar, "
            "basadas UNICAMENTE en el contexto provisto. Cada pregunta debe tener "
            "exactamente 4 opciones, con una sola correcta, y una explicacion breve "
            "de por que esa es la respuesta correcta.\n"
            "Responde SOLO con JSON compacto, sin explicaciones fuera del JSON.\n"
            'Formato: {"questions": [{"question": "...", "options": ["...", "...", "...", "..."], '
            '"correct_index": 0, "explanation": "..."}]}\n'
            "correct_index es la posicion (empezando en 0) de la opcion correcta dentro de options.\n\n"
            f"Contexto:\n{context}"
        )

        payload = await self._complete_json(prompt, max_tokens=2048)
        if payload is None:
            return None

        quiz = _parse_quiz(payload)
        if quiz is None or not quiz.questions:
            return None

        questions = []
        for item in quiz.questions:
            if len(item.options) < 2 or not (0 <= item.correct_index < len(item.options)):
                continue
            questions.append(
                {
                    "question": item.question,
                    "options": item.options,
                    "correct_index": item.correct_index,
                    "explanation": item.explanation,
                }
            )
        return questions or None

    async def embed_texts(self, texts: list[str], input_type: str) -> list[list[float]] | None:
        """Embed a batch of texts with the active provider's embedding model.

        input_type is "query" for a search question or "passage" for a stored
        chunk. NIM's asymmetric models (e5, bge) need this distinction to embed
        queries and documents into a comparable space; other providers ignore it.
        Returns None (never raises) when no provider is configured or the call
        fails, so callers can fall back to lexical search.
        """
        if not texts:
            return []

        config = self._client_config()
        if config is None or not config.get("embed_model"):
            return None

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=config["api_key"], base_url=config["base_url"])
            extra_body = {"input_type": input_type} if config["provider"] == "nim" else None
            response = await client.embeddings.create(
                model=config["embed_model"],
                input=texts,
                extra_body=extra_body,
                timeout=settings.ai_timeout_seconds,
            )
            return [item.embedding for item in response.data]
        except Exception:
            return None

    async def _complete(self, prompt: str, fallback: str, max_tokens: int) -> str:
        config = self._client_config()
        if config is None:
            return fallback

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=config["api_key"], base_url=config["base_url"])
        extra_body = _disable_thinking(config)

        last_error: Exception | None = None
        for model in config["models"]:
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un tutor de estudio preciso. No inventes informacion.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                    extra_body=extra_body,
                    timeout=settings.ai_timeout_seconds,
                )
                choice = response.choices[0]
                content = choice.message.content
                if content:
                    if choice.finish_reason == "length":
                        content = _trim_to_sentence_boundary(content)
                    return content
            except Exception as exc:
                last_error = exc

        return f"{fallback}\n\nNota tecnica: no se pudo usar el proveedor de IA ({last_error})."

    async def _complete_json(self, prompt: str, max_tokens: int = 1024) -> dict | None:
        """Ask the model for a JSON object. Returns None on any failure.

        Tries each configured model in order (fast model first, heavier
        fallback second for NIM) -- both on a hard error and on a reply that
        doesn't parse as usable JSON, since a model can "succeed" with junk.
        """
        config = self._client_config()
        if config is None:
            return None

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=config["api_key"], base_url=config["base_url"])
        extra_body = _disable_thinking(config)

        for model in config["models"]:
            try:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un asistente que solo emite JSON valido, sin markdown.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=max_tokens,
                    extra_body=extra_body,
                    timeout=settings.ai_timeout_seconds,
                )
                content = response.choices[0].message.content or ""
                parsed = _extract_json_object(content)
                if parsed is not None:
                    return parsed
            except Exception:
                continue

        return None

    def _client_config(self) -> dict[str, str | None] | None:
        """Resolve the active AI provider from settings.

        Supported providers:
        - "ollama": any model served by a local Ollama instance (OpenAI-compatible
          endpoint at /v1). No API key required.
        - "openai": the official OpenAI API (or any OpenAI-compatible provider when
          OPENAI_BASE_URL is configured, e.g. Groq, OpenRouter, together.ai).
        - "nim": NVIDIA NIM, hosted (build.nvidia.com/integrate.api.nvidia.com,
          requires NVIDIA_API_KEY) or self-hosted (point NIM_BASE_URL at your own
          NIM container; no key needed there). Also OpenAI-compatible.
        - "": auto-detect from the configured environment variables.
        """
        provider = settings.ai_provider or self._detect_provider()

        if provider == "ollama":
            return {
                "provider": "ollama",
                "api_key": "ollama",
                "base_url": f"{settings.ollama_base_url.rstrip('/')}/v1",
                "models": [settings.ollama_model],
                "embed_model": settings.ollama_embed_model,
            }

        if provider == "nim":
            # Try the fast model first; if it errors out or times out, fall
            # back to the heavier one instead of failing the whole request.
            models = _dedupe([settings.nim_model, settings.nim_fallback_model])
            return {
                "provider": "nim",
                # Self-hosted NIM containers ignore the key but the OpenAI SDK
                # still requires a non-empty string.
                "api_key": settings.nim_api_key or "not-needed",
                "base_url": settings.nim_base_url,
                "models": models,
                "embed_model": settings.nim_embed_model,
            }

        if provider == "openai":
            if not settings.openai_api_key:
                return None
            return {
                "provider": "openai",
                "api_key": settings.openai_api_key,
                "base_url": settings.openai_base_url or None,
                "models": [settings.openai_chat_model],
                "embed_model": settings.openai_embed_model,
            }

        return None

    def _detect_provider(self) -> str:
        # Detection looks at the environment directly so that default values in
        # settings (e.g. OLLAMA_MODEL=llama3.2, NIM_BASE_URL) never enable a
        # provider implicitly.
        import os

        if os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_BASE_URL"):
            return "openai"
        if os.getenv("NVIDIA_API_KEY") or os.getenv("NIM_API_KEY"):
            return "nim"
        if os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_MODEL"):
            return "ollama"
        return ""

    def _fallback_study_output(self, action: str, context: str) -> str:
        sentences = _first_sentences(context, limit=6)
        if action == "simple_explanation":
            return (
                "Explicacion simple basada en los documentos:\n\n"
                + "\n".join(f"- {sentence}" for sentence in sentences[:5])
            )

        return "Resumen basado en los documentos:\n\n" + "\n".join(
            f"- {sentence}" for sentence in sentences[:6]
        )

    def _fallback_chat_answer(self, question: str, context: str) -> str:
        sentences = _first_sentences(context, limit=4)
        if not sentences:
            return "No encontre informacion suficiente en los documentos cargados."

        return (
            "Con la informacion cargada, esto es lo mas relevante que encontre:\n\n"
            + "\n".join(f"- {sentence}" for sentence in sentences)
            + "\n\nPara respuestas mas elaboradas, configura OPENAI_API_KEY en el backend."
        )


def _disable_thinking(config: dict) -> dict | None:
    """Turn off reasoning/"thinking" mode where the provider supports it.

    Some NIM models default to emitting their internal chain-of-thought
    before the actual answer. When they do, that reasoning can eat the
    whole max_tokens budget (leaving no room for the real answer) or, worse,
    leak straight into the visible response instead of staying in the
    separate reasoning_content field. Neither is useful here, so it's
    disabled for every call.
    """
    if config["provider"] == "nim":
        return {"chat_template_kwargs": {"enable_thinking": False}}
    return None


def _trim_to_sentence_boundary(text: str) -> str:
    """Cut a response that got truncated by max_tokens back to the end of
    its last complete sentence/paragraph, so it never stops mid-word or
    mid-phrase. Only called when the API reports finish_reason == "length".
    """
    text = text.rstrip()
    if not text:
        return text

    last_end = max(text.rfind("."), text.rfind("!"), text.rfind("?"), text.rfind("\n\n"))
    if last_end != -1:
        trimmed = text[: last_end + 1].rstrip()
        # If almost nothing survives (e.g. one stray period near the
        # start), keep looking for a softer boundary below instead.
        if len(trimmed) >= len(text) * 0.4:
            return trimmed

    # No full sentence finished within the token budget at all (can happen
    # with a very tight max_tokens). Falling back to the raw cutoff would
    # still end mid-word, so cut at the last complete word instead and mark
    # it as unfinished rather than pretending it's a finished thought.
    last_space = text.rfind(" ")
    if last_space > len(text) * 0.4:
        return text[:last_space].rstrip() + "..."
    return text


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _extract_json_object(content: str) -> dict | None:
    import json

    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = content[start : end + 1]
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _parse_topic_tree(payload: dict):
    try:
        from pydantic import ValidationError

        from app.models.schemas import AiTopicTree

        return AiTopicTree.model_validate(payload)
    except (ValidationError, ValueError):
        return None


def _parse_invalid_indices(payload: dict) -> list[int] | None:
    try:
        from pydantic import ValidationError

        from app.models.schemas import AiInvalidTopicIndices

        return AiInvalidTopicIndices.model_validate(payload).invalid_indices
    except (ValidationError, ValueError):
        return None


def _parse_quiz(payload: dict):
    try:
        from pydantic import ValidationError

        from app.models.schemas import AiQuiz

        return AiQuiz.model_validate(payload)
    except (ValidationError, ValueError):
        return None


def _first_sentences(text: str, limit: int) -> list[str]:
    compact = " ".join(text.split())
    raw_sentences = compact.replace("?", ".").replace("!", ".").split(".")
    sentences = [sentence.strip() for sentence in raw_sentences if len(sentence.strip()) > 40]
    return sentences[:limit]


ai_service = AIService()

