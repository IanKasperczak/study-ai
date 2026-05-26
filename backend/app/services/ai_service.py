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
        return await self._complete(prompt=prompt, fallback=fallback)

    async def answer_question(self, question: str, context: str) -> str:
        prompt = (
            "Responde la pregunta usando solamente el contexto provisto. "
            "Si la respuesta no esta en el contexto, di que no aparece en los documentos.\n\n"
            f"Pregunta: {question}\n\nContexto:\n{context}"
        )
        fallback = self._fallback_chat_answer(question=question, context=context)
        return await self._complete(prompt=prompt, fallback=fallback)

    async def _complete(self, prompt: str, fallback: str) -> str:
        if not settings.openai_api_key:
            return fallback

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=settings.openai_chat_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un tutor de estudio preciso. No inventes informacion.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content or fallback
        except Exception as exc:
            return f"{fallback}\n\nNota tecnica: no se pudo usar OpenAI en esta ejecucion ({exc})."

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

