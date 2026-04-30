from fastapi import APIRouter

from ..config import get_settings
from ..llm.query_rewriter import rewrite_query
from ..rag.retriever import retrieve
from ..schemas import Citation, SearchRequest, SearchResponse

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    settings = get_settings()
    normalized_query = rewrite_query(req.query)
    chunks = retrieve(
        query=normalized_query,
        chroma_dir=settings.chroma_path,
        collection_name=settings.collection_name,
        embed_model=settings.embed_model,
        top_k=req.top_k,
        min_score=0.0,
    )
    results = [
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
    return SearchResponse(results=results)
