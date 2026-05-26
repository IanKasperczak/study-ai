from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.models.schemas import FileSummary, ProjectResponse
from app.processors.chunker import chunk_text
from app.processors.docx_processor import extract_docx_text
from app.processors.pdf_processor import extract_pdf_text
from app.processors.text_processor import extract_plain_text
from app.services.study_store import study_store
from app.services.topic_service import generate_topics

router = APIRouter()
settings = get_settings()

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@router.post("", response_model=ProjectResponse)
async def upload_files(files: list[UploadFile] = File(...)) -> ProjectResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    project_id = uuid4().hex
    upload_dir = settings.upload_dir / project_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_summaries: list[FileSummary] = []
    all_chunks: list[dict] = []

    for file in files:
        original_name = file.filename or "untitled"
        suffix = Path(original_name).suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            file_summaries.append(
                FileSummary(
                    filename=original_name,
                    content_type=file.content_type or "unknown",
                    character_count=0,
                    status=f"skipped: unsupported extension {suffix or 'none'}",
                )
            )
            continue

        safe_name = Path(original_name.replace("\\", "/")).name
        saved_path = upload_dir / f"{uuid4().hex}_{safe_name}"
        content = await file.read()
        saved_path.write_bytes(content)

        try:
            extracted_text = _extract_text(saved_path, suffix)
        except Exception as exc:
            file_summaries.append(
                FileSummary(
                    filename=original_name,
                    content_type=file.content_type or "unknown",
                    character_count=0,
                    status=f"error: {exc}",
                )
            )
            continue

        chunks = chunk_text(extracted_text)
        for index, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "id": f"chunk_{len(all_chunks) + 1}",
                    "source": original_name,
                    "text": chunk,
                    "order": index,
                }
            )

        file_summaries.append(
            FileSummary(
                filename=original_name,
                content_type=file.content_type or "unknown",
                character_count=len(extracted_text),
                status="processed",
            )
        )

    if not all_chunks:
        raise HTTPException(
            status_code=422,
            detail="No readable content was extracted from the uploaded files.",
        )

    topics = generate_topics(all_chunks)
    project = study_store.create_project(
        project_id=project_id,
        files=file_summaries,
        chunks=all_chunks,
        topics=topics,
    )

    return ProjectResponse(
        project_id=project["project_id"],
        files=project["files"],
        topics=project["topics"],
        total_chunks=len(project["chunks"]),
    )


def _extract_text(path: Path, suffix: str) -> str:
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix == ".docx":
        return extract_docx_text(path)
    return extract_plain_text(path)
