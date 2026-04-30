import json
import logging

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from ..config import get_settings
from ..llm.generator import generate, stream_generate
from ..llm.keyword_extractor import build_enriched_query, extract_keywords
from ..llm.prompts import REFUSAL_TEXT
from ..llm.query_rewriter import rewrite_query
from ..rag.retriever import RetrievedChunk, retrieve_multi
from ..schemas import ChatRequest, ChatResponse, Citation

router = APIRouter()
logger = logging.getLogger(__name__)


def _to_citations(chunks: list[RetrievedChunk]) -> list[Citation]:
    return [
        Citation(
            article_number=c.article_number,
            article_title=c.article_title or None,
            document=c.document,
            volume=c.volume,
            section=c.section,
            page=c.page,
            snippet=c.text[:400],
            score=c.score,
        )
        for c in chunks
    ]


def _retrieve(question: str, top_k: int | None) -> tuple[list[RetrievedChunk], list[str]]:
    """Pipeline RAG enrichi.

    1. La question (déjà nettoyée) est envoyée au LLM pour extraire des
       mots-clés et synonymes du vocabulaire juridique sénégalais.
    2. Le retriever est interrogé deux fois : avec la question seule et avec
       la question enrichie des mots-clés. Les chunks sont fusionnés par id en
       gardant le meilleur score.
    """
    settings = get_settings()
    keywords = extract_keywords(question)
    enriched = build_enriched_query(question, keywords)
    queries = [question, enriched] if enriched != question else [question]

    chunks = retrieve_multi(
        queries=queries,
        chroma_dir=settings.chroma_path,
        collection_name=settings.collection_name,
        embed_model=settings.embed_model,
        top_k=top_k or settings.top_k,
        min_score=settings.min_score,
    )
    return chunks, keywords


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    normalized_question = rewrite_query(req.question)
    chunks, keywords = _retrieve(normalized_question, req.top_k)
    if not chunks:
        logger.info(
            "Aucun chunk pour question=%r (mots-clés=%s)", normalized_question, keywords
        )
        return ChatResponse(
            answer=REFUSAL_TEXT,
            citations=[],
            used_context=False,
            rewritten_question=normalized_question,
        )

    answer, used = generate(normalized_question, chunks)
    citations = _to_citations(chunks) if used and answer != REFUSAL_TEXT else []
    return ChatResponse(
        answer=answer,
        citations=citations,
        used_context=used,
        rewritten_question=normalized_question,
    )


@router.post("/chat/stream")
def chat_stream(req: ChatRequest):
    normalized_question = rewrite_query(req.question)
    chunks, _keywords = _retrieve(normalized_question, req.top_k)

    def event_gen():
        # Toujours envoyer la question reformulée en premier afin que le
        # backend puisse l'utiliser comme titre auto de la conversation.
        yield {
            "event": "rewritten",
            "data": json.dumps({"rewritten_question": normalized_question}),
        }

        if not chunks:
            yield {
                "event": "citations",
                "data": json.dumps({"citations": [], "used_context": False}),
            }
            yield {"event": "token", "data": REFUSAL_TEXT}
            yield {"event": "done", "data": "ok"}
            return

        cits = [c.model_dump() for c in _to_citations(chunks)]
        yield {
            "event": "citations",
            "data": json.dumps({"citations": cits, "used_context": True}),
        }
        for tok in stream_generate(normalized_question, chunks):
            yield {"event": "token", "data": tok}
        yield {"event": "done", "data": "ok"}

    return EventSourceResponse(event_gen())
