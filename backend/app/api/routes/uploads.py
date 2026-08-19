from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import get_settings
from app.models.schemas import DocumentFile, ProjectResponse
from app.processors.chunker import chunk_text_with_offsets
from app.processors.docx_processor import extract_docx
from app.processors.pdf_processor import detect_pdf_headings, extract_pdf_text
from app.processors.structure import detect_text_headings, merge_headings, normalize_text
from app.processors.text_processor import extract_plain_text
from app.services.ai_service import ai_service
from app.services.study_store import study_store
from app.services.topic_service import build_topics_for_document

router = APIRouter()
settings = get_settings()

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


@router.post("", response_model=ProjectResponse)
async def upload_files(
    files: list[UploadFile] = File(...),
    project_id: str | None = None,
) -> ProjectResponse:
    """Upload documents into an existing project (or create a new one when
    project_id is omitted). Existing content is never overwritten."""
    if not files:
        raise HTTPException(status_code=400, detail="No se recibieron archivos.")

    project = study_store.get_project(project_id) if project_id else None
    if project_id and project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    if project is None:
        project = study_store.create_project(uuid4().hex)
        project_id = project["project_id"]

    new_documents: list[dict] = []
    new_topics: list[dict] = []
    new_chunks: list[dict] = []
    processed_any = False

    for file in files:
        original_name = file.filename or "untitled"
        suffix = Path(original_name).suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            new_documents.append(
                _document_failed(
                    original_name,
                    file.content_type or "unknown",
                    f"Formato .{suffix or 'desconocido'} no soportado.",
                )
            )
            continue

        safe_name = Path(original_name.replace("\\", "/")).name
        upload_dir = settings.upload_dir / project_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        saved_path = upload_dir / f"{uuid4().hex}_{safe_name}"
        saved_path.write_bytes(await file.read())

        result = await _process_document(saved_path, suffix, original_name, file.content_type or "unknown")
        if result is not None:
            document, topics, chunks, ok = result
            new_documents.append(document)
            if ok:
                processed_any = True
                new_topics.extend(topics)
                new_chunks.extend(chunks)

    if not new_documents:
        raise HTTPException(status_code=422, detail="No se pudo procesar ningun archivo.")
    if not processed_any:
        details = "; ".join(item["error"] for item in new_documents if item.get("error"))
        raise HTTPException(status_code=422, detail=details or "No se pudo extraer contenido util de los archivos.")

    study_store.add_documents(project_id, new_documents)
    study_store.add_topics(project_id, new_topics)
    study_store.add_chunks(project_id, new_chunks)

    project = study_store.get_project(project_id)
    return _to_response(project)


def _to_response(project: dict) -> ProjectResponse:
    return ProjectResponse(
        project_id=project["project_id"],
        documents=project["documents"],
        topics=project["topics"],
        total_chunks=len(project["chunks"]),
    )


def _document_failed(filename: str, content_type: str, reason: str) -> dict:
    document = DocumentFile(
        id=uuid4().hex,
        filename=filename,
        content_type=content_type,
        character_count=0,
        word_count=0,
        status="error",
        error=reason,
    )
    return document.model_dump()


async def _process_document(
    path: Path,
    suffix: str,
    filename: str,
    content_type: str,
) -> tuple[dict, list[dict], list[dict], bool] | None:
    doc_id = uuid4().hex

    def failed(reason: str) -> tuple[dict, list[dict], list[dict], bool]:
        return (
            DocumentFile(
                id=doc_id,
                filename=filename,
                content_type=content_type,
                character_count=0,
                word_count=0,
                status="error",
                error=reason,
            ).model_dump(),
            [],
            [],
            False,
        )

    try:
        if suffix == ".pdf":
            raw = extract_pdf_text(path)
            format_headings = detect_pdf_headings(path)
        elif suffix == ".docx":
            raw, format_headings = extract_docx(path)
        else:
            raw = extract_plain_text(path)
            format_headings = []
    except Exception as exc:
        return failed(f"No se pudo leer el archivo: {exc}")

    text = normalize_text(raw)
    if not text:
        return failed("No se encontro texto en el archivo.")

    headings = merge_headings(format_headings, detect_text_headings(text))
    chunks_with_offsets = chunk_text_with_offsets(text)
    if not chunks_with_offsets:
        return failed("No se pudo dividir el contenido para estudiar.")

    chunk_ids = [f"chunk_{doc_id}_{index + 1}" for index in range(len(chunks_with_offsets))]
    chunks = [
        {
            "id": chunk_id,
            "source": filename,
            "document_id": doc_id,
            "text": chunk_text,
            "order": index,
            "start": start,
        }
        for index, ((start, chunk_text), chunk_id) in enumerate(zip(chunks_with_offsets, chunk_ids))
    ]

    topics = build_topics_for_document(
        document_id=doc_id,
        filename=filename,
        text=text,
        headings=headings,
        chunks_with_offsets=chunks_with_offsets,
        chunk_ids=chunk_ids,
    )

    refined = await ai_service.refine_topic_titles(
        [topic.title for topic in topics],
        text[:4000],
    )
    if refined:
        for topic, (title, description) in zip(topics, refined):
            topic.title = title
            topic.description = description

    document = DocumentFile(
        id=doc_id,
        filename=filename,
        content_type=content_type,
        character_count=len(text),
        word_count=len(text.split()),
        status="processed",
    )
    return document.model_dump(), [topic.model_dump() for topic in topics], chunks, True