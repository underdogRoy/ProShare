"""Article operations and feed calculations."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Article, ArticleStatus, Comment, Like
from app.schemas.article import ArticleCreate, ArticleUpdate


def create_article(payload: ArticleCreate, user_id: int, db: Session) -> Article:
    article = Article(user_id=user_id, **payload.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def update_article(article: Article, payload: ArticleUpdate, db: Session) -> Article:
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(article, key, value)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def publish_article(article: Article, db: Session) -> Article:
    article.status = ArticleStatus.PUBLISHED
    article.published_at = datetime.now(timezone.utc)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def recent_feed(db: Session) -> list[Article]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    return (
        db.query(Article)
        .filter(Article.status == ArticleStatus.PUBLISHED, Article.published_at >= cutoff)
        .order_by(Article.published_at.desc())
        .all()
    )


def trending_feed(db: Session) -> list[Article]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    age_factor = func.extract("epoch", func.now() - Article.published_at) / 86400
    score = func.count(Like.id) * 0.6 + func.count(Comment.id) * 0.3 + (30 - age_factor) * 0.1
    rows = (
        db.query(Article.id)
        .outerjoin(Like, Like.article_id == Article.id)
        .outerjoin(Comment, Comment.article_id == Article.id)
        .filter(Article.status == ArticleStatus.PUBLISHED, Article.published_at >= cutoff)
        .group_by(Article.id)
        .order_by(score.desc())
        .limit(50)
        .all()
    )
    ids = [x.id for x in rows]
    if not ids:
        return []
    return db.query(Article).filter(Article.id.in_(ids)).all()
