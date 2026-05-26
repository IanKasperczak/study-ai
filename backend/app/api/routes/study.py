from fastapi import APIRouter, HTTPException

from app.models.schemas import StudyActionRequest, StudyActionResponse, Topic
from app.services.ai_service import ai_service
from app.services.rag_service import rag_service
from app.services.study_store import study_store

router = APIRouter()


@router.get("/{project_id}/topics", response_model=list[Topic])
def get_topics(project_id: str) -> list[Topic]:
    project = study_store.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project["topics"]


@router.post("/summary", response_model=StudyActionResponse)
async def generate_summary(request: StudyActionRequest) -> StudyActionResponse:
    return await _run_study_action(
        request=request,
        action="summary",
        title="Resumen",
        instruction="Genera un resumen claro, ordenado y util para estudiar.",
    )


@router.post("/simple-explanation", response_model=StudyActionResponse)
async def generate_simple_explanation(request: StudyActionRequest) -> StudyActionResponse:
    return await _run_study_action(
        request=request,
        action="simple_explanation",
        title="Explicacion simple",
        instruction=(
            "Explica el contenido con lenguaje simple, ejemplos cotidianos y pasos faciles de seguir."
        ),
    )


async def _run_study_action(
    request: StudyActionRequest,
    action: str,
    title: str,
    instruction: str,
) -> StudyActionResponse:
    project = study_store.get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    selected_chunks = rag_service.get_chunks_for_topics(
        project=project,
        topic_ids=request.topic_ids,
        limit=8,
    )

    if not selected_chunks:
        raise HTTPException(status_code=422, detail="No chunks found for the selected topics.")

    context = rag_service.build_context(selected_chunks)
    content = await ai_service.generate_study_output(
        action=action,
        instruction=instruction,
        context=context,
    )

    return StudyActionResponse(
        title=title,
        content=content,
        source_chunk_ids=[chunk["id"] for chunk in selected_chunks],
    )

