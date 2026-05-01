from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    article_number: str = Field(..., description="Numéro d'article (ex: '12', 'premier', '7-1')")
    article_title: str | None = None
    document: str
    volume: str | None = None
    section: str | None = None
    page: int
    snippet: str
    score: float | None = None


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int | None = None
    history: list[Message] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    used_context: bool
    rewritten_question: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = 5


class SearchResponse(BaseModel):
    results: list[Citation]


class HealthResponse(BaseModel):
    status: str
    llm_loaded: bool
    embedder_loaded: bool
    chunks_indexed: int
    collection: str
    chroma_ok: bool = True
    chroma_mode: Literal["http", "persistent"] = "persistent"


class IngestResponse(BaseModel):
    status: str
    detail: str
