from pathlib import Path


def extract_plain_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise RuntimeError("Could not decode text file.")

