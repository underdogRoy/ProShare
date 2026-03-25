"""Summary retrieval and generation dispatch."""
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Article, Summary, SummaryMethod, SummaryRateLimitLog


async def generate_or_get_summary(
    article: Article,
    user_id: int,
    method: SummaryMethod,
    regenerate: bool,
    db: Session,
) -> dict:
    if regenerate:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        log = (
            db.query(SummaryRateLimitLog)
            .filter(
                SummaryRateLimitLog.article_id == article.id,
                SummaryRateLimitLog.user_id == user_id,
                SummaryRateLimitLog.method == method,
                SummaryRateLimitLog.created_at >= cutoff,
            )
            .first()
        )
        if log:
            raise PermissionError("RATE_LIMIT_EXCEEDED")

    cached = (
        db.query(Summary)
        .filter(Summary.article_id == article.id, Summary.method == method)
        .order_by(Summary.created_at.desc())
        .first()
    )
    if cached and not regenerate:
        return {"summary": cached.summary_text, "cached": True}

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{settings.ai_service_url}/summaries/generate",
                json={"article_id": article.id, "content": article.content, "method": method.value},
            )
            response.raise_for_status()
            data = response.json()
    except Exception:
        if cached:
            return {"summary": cached.summary_text, "cached": True, "fallback": True}
        return {"summary": "Summary unavailable; please try again later", "cached": False}

    summary = Summary(
        article_id=article.id,
        method=method,
        summary_text=data["summary"],
    )
    db.merge(summary)
    db.add(SummaryRateLimitLog(article_id=article.id, user_id=user_id, method=method))
    db.commit()
    return {"summary": data["summary"], "cached": False}
