from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse, SourceChunk
from app.services.ai_service import ai_service
from app.services.rag_service import rag_service
from app.services.study_store import study_store

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat_with_project(request: ChatRequest) -> ChatResponse:
    project = study_store.get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    matches = rag_service.search(
        project=project,
        query=request.message,
        topic_ids=request.topic_ids,
        limit=5,
    )

    if not matches:
        return ChatResponse(
            answer="No encontre informacion suficiente en los documentos cargados para responder eso.",
            sources=[],
        )

    context = rag_service.build_context(matches)
    answer = await ai_service.answer_question(
        question=request.message,
        context=context,
    )

    return ChatResponse(
        answer=answer,
        sources=[
            SourceChunk(id=chunk["id"], source=chunk["source"], preview=chunk["text"][:260])
            for chunk in matches
        ],
    )

