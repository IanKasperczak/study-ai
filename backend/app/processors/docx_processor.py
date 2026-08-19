"""DOCX extraction with real heading detection from paragraph styles."""
import re
from pathlib import Path

from app.processors.structure import Heading, clean_title


def extract_docx(path: Path) -> tuple[str, list[Heading]]:
    """Return (joined_text, detected_headings)."""
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("python-docx is not installed.") from exc

    document = Document(path)
    parts: list[str] = []
    headings: list[Heading] = []
    offset = 0

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue

        level = _heading_level(paragraph)
        if level:
            headings.append(
                Heading(level=level, title=clean_title(text), offset=offset, source="docx")
            )

        parts.append(text)
        offset += len(text) + 2

    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                line = " | ".join(cells)
                parts.append(line)
                offset += len(line) + 2

    return "\n\n".join(parts), headings


def _heading_level(paragraph) -> int | None:
    style = (paragraph.style.name or "").lower()
    if "heading" in style:
        for token in re.findall(r"\d+", style):
            return min(6, max(1, int(token)))
        return 1
    return None