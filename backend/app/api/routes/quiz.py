from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_user_id
from app.models.schemas import (
    GenerateQuizRequest,
    GenerateQuizResponse,
    QuizAttempt,
    QuizQuestion,
    SaveQuizAttemptRequest,
)
from app.services.ai_service import ai_service
from app.services.quiz_store import quiz_store
from app.services.rag_service import rag_service
from app.services.study_store import study_store

router = APIRouter()


@router.post("/generate", response_model=GenerateQuizResponse)
async def generate_quiz(
    request: GenerateQuizRequest,
    user_id: Annotated[str, Depends(get_user_id)],
) -> GenerateQuizResponse:
    project = study_store.get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Same chunk-retrieval building block used for summaries/explanations:
    # every topic already knows exactly which chunks are its own, so no
    # semantic search is needed here, just the existing context assembly
    # across whatever topics are currently selected in the sidebar.
    selected_chunks = rag_service.get_chunks_for_topics(
        project=project,
        topic_ids=request.topic_ids,
        limit=12,
    )
    if not selected_chunks:
        raise HTTPException(status_code=422, detail="No chunks found for the selected topics.")

    context = rag_service.build_context(selected_chunks)
    questions = await ai_service.generate_quiz(context=context, num_questions=request.num_questions)
    if not questions:
        raise HTTPException(
            status_code=503,
            detail="No se pudo generar el quiz. Verifica que haya un proveedor de IA configurado.",
        )

    return GenerateQuizResponse(
        topic_ids=request.topic_ids,
        questions=[QuizQuestion(**question) for question in questions],
    )


@router.post("/attempts", response_model=QuizAttempt)
def save_quiz_attempt(
    request: SaveQuizAttemptRequest,
    user_id: Annotated[str, Depends(get_user_id)],
) -> QuizAttempt:
    attempt = quiz_store.record_attempt(
        user_id=user_id,
        subtema_id=",".join(request.topic_ids),
        score=request.score,
        total_questions=request.total_questions,
    )
    return QuizAttempt(**attempt)


@router.get("/attempts", response_model=list[QuizAttempt])
def list_quiz_attempts(user_id: Annotated[str, Depends(get_user_id)]) -> list[QuizAttempt]:
    return [QuizAttempt(**attempt) for attempt in quiz_store.list_attempts(user_id)]
