from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.middleware.auth import get_current_user
from app.models.models import Bookmark, Comment, Like

router = APIRouter(prefix="/articles", tags=["engagement"])


@router.post("/{article_id}/like", status_code=201)
def like(article_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    like_obj = Like(article_id=article_id, user_id=user.id)
    db.add(like_obj)
    db.commit()
    return {"message": "liked"}


@router.delete("/{article_id}/like", status_code=204)
def unlike(article_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    like_obj = db.query(Like).filter(Like.article_id == article_id, Like.user_id == user.id).first()
    if like_obj:
        db.delete(like_obj)
        db.commit()


@router.post("/{article_id}/comments", status_code=201)
def add_comment(article_id: int, payload: dict, user=Depends(get_current_user), db: Session = Depends(get_db)):
    comment = Comment(article_id=article_id, user_id=user.id, parent_comment_id=payload.get("parent_comment_id"), content=payload["content"])
    db.add(comment)
    db.commit()
    return {"id": comment.id}


@router.get("/{article_id}/comments")
def comments(article_id: int, db: Session = Depends(get_db)):
    return db.query(Comment).filter(Comment.article_id == article_id).all()


@router.post("/{article_id}/bookmark", status_code=201)
def bookmark(article_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    mark = Bookmark(article_id=article_id, user_id=user.id)
    db.add(mark)
    db.commit()
    return {"message": "bookmarked"}


@router.delete("/{article_id}/bookmark", status_code=204)
def unbookmark(article_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    mark = db.query(Bookmark).filter(Bookmark.article_id == article_id, Bookmark.user_id == user.id).first()
    if mark:
        db.delete(mark)
        db.commit()
