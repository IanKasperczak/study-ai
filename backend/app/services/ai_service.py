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
        return await self._complete(prompt=prompt, fallback=fallback, max_tokens=1024)

    async def answer_question(self, question: str, context: str) -> str:
        prompt = (
            "Responde la pregunta usando solamente el contexto provisto. "
            "Si la respuesta no esta en el contexto, di que no aparece en los documentos.\n\n"
            f"Pregunta: {question}\n\nContexto:\n{context}"
        )
        fallback = self._fallback_chat_answer(question=question, context=context)
        return await self._complete(prompt=prompt, fallback=fallback, max_tokens=512)

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

    async def _complete(self, prompt: str, fallback: str, max_tokens: int) -> str:
        config = self._client_config()
        if config is None:
            return fallback

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=config["api_key"], base_url=config["base_url"])
            response = await client.chat.completions.create(
                model=config["model"],
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un tutor de estudio preciso. No inventes informacion.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=max_tokens,
                timeout=settings.ai_timeout_seconds,
            )
            return response.choices[0].message.content or fallback
        except Exception as exc:
            return f"{fallback}\n\nNota tecnica: no se pudo usar el proveedor de IA ({exc})."

    async def _complete_json(self, prompt: str, max_tokens: int = 1024) -> dict | None:
        """Ask the model for a JSON object. Returns None on any failure."""
        config = self._client_config()
        if config is None:
            return None

        try:
            import json

            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=config["api_key"], base_url=config["base_url"])
            response = await client.chat.completions.create(
                model=config["model"],
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente que solo emite JSON valido, sin markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=max_tokens,
                timeout=settings.ai_timeout_seconds,
            )
            content = response.choices[0].message.content or ""
            return _extract_json_object(content)
        except Exception:
            return None

    def _client_config(self) -> dict[str, str | None] | None:
        """Resolve the active AI provider from settings.

        Supported providers:
        - "ollama": any model served by a local Ollama instance (OpenAI-compatible
          endpoint at /v1). No API key required.
        - "openai": the official OpenAI API (or any OpenAI-compatible provider when
          OPENAI_BASE_URL is configured, e.g. Groq, OpenRouter, together.ai).
        - "": auto-detect from the configured environment variables.
        """
        provider = settings.ai_provider or self._detect_provider()

        if provider == "ollama":
            return {
                "api_key": "ollama",
                "base_url": f"{settings.ollama_base_url.rstrip('/')}/v1",
                "model": settings.ollama_model,
            }

        if provider == "openai":
            if not settings.openai_api_key:
                return None
            return {
                "api_key": settings.openai_api_key,
                "base_url": settings.openai_base_url or None,
                "model": settings.openai_chat_model,
            }

        return None

    def _detect_provider(self) -> str:
        # Detection looks at the environment directly so that default values in
        # settings (e.g. OLLAMA_MODEL=llama3.2) never enable a provider implicitly.
        import os

        if os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_BASE_URL"):
            return "openai"
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


def _first_sentences(text: str, limit: int) -> list[str]:
    compact = " ".join(text.split())
    raw_sentences = compact.replace("?", ".").replace("!", ".").split(".")
    sentences = [sentence.strip() for sentence in raw_sentences if len(sentence.strip()) > 40]
    return sentences[:limit]


ai_service = AIService()

