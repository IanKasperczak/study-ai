"""Regression tests for PDF heading detection.

Reproduces the two real bugs found while building this: a body line with
one inline bold/larger word getting mistaken for a heading (fixed by using
the MIN span size per line, not the max), and a heading candidate that
starts lowercase because it's really a fragment cut out of running text.
"""
import fitz
import pytest

from app.processors.pdf_processor import detect_pdf_headings


@pytest.fixture
def pdf_with_mixed_formatting(tmp_path):
    """One genuine, uniformly-large heading plus a body paragraph that has
    a single inline word rendered at a different size (the pattern that
    used to produce a bogus heading)."""
    doc = fitz.open()
    page = doc.new_page()

    page.insert_text((50, 60), "Ecuaciones de Maxwell", fontsize=16)

    y = 100
    page.insert_text((50, y), "El campo electrico y el ", fontsize=11)
    page.insert_text((50 + 130, y), "magnetico", fontsize=13)
    page.insert_text((50 + 200, y), " se relacionan de forma directa", fontsize=11)

    # Bulk body text at the base size so the font-size heuristic has a
    # meaningful median to compare against.
    y2 = 130
    for _ in range(20):
        page.insert_text(
            (50, y2), "Texto de cuerpo normal para establecer el tamano base.", fontsize=11
        )
        y2 += 14

    path = tmp_path / "test.pdf"
    doc.save(str(path))
    doc.close()
    return path


def test_inline_emphasis_does_not_create_a_bogus_heading(pdf_with_mixed_formatting):
    headings = detect_pdf_headings(pdf_with_mixed_formatting)
    titles = [heading.title for heading in headings]

    assert "Ecuaciones de Maxwell" in titles
    assert "magnetico" not in titles
    assert not any(title.islower() for title in titles)
