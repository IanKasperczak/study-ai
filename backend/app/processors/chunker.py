"""Text chunking that tracks character offsets.

Offsets are computed against the SAME normalized text used by the structure
detector, so each RAG chunk can be mapped back to the topic/section it belongs
to. This is what keeps topics semantic while chunks stay an internal detail.
"""
import re

_PARAGRAPH_SPLIT = re.compile(r"\n{2,}")


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 160) -> list[str]:
    return [chunk for _, chunk in chunk_text_with_offsets(text, max_chars, overlap)]


def chunk_text_with_offsets(
    text: str,
    max_chars: int = 1200,
    overlap: int = 160,
) -> list[tuple[int, str]]:
    """Return (start_offset, chunk_text) pairs over the given normalized text."""
    if not text or not text.strip():
        return []

    chunks: list[tuple[int, str]] = []
    current = ""
    current_start = 0

    for start, paragraph in _paragraphs_with_offsets(text):
        if not current:
            current_start = start

        if len(paragraph) > max_chars:
            if current:
                chunks.append((current_start, current.strip()))
                current = ""
            for index, piece in enumerate(
                _split_long_paragraph(paragraph, max_chars=max_chars, overlap=overlap)
            ):
                chunks.append((start + index * max_chars, piece))
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append((current_start, current.strip()))
            current = paragraph
            current_start = start

    if current:
        chunks.append((current_start, current.strip()))

    return chunks


def _paragraphs_with_offsets(text: str) -> list[tuple[int, str]]:
    paragraphs: list[tuple[int, str]] = []
    start = 0
    for match in _PARAGRAPH_SPLIT.finditer(text):
        content = text[start : match.start()]
        if content.strip():
            paragraphs.append((start, content.strip()))
        start = match.end()
    tail = text[start:]
    if tail.strip():
        paragraphs.append((start, tail.strip()))
    return paragraphs


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