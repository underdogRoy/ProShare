"""Article routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.middleware.auth import get_current_user
from app.models.models import Article, ArticleStatus, SummaryFeedback, SummaryMethod
from app.schemas.article import ArticleCreate, ArticleOut, ArticleUpdate
from app.schemas.summary import SummaryFeedbackRequest, SummaryRequest
from app.services.article_service import create_article, publish_article, recent_feed, trending_feed, update_article
from app.services.summary_service import generate_or_get_summary

router = APIRouter(prefix="/articles", tags=["articles"])


@router.post("", response_model=ArticleOut, status_code=201)
def create(payload: ArticleCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return create_article(payload, user.id, db)


@router.get("", response_model=list[ArticleOut])
def list_published(db: Session = Depends(get_db)):
    return db.query(Article).filter(Article.status == ArticleStatus.PUBLISHED).all()


@router.get("/search", response_model=list[ArticleOut])
def search(q: str = Query(min_length=2), db: Session = Depends(get_db)):
    return db.query(Article).filter(Article.status == ArticleStatus.PUBLISHED, Article.title.ilike(f"%{q}%")).all()


@router.get("/tags/{tag}", response_model=list[ArticleOut])
def by_tag(tag: str, db: Session = Depends(get_db)):
    return db.query(Article).filter(Article.tags.any(tag), Article.status == ArticleStatus.PUBLISHED).all()


@router.get("/recent", response_model=list[ArticleOut])
def recent(db: Session = Depends(get_db)):
    return recent_feed(db)


@router.get("/trending", response_model=list[ArticleOut])
def trending(db: Session = Depends(get_db)):
    return trending_feed(db)


@router.get("/{article_id}", response_model=ArticleOut)
def detail(article_id: int, db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return article


@router.put("/{article_id}", response_model=ArticleOut)
def update(article_id: int, payload: ArticleUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    if article.user_id != user.id:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    return update_article(article, payload, db)


@router.post("/{article_id}/publish", response_model=ArticleOut)
def publish(article_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    if article.user_id != user.id:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    return publish_article(article, db)


@router.delete("/{article_id}", status_code=204)
def remove(article_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    if article.user_id != user.id:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    db.delete(article)
    db.commit()


@router.post("/{article_id}/summary")
async def summary(article_id: int, payload: SummaryRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    article = db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    try:
        return await generate_or_get_summary(
            article,
            user.id,
            SummaryMethod(payload.method),
            payload.regenerate,
            db,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@router.get("/{article_id}/summary")
def get_summary(article_id: int, db: Session = Depends(get_db)):
    from app.models.models import Summary
    summary_obj = (
        db.query(Summary)
        .filter(Summary.article_id == article_id)
        .order_by(Summary.created_at.desc())
        .first()
    )
    if not summary_obj:
        raise HTTPException(status_code=404, detail="SUMMARY_NOT_FOUND")
    return {"summary": summary_obj.summary_text, "method": summary_obj.method}


@router.post("/{article_id}/summary/feedback", status_code=201)
def summary_feedback(article_id: int, payload: SummaryFeedbackRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    from app.models.models import Summary
    summary_obj = db.query(Summary).filter(Summary.article_id == article_id).order_by(Summary.created_at.desc()).first()
    if not summary_obj:
        raise HTTPException(status_code=404, detail="SUMMARY_NOT_FOUND")
    feedback = SummaryFeedback(summary_id=summary_obj.id, user_id=user.id, rating=payload.rating, feedback_text=payload.feedback_text)
    db.add(feedback)
    db.commit()
    return {"message": "saved"}
