"""Semantic topic generation.

Topics come from the document's own structure (headings detected by the format
processors), NOT from chunk boundaries. Each topic carries the character offsets
of its section so we can map RAG chunks back to the topic that contains them.
"""
from __future__ import annotations

import bisect
import re
from dataclasses import dataclass

from app.models.schemas import Topic
from app.processors.structure import Heading

# A preamble (text before the first heading) becomes its own topic above this size.
_MIN_PREAMBLE_CHARS = 200


@dataclass
class _Section:
    title: str
    level: int
    start: int
    end: int


def build_topics_for_document(
    document_id: str,
    filename: str,
    text: str,
    headings: list[Heading],
    chunks_with_offsets: list[tuple[int, str]],
    chunk_ids: list[str],
) -> list[Topic]:
    """Build the hierarchical topic list for one document and assign chunk ids.

    chunk_ids keeps the same order as chunks_with_offsets so the offsets align.
    """
    if not headings:
        topic = build_fallback_topic(document_id, filename, chunk_ids)
        topic.description = _section_description(text, 0, len(text)) or topic.description
        return [topic]

    sections = _segment_sections(text, headings)
    topics = _sections_to_topics(document_id, sections)
    for topic, section in zip(topics, sections):
        topic.description = _section_description(text, section.start, section.end)
    _assign_chunks_to_topics(topics, sections, chunks_with_offsets, chunk_ids)
    return topics


def build_fallback_topic(document_id: str, filename: str, chunk_ids: list[str]) -> Topic:
    return Topic(
        id=_topic_id(document_id, 0),
        title=_title_from_filename(filename),
        description="Documento completo sin secciones reconocibles.",
        document_id=document_id,
        order=0,
        chunk_ids=chunk_ids,
    )


def _segment_sections(text: str, headings: list[Heading]) -> list[_Section]:
    sections: list[_Section] = []
    first_offset = headings[0].offset

    preamble = text[:first_offset].strip()
    if len(preamble) >= _MIN_PREAMBLE_CHARS:
        sections.append(_Section(title="Introducción", level=1, start=0, end=first_offset))

    total = len(text)
    for index, heading in enumerate(headings):
        start = heading.offset
        end = headings[index + 1].offset if index + 1 < len(headings) else total
        sections.append(_Section(title=heading.title, level=heading.level, start=start, end=end))

    return sections


def _sections_to_topics(document_id: str, sections: list[_Section]) -> list[Topic]:
    topics: list[Topic] = []
    stack: list[tuple[int, str]] = []  # (level, topic_id)

    for index, section in enumerate(sections):
        while stack and stack[-1][0] >= section.level:
            stack.pop()

        parent_id = stack[-1][1] if stack else None
        topics.append(
            Topic(
                id=_topic_id(document_id, index + 1),
                title=section.title,
                description="",
                parent_id=parent_id,
                order=index,
                document_id=document_id,
            )
        )
        stack.append((section.level, topics[-1].id))

    return topics


def _assign_chunks_to_topics(
    topics: list[Topic],
    sections: list[_Section],
    chunks_with_offsets: list[tuple[int, str]],
    chunk_ids: list[str],
) -> None:
    ends = [section.start for section in sections]
    topic_by_start = {section.start: topic for section, topic in zip(sections, topics)}

    for (start, _), chunk_id in zip(chunks_with_offsets, chunk_ids):
        position = bisect.bisect_right(ends, start) - 1
        if position < 0:
            position = 0
        topic_by_start[sections[position].start].chunk_ids.append(chunk_id)


def _section_description(text: str, start: int, end: int) -> str:
    window = re.sub(r"\s+", " ", text[start:end]).strip()
    raw_sentences = [item.strip() for item in window.replace("?", ".").replace("!", ".").split(".")]
    sentences = [item for item in raw_sentences if len(item) > 40]
    return " ".join(sentences[:2])[:220] + ("." if sentences else "")


def _topic_id(document_id: str, index: int) -> str:
    return f"topic_{document_id}_{index}"


def _title_from_filename(filename: str) -> str:
    name = filename.rsplit(".", 1)[0].strip() or "Documento"
    words = re.sub(r"[_-]+", " ", name).split()
    return " ".join(word[:1].upper() + word[1:] for word in words)[:60] or "Documento"