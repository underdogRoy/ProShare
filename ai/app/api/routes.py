from fastapi import APIRouter

from ai.app.schemas.summary import GenerateSummaryRequest, GenerateSummaryResponse
from ai.app.services.cache import get_cached
from ai.app.services.summarizer import summarize_article

router = APIRouter(prefix="/summaries", tags=["summaries"])


@router.post("/generate", response_model=GenerateSummaryResponse)
def generate(payload: GenerateSummaryRequest) -> GenerateSummaryResponse:
    cached = get_cached(payload.article_id, payload.method)
    if cached:
        return GenerateSummaryResponse(summary=cached)
    summary = summarize_article(payload.content, payload.method)
    return GenerateSummaryResponse(summary=summary)
