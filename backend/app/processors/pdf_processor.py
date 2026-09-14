"""PDF extraction without page markers, plus font-size based heading detection."""
import re
from pathlib import Path

from app.processors.structure import Heading, clean_title, looks_like_title, normalize_text

_BODY_RATIO_LEVEL_1 = 1.4


def extract_pdf_text(path: Path) -> str:
    """Plain text, pages joined with blank lines. No '[Page N]' markers so the
    raw text never leaks machine labels into titles, previews or answers."""
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is not installed.") from exc

    parts: list[str] = []
    with fitz.open(path) as document:
        for page in document:
            text = page.get_text("text").strip()
            if text:
                parts.append(text)
    return "\n\n".join(parts)


def detect_pdf_headings(path: Path) -> list[Heading]:
    """Detect section headings by comparing span font sizes against the body.

    Returns Heading items whose offsets point into the SAME text produced by
    extract_pdf_text() normalized with structure.normalize_text()."""
    try:
        import fitz
    except ImportError:
        return []

    with fitz.open(path) as document:
        pages = [page.get_text("text").strip() for page in document]
        normalized_pages = [normalize_text(page) for page in pages if page]

        sizes: list[tuple[float, int]] = []
        spans_by_page: list[list[tuple[float, str]]] = []
        for page in document:
            page_spans: list[tuple[float, str]] = []
            raw = page.get_text("dict")
            for block in raw.get("blocks", []):
                for line in block.get("lines", []):
                    line_spans = [
                        span for span in line.get("spans", []) if span.get("text", "").strip()
                    ]
                    if not line_spans:
                        continue
                    # Use the SMALLEST span size in the line, not the largest: a real
                    # heading is styled uniformly large, while a body line with just
                    # one inline bold/emphasized word would otherwise pass the size
                    # threshold via that single word and drag in the whole line as a
                    # bogus, mid-sentence "heading".
                    size = min(span.get("size", 0.0) for span in line_spans)
                    text = "".join(span.get("text", "") for span in line_spans).strip()
                    if size > 0 and text:
                        sizes.append((size, len(text) * max(1, int(size / 10))))
                        page_spans.append((size, text))
            spans_by_page.append(page_spans)

    body_size = _weighted_median_size(sizes)
    if body_size <= 0:
        return []

    headings: list[Heading] = []
    running_offset = 0
    for page_index, page_text in enumerate(normalized_pages):
        page_start = running_offset
        for size, text in spans_by_page[page_index]:
            if size < body_size * 1.18 or not looks_like_title(text):
                continue
            clean = clean_title(text)
            if not clean:
                continue
            local = _locate(page_text, text)
            if local < 0:
                continue
            level = 1 if size >= body_size * _BODY_RATIO_LEVEL_1 else 2
            headings.append(Heading(level=level, title=clean, offset=page_start + local, source="pdf"))
        running_offset = page_start + len(page_text) + 2

    return headings


def _locate(window: str, line: str) -> int:
    index = window.find(line)
    if index != -1:
        return index
    pattern = r"\s+".join(re.escape(token) for token in line.split())
    match = re.search(pattern, window)
    return match.start() if match else -1


def _weighted_median_size(sizes: list[tuple[float, int]]) -> float:
    ordered = sorted(sizes, key=lambda item: item[0])
    total = sum(weight for _, weight in ordered)
    half = total / 2
    acc = 0
    for size, weight in ordered:
        acc += weight
        if acc >= half:
            return size
    return ordered[-1][0] if ordered else 0.0