from typing import Literal

from pydantic import BaseModel, Field


class FileSummary(BaseModel):
    filename: str
    content_type: str
    character_count: int
    status: str


class Topic(BaseModel):
    id: str
    title: str
    description: str
    keywords: list[str] = Field(default_factory=list)
    chunk_ids: list[str] = Field(default_factory=list)


class ProjectResponse(BaseModel):
    project_id: str
    files: list[FileSummary]
    topics: list[Topic]
    total_chunks: int


class StudyActionRequest(BaseModel):
    project_id: str
    topic_ids: list[str] = Field(default_factory=list)


class StudyActionResponse(BaseModel):
    title: str
    content: str
    source_chunk_ids: list[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    project_id: str
    message: str
    topic_ids: list[str] = Field(default_factory=list)


class SourceChunk(BaseModel):
    id: str
    source: str
    preview: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceChunk] = Field(default_factory=list)

