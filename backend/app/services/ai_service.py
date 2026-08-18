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


def _first_sentences(text: str, limit: int) -> list[str]:
    compact = " ".join(text.split())
    raw_sentences = compact.replace("?", ".").replace("!", ".").split(".")
    sentences = [sentence.strip() for sentence in raw_sentences if len(sentence.strip()) > 40]
    return sentences[:limit]


ai_service = AIService()

