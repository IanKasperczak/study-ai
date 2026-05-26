from fastapi import APIRouter

from app.api.routes import chat, study, uploads

api_router = APIRouter()
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
api_router.include_router(study.router, prefix="/study", tags=["study"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

