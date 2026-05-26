from pathlib import Path


def extract_pdf_text(path: Path) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is not installed.") from exc

    parts: list[str] = []
    with fitz.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if text:
                parts.append(f"[Page {page_number}]\n{text}")

    return "\n\n".join(parts)

