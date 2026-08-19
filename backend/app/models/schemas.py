from typing import Literal

from pydantic import BaseModel, Field


class DocumentFile(BaseModel):
    """Metadata of a single uploaded document. File-level state lives here."""

    id: str
    filename: str
    content_type: str
    character_count: int
    word_count: int = 0
    status: str = "processed"
    error: str | None = None


class Topic(BaseModel):
    """A semantic, user-facing topic. Independent from the RAG chunks."""

    id: str
    title: str
    description: str = ""
    parent_id: str | None = None
    order: int = 0
    document_id: str
    chunk_ids: list[str] = Field(default_factory=list)


class Chunk(BaseModel):
    """Internal unit used only for RAG/context retrieval."""

    id: str
    source: str
    document_id: str
    text: str
    order: int = 0
    start: int = 0


class ProjectResponse(BaseModel):
    project_id: str
    documents: list[DocumentFile]
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


class DeleteResponse(BaseModel):
    project: ProjectResponse


# Structured output expected from the AI when inferring document topics.
class AiTopicSection(BaseModel):
    title: str
    description: str = ""


class AiTopic(BaseModel):
    title: str
    description: str = ""
    sections: list[AiTopicSection] = Field(default_factory=list)


class AiTopicTree(BaseModel):
    topics: list[AiTopic] = Field(default_factory=list)