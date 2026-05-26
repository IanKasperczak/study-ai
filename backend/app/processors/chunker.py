import re


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 160) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []

    paragraphs = [item.strip() for item in normalized.split("\n\n") if item.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_paragraph(paragraph, max_chars=max_chars, overlap=overlap))
            continue

        next_value = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(next_value) <= max_chars:
            current = next_value
        else:
            chunks.append(current.strip())
            current = paragraph

    if current:
        chunks.append(current.strip())

    return chunks


def _split_long_paragraph(paragraph: str, max_chars: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0

    while start < len(paragraph):
        end = min(start + max_chars, len(paragraph))
        chunks.append(paragraph[start:end].strip())
        if end == len(paragraph):
            break
        start = max(0, end - overlap)

    return [chunk for chunk in chunks if chunk]


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

