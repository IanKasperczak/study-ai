"""Regression tests for topic-tree building and the AI noise filter.

apply_ai_topic_filter has to drop topics the AI flags as noise (author
names, cover titles, cut fragments) without losing the chunks that were
assigned to them -- chunks are the only thing that actually feeds the RAG
chat, so silently dropping one would make cited content disappear.
"""
from app.models.schemas import Topic
from app.services.topic_service import apply_ai_topic_filter, build_topics_for_document
from app.processors.structure import Heading


def _topic(id_, title, parent_id=None, order=0, chunk_ids=None):
    return Topic(
        id=id_,
        title=title,
        parent_id=parent_id,
        order=order,
        document_id="d1",
        chunk_ids=chunk_ids or [],
    )


def test_apply_ai_topic_filter_keeps_all_chunks():
    topics = [
        _topic("t1", "Introduccion", chunk_ids=["c1"]),
        _topic("t2", "Prof. Fulana de Tal", chunk_ids=["c2"]),  # noise, root-level
        _topic("t3", "Subtema de Prof", parent_id="t2", chunk_ids=["c3"]),  # valid child of noise
        _topic("t4", "con dud", chunk_ids=["c4"]),  # noise, no children
        _topic("t5", "Campos Electricos", chunk_ids=["c5"]),
    ]
    valid_flags = [True, False, True, False, True]

    result = apply_ai_topic_filter(topics, valid_flags)

    kept_ids = {topic.id for topic in result}
    assert kept_ids == {"t1", "t3", "t5"}

    all_chunks = sorted(chunk for topic in result for chunk in topic.chunk_ids)
    assert all_chunks == ["c1", "c2", "c3", "c4", "c5"]


def test_apply_ai_topic_filter_reparents_children_of_removed_topic():
    topics = [
        _topic("t1", "Prof. Fulana de Tal"),  # noise, root-level
        _topic("t2", "Subtema valido", parent_id="t1"),
    ]
    result = apply_ai_topic_filter(topics, [False, True])

    assert len(result) == 1
    assert result[0].id == "t2"
    assert result[0].parent_id is None  # reparented to root, not left dangling


def test_apply_ai_topic_filter_ignores_mismatched_flag_count():
    topics = [_topic("t1", "Tema")]
    result = apply_ai_topic_filter(topics, [True, False])  # wrong length
    assert result == topics


def test_apply_ai_topic_filter_never_drops_everything():
    topics = [_topic("t1", "Ruido 1"), _topic("t2", "Ruido 2")]
    result = apply_ai_topic_filter(topics, [False, False])
    assert result == topics  # nothing would survive -> filter is a no-op


def test_build_topics_for_document_without_headings_returns_single_fallback_topic():
    text = "Documento sin estructura reconocible, solo texto plano."
    topics = build_topics_for_document(
        document_id="d1",
        filename="apunte.txt",
        text=text,
        headings=[],
        chunks_with_offsets=[(0, text)],
        chunk_ids=["c1"],
    )
    assert len(topics) == 1
    assert topics[0].chunk_ids == ["c1"]


def test_build_topics_for_document_builds_hierarchy_from_headings():
    text = "Tema 1\n\ncontenido uno\n\nSubtema 1.1\n\ncontenido dos\n\nTema 2\n\ncontenido tres"
    headings = [
        Heading(level=1, title="Tema 1", offset=0),
        Heading(level=2, title="Subtema 1.1", offset=text.index("Subtema 1.1")),
        Heading(level=1, title="Tema 2", offset=text.index("Tema 2")),
    ]
    chunks_with_offsets = [(0, "contenido uno"), (text.index("contenido dos"), "contenido dos")]
    topics = build_topics_for_document(
        document_id="d1",
        filename="apunte.txt",
        text=text,
        headings=headings,
        chunks_with_offsets=chunks_with_offsets,
        chunk_ids=["c1", "c2"],
    )

    by_title = {topic.title: topic for topic in topics}
    assert by_title["Subtema 1.1"].parent_id == by_title["Tema 1"].id
    assert by_title["Tema 2"].parent_id is None
