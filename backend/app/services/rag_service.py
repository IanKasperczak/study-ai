import re
from collections import Counter


class RAGService:
    def search(
        self,
        project: dict,
        query: str,
        topic_ids: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict]:
        candidates = self.get_chunks_for_topics(project=project, topic_ids=topic_ids or [], limit=0)
        query_terms = _terms(query)

        if not query_terms:
            return candidates[:limit]

        scored: list[tuple[int, dict]] = []
        for chunk in candidates:
            chunk_terms = Counter(_terms(chunk["text"]))
            score = sum(chunk_terms.get(term, 0) for term in query_terms)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        if not scored:
            return candidates[:limit]
        return [chunk for _, chunk in scored[:limit]]

    def get_chunks_for_topics(self, project: dict, topic_ids: list[str], limit: int = 8) -> list[dict]:
        chunks = project["chunks"]
        if topic_ids:
            selected_ids = set()
            for topic in project["topics"]:
                if topic["id"] in topic_ids:
                    selected_ids.update(topic["chunk_ids"])
            chunks = [chunk for chunk in chunks if chunk["id"] in selected_ids]

        return chunks if limit == 0 else chunks[:limit]

    def build_context(self, chunks: list[dict]) -> str:
        return "\n\n".join(
            f"Source: {chunk['source']} | Chunk: {chunk['id']}\n{chunk['text']}" for chunk in chunks
        )


def _terms(text: str) -> list[str]:
    return [term.lower() for term in re.findall(r"\b[\wáéíóúñü]{4,}\b", text.lower())]


rag_service = RAGService()
