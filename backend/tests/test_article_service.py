from datetime import datetime, timezone

from app.models.models import Article


def test_trending_formula_reference() -> None:
    likes_count = 10
    comments_count = 3
    published_at = datetime.now(timezone.utc)
    recency = 30
    score = likes_count * 0.6 + comments_count * 0.3 + recency * 0.1
    assert round(score, 2) == 9.9
    assert published_at is not None
    assert Article.__tablename__ == "articles"
