"""Document structure detection shared by every format.

Produces a flat, ordered list of Heading items (level + title + offset in the
normalized text). Format-specific processors (PDF font sizes, DOCX styles) can
supply their own heading lists; text-only formats rely on the heuristics here.
The offset is what links sections to RAG chunks later.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Heading:
    level: int
    title: str
    offset: int
    source: str = "heuristic"


_MARKDOWN_HEADING = re.compile(r"^\s{0,3}(#{1,6})[ \t]+(.+)$")
_SIMPLE_NUMBERED = re.compile(r"^\s*(\d{1,3})[.)][ \t]+(.+)$")
_GROUPED_NUMBERED = re.compile(r"^\s*(\d{1,3}(?:[.)][ \t]*\d{1,3})+)[.)][ \t]+(.+)$")
_WORD_NUMBERED = re.compile(
    r"^\s*(cap[ií]tulo|chapter|unidad|lecci[oó]n|secci[oó]n|parte|tema|t[oó]pico|m[oó]dulo)"
    r"[ \t]+(\d+|[ivxlcdmIVXLCDM]+)\b"
)
_CAPS_CANDIDATE = re.compile(r"^[\dA-ZÁÉÍÓÚÑÜÀÈÌÒÙ][\dA-ZÁÉÍÓÚÑÜÀÈÌÒÙ \-–—:·'’”]{2,63}$")
_SENTENCE_END = re.compile(r"[.!?]([\s\u2026\"'»)\]]*)$")
_PAGE_MARKER = re.compile(
    r"^\s*(?:page|p[aá]g\.?|pag[- ]?[aá]gina|fol\.?)?[ \t]*\d{1,4}[ \t]*\d*$",
    re.IGNORECASE,
)
_URL_PATTERN = re.compile(r"https?://|www\.")
_DOUBLE_SPACE = re.compile(r"\s{2,}")
_DIGIT_GROUP = re.compile(r"\d{1,3}")

HEADER_LIKE_KEYWORDS = re.compile(
    r"\b(?:index|contents|indice|glosario|bibliograf[íi]a|referencias|ap[ée]ndice|"
    r"introducci[óo]n|abstract|resumen)\b",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    """Clean whitespace while keeping paragraphs and line structure."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def detect_text_headings(text: str) -> list[Heading]:
    """Heuristic heading detection for text/markdown-style content."""
    headings: list[Heading] = []
    offset = 0
    for raw_line in text.split("\n"):
        stripped = raw_line.strip()
        if stripped:
            level: int | None = None
            title: str | None = None

            match = _MARKDOWN_HEADING.match(raw_line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
            else:
                match = _GROUPED_NUMBERED.match(raw_line)
                if match:
                    level = min(6, len(_DIGIT_GROUP.findall(match.group(1))))
                    title = match.group(2).strip()
                else:
                    match = _SIMPLE_NUMBERED.match(raw_line)
                    if match:
                        level = 1
                        title = match.group(2).strip()
                    else:
                        match = _WORD_NUMBERED.match(stripped.lower())
                        if match:
                            level = 2 if "seccion" in match.group(1) or "leccion" in match.group(1) else 1
                            title = stripped
                        elif _is_heading_like(stripped) and is_valid_title(stripped):
                            level = 1
                            title = stripped

            if level and title and is_valid_title(title):
                clean = clean_title(title)
                if clean:
                    indent = len(raw_line) - len(raw_line.lstrip())
                    headings.append(Heading(level=level, title=clean, offset=offset + indent))

        offset += len(raw_line) + 1

    return dedupe_headings(headings)


def looks_like_title(line: str) -> bool:
    """Public helper: is this single line a plausible section heading?

    Used by format-specific detectors (PDF font size, DOCX styles) to validate
    their candidates before they become topics.
    """
    if _looks_like_header(line):
        return False
    if not is_valid_title(line):
        return False
    if _SENTENCE_END.search(line):
        return False
    return True


def _is_heading_like(line: str) -> bool:
    if _looks_like_header(line):
        return False
    lower = line.lower()
    if _WORD_NUMBERED.search(" " + lower + " "):
        return False
    # Uppercase captions (conference titles, section banners) are strong signals.
    if line.isupper():
        words = line.split()
        return 2 <= len(words) <= 18
    # Title-case short lines: accept only if short and clearly not a sentence.
    if not line[0].isupper():
        return False
    if _SENTENCE_END.search(line):
        return False
    words = line.split()
    if not (2 <= len(words) <= 12):
        return False
    if sum(1 for w in words if w and w[0].isupper()) < 1:
        return False
    return True


def _looks_like_header(line: str) -> bool:
    if _URL_PATTERN.search(line):
        return True
    if _PAGE_MARKER.match(line):
        return True
    digits = sum(ch.isdigit() for ch in line)
    if line and digits / len(line) > 0.5 and len(line) < 12:
        return True
    return False


def clean_title(title: str) -> str:
    title = title.strip().strip("*_`#").strip()
    title = title.strip(":·-–— ")
    title = _DOUBLE_SPACE.sub(" ", title)
    return title.strip()


def is_valid_title(title: str) -> bool:
    title = title.strip()
    if not (3 <= len(title) <= 90):
        return False
    if "[" in title or "]" in title:
        return False
    if _SENTENCE_END.search(title):
        return False
    if re.fullmatch(r"[\d\s.,()\-–—]+", title):
        return False
    if _PAGE_MARKER.match(title):
        return False
    if title.isdigit():
        return False
    words = title.split()
    if any(w.isupper() and len(w) <= 2 for w in words):
        pass  # single-letter acronyms inside a title are fine
    return True


def dedupe_headings(headings: list[Heading], max_repeats: int = 3) -> list[Heading]:
    """Drop consecutive duplicates and titles repeated too often (running headers,
    table-of-contents echoes)."""
    seen: dict[str, int] = {}
    result: list[Heading] = []
    previous: str | None = None
    for heading in headings:
        key = heading.title.casefold()
        if key == previous:
            continue
        count = seen.get(key, 0)
        if count >= max_repeats:
            continue
        seen[key] = count + 1
        result.append(heading)
        previous = key
    return result


def merge_headings(primary: list[Heading], fallback: list[Heading]) -> list[Heading]:
    """Combine format-level headings (PDF font size, DOCX styles) with text ones,
    preferring the explicit structure when available and removing overlaps."""
    if not primary:
        return fallback
    seen_offsets: set[int] = set()
    merged: list[Heading] = []
    fallback_by_offset = {item.offset: item for item in fallback}
    for heading in primary:
        if heading.offset in fallback_by_offset:
            # Prefer the format-derived level, keep a fallback title if better.
            fallback_item = fallback_by_offset[heading.offset]
            if not is_valid_title(heading.title) and is_valid_title(fallback_item.title):
                heading = Heading(heading.level, fallback_item.title, heading.offset, "merged")
        seen_offsets.add(heading.offset)
        merged.append(heading)
    for item in fallback:
        if item.offset not in seen_offsets and is_valid_title(item.title):
            merged.append(item)
    merged.sort(key=lambda item: item.offset)
    return dedupe_headings(merged)