"""Regression tests for chunk offset correctness.

The offsets returned here are what maps a RAG chunk back to the topic that
contains it (see topic_service._assign_chunks_to_topics). A previous bug
advanced the offset by max_chars per piece instead of (max_chars - overlap),
which silently misaligned every chunk after the first one in any paragraph
longer than max_chars.
"""
from app.processors.chunker import chunk_text_with_offsets, _split_long_paragraph


def test_split_long_paragraph_offsets_account_for_overlap():
    # Pure digits: no whitespace means .strip() never changes a slice, so we
    # can compare pieces against the source text directly.
    paragraph = "0123456789" * 200  # 2000 chars
    pieces = _split_long_paragraph(paragraph, max_chars=500, overlap=60)

    assert len(pieces) > 1
    for local_start, piece in pieces:
        assert paragraph[local_start : local_start + len(piece)] == piece

    # Consecutive offsets must advance by (max_chars - overlap), not max_chars.
    starts = [start for start, _ in pieces]
    for previous, current in zip(starts, starts[1:]):
        assert current - previous == 500 - 60


def test_chunk_text_with_offsets_maps_back_to_source_text():
    text = "Intro parrafo corto.\n\n" + ("abcdefghij" * 150)  # second paragraph is long
    chunks = chunk_text_with_offsets(text, max_chars=400, overlap=50)

    assert len(chunks) > 1
    for start, chunk in chunks:
        # The stripped chunk must be found starting exactly at its reported
        # offset in the original text (allowing for the leading/trailing
        # whitespace .strip() removes at paragraph boundaries).
        found_at = text.find(chunk.strip(), max(0, start - 5))
        assert found_at != -1
        assert abs(found_at - start) <= 5


def test_empty_text_returns_no_chunks():
    assert chunk_text_with_offsets("") == []
    assert chunk_text_with_offsets("   \n\n  ") == []
