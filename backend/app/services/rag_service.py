import math
import re
from collections import Counter

from app.services.ai_service import ai_service


class RAGService:
    async def search(
        self,
        project: dict,
        query: str,
        topic_ids: list[str] | None = None,
        limit: int = 5,
    ) -> list[dict]:
        candidates = self.get_chunks_for_topics(project=project, topic_ids=topic_ids or [], limit=0)

        semantic = await self._semantic_search(candidates, query, limit)
        if semantic is not None:
            return semantic

        return self._lexical_search(candidates, query, limit)

    async def _semantic_search(
        self, candidates: list[dict], query: str, limit: int
    ) -> list[dict] | None:
        """Rank chunks by embedding similarity. Returns None (never an empty
        list) when embeddings are not available, so callers know to fall back
        to lexical search instead of treating "no semantic result" as "no match".
        """
        if not candidates or any(chunk.get("embedding") is None for chunk in candidates):
            return None

        query_vectors = await ai_service.embed_texts([query], input_type="query")
        if not query_vectors:
            return None
        query_vector = query_vectors[0]

        scored = [
            (_cosine_similarity(query_vector, chunk["embedding"]), chunk)
            for chunk in candidates
        ]
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:limit]]

    def _lexical_search(self, candidates: list[dict], query: str, limit: int) -> list[dict]:
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
            matched = False
            topics = {topic["id"]: topic for topic in project["topics"]}
            children: dict[str, list[str]] = {}
            for topic in project["topics"]:
                parent = topic.get("parent_id")
                if parent:
                    children.setdefault(parent, []).append(topic["id"])

            def collect(topic_id: str, visited: set[str]) -> None:
                nonlocal matched
                if topic_id in visited:
                    return
                visited.add(topic_id)
                topic = topics.get(topic_id)
                if topic is None:
                    return
                matched = True
                selected_ids.update(topic.get("chunk_ids", []))
                for child_id in children.get(topic_id, []):
                    collect(child_id, visited)

            for topic_id in topic_ids:
                collect(topic_id, set())

            if matched:
                chunks = [chunk for chunk in chunks if chunk["id"] in selected_ids]

        return chunks if limit == 0 else chunks[:limit]

    def build_context(self, chunks: list[dict], max_chars: int = 8000) -> str:
        """Join chunks into a single context block, capped so small local models
        do not stall processing an oversized prompt (fewer tokens = faster)."""
        parts: list[str] = []
        budget = max_chars

        for chunk in chunks:
            header = f"Source: {chunk['source']} | Chunk: {chunk['id']}\n"
            block = f"{header}{chunk['text']}"

            if len(block) <= budget:
                parts.append(block)
                budget -= len(block)
            else:
                if budget > len(header) + 120:
                    parts.append(f"{header}{chunk['text'][: max(0, budget - len(header))]}")
                break

            if budget <= 0:
                break

        return "\n\n".join(parts)


def _terms(text: str) -> list[str]:
    return [term.lower() for term in re.findall(r"\b[\wáéíóúñü]{4,}\b", text.lower())]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


rag_service = RAGService()
