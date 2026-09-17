"""Regression tests for the heading-detection heuristics.

These guard the fixes that stopped a PDF's justified body text from being
misread as section headings by the thousands (see pdf_processor for the
font-size half of the fix).
"""
from app.processors.structure import (
    Heading,
    dedupe_headings,
    detect_text_headings,
    is_valid_title,
    looks_like_title,
    merge_headings,
)


def test_looks_like_title_rejects_lowercase_start():
    # A fragment continuing mid-sentence (e.g. carved out by a PDF extractor
    # around an inline bold word) starts lowercase; a real title doesn't.
    assert not looks_like_title("con dudas cada una de las leyes")
    assert not looks_like_title("magnetico")


def test_looks_like_title_accepts_real_titles():
    assert looks_like_title("Ecuaciones de Maxwell")
    assert looks_like_title("INTRODUCCION")


def test_looks_like_title_rejects_sentence_ending_punctuation():
    assert not looks_like_title("Esto es una oracion completa.")


def test_is_valid_title_rejects_page_markers_and_bare_numbers():
    assert not is_valid_title("Pagina 12")
    assert not is_valid_title("42")
    assert not is_valid_title("ab")  # too short


def test_detect_text_headings_finds_markdown_and_numbered_headings():
    text = "# Titulo Principal\n\nTexto de cuerpo normal.\n\n1. Primera Seccion\n\nMas texto."
    headings = detect_text_headings(text)
    titles = [heading.title for heading in headings]
    assert "Titulo Principal" in titles
    assert "Primera Seccion" in titles


def test_dedupe_headings_caps_repeated_running_headers():
    # A running header/footer repeated across pages, with a real heading in
    # between each occurrence (not literally back-to-back, which collapses
    # to 1 via the separate consecutive-duplicate rule instead).
    headings = []
    for i in range(10):
        headings.append(Heading(level=1, title="Compendio", offset=i * 100))
        headings.append(Heading(level=2, title=f"Seccion {i}", offset=i * 100 + 50))

    result = dedupe_headings(headings, max_repeats=3)
    compendio_count = sum(1 for heading in result if heading.title == "Compendio")
    assert compendio_count == 3


def test_dedupe_headings_collapses_immediate_consecutive_duplicates():
    repeated = [Heading(level=1, title="Compendio", offset=i * 100) for i in range(10)]
    result = dedupe_headings(repeated, max_repeats=3)
    assert len(result) == 1


def test_merge_headings_prefers_format_source_but_fills_gaps():
    primary = [Heading(level=1, title="Del PDF", offset=0, source="pdf")]
    fallback = [
        Heading(level=1, title="Del PDF", offset=0, source="heuristic"),
        Heading(level=2, title="Solo En Texto", offset=50, source="heuristic"),
    ]
    merged = merge_headings(primary, fallback)
    titles = [heading.title for heading in merged]
    assert titles == ["Del PDF", "Solo En Texto"]
