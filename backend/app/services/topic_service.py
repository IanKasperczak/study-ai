import math
import re
from collections import Counter

from app.models.schemas import Topic

STOPWORDS = {
    "para",
    "como",
    "este",
    "esta",
    "estos",
    "estas",
    "desde",
    "sobre",
    "entre",
    "porque",
    "cuando",
    "donde",
    "tambien",
    "puede",
    "pueden",
    "tiene",
    "tienen",
    "with",
    "that",
    "this",
    "from",
    "have",
    "your",
    "about",
    "into",
}


def generate_topics(chunks: list[dict]) -> list[Topic]:
    if not chunks:
        return []

    topic_count = min(8, max(1, math.ceil(len(chunks) / 3)))
    group_size = math.ceil(len(chunks) / topic_count)
    topics: list[Topic] = []

    for index in range(topic_count):
        group = chunks[index * group_size : (index + 1) * group_size]
        if not group:
            continue

        keywords = _top_keywords(" ".join(chunk["text"] for chunk in group), limit=5)
        title = _title_from_chunk(group[0]["text"], keywords, index)
        description = _description_from_keywords(keywords)

        topics.append(
            Topic(
                id=f"topic_{index + 1}",
                title=title,
                description=description,
                keywords=keywords,
                chunk_ids=[chunk["id"] for chunk in group],
            )
        )

    return topics


def _top_keywords(text: str, limit: int) -> list[str]:
    words = [
        word.lower()
        for word in re.findall(r"\b[\wáéíóúñü]{5,}\b", text.lower())
        if word.lower() not in STOPWORDS
    ]
    return [word for word, _ in Counter(words).most_common(limit)]


def _title_from_chunk(text: str, keywords: list[str], index: int) -> str:
    for line in text.splitlines()[:8]:
        clean = line.strip(" -:#\t")
        if 8 <= len(clean) <= 80 and not clean.endswith("."):
            return clean[:70]

    if keywords:
        return " ".join(word.capitalize() for word in keywords[:3])

    return f"Tema {index + 1}"


def _description_from_keywords(keywords: list[str]) -> str:
    if not keywords:
        return "Contenido detectado automaticamente a partir de los documentos."
    return "Conceptos clave: " + ", ".join(keywords) + "."

