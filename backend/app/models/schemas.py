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
    embedding: list[float] | None = None


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


# Structured output expected from the AI when filtering out noise
# (author names, cover titles, repeated headers, cut fragments) among the
# heuristically-detected topics of a document. Asking for just the noisy
# indices (instead of a true/false per topic) keeps the reply short even for
# hundreds of topics -- a long run of repeated true/false values is exactly
# the kind of degenerate pattern that can make some models loop instead of
# terminating.
class AiInvalidTopicIndices(BaseModel):
    invalid_indices: list[int] = Field(default_factory=list)


# Structured output expected from the AI when generating a multiple-choice
# quiz from a Subtema's chunks.
class AiQuizQuestion(BaseModel):
    question: str
    options: list[str] = Field(default_factory=list)
    correct_index: int = 0
    explanation: str = ""


class AiQuiz(BaseModel):
    questions: list[AiQuizQuestion] = Field(default_factory=list)


class QuizQuestion(BaseModel):
    """A quiz question as served to the client."""

    question: str
    options: list[str]
    correct_index: int
    explanation: str = ""


class GenerateQuizRequest(BaseModel):
    project_id: str
    topic_ids: list[str]
    num_questions: int = 10


class GenerateQuizResponse(BaseModel):
    topic_ids: list[str]
    questions: list[QuizQuestion] = Field(default_factory=list)


class SaveQuizAttemptRequest(BaseModel):
    # Stored joined by commas into quiz_attempts.subtema_id (see quiz_store.py)
    # -- the column keeps its original single-id name/shape, but a quiz can
    # now span every topic selected in the sidebar, not just one Subtema.
    topic_ids: list[str]
    score: int
    total_questions: int


class QuizAttempt(BaseModel):
    id: int
    user_id: str
    subtema_id: str
    score: int
    total_questions: int
    created_at: str