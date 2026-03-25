from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.middleware.auth import get_current_user
from app.models.models import Article, User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="NOT_FOUND")
    return {
        "id": user.id,
        "username": user.username,
        "bio": user.bio,
        "expertise_tags": user.expertise_tags,
        "social_links": user.social_links,
    }


@router.put("/{user_id}")
def update_user(user_id: int, payload: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    user = db.get(User, user_id)
    for key in ["bio", "expertise_tags", "social_links"]:
        if key in payload:
            setattr(user, key, payload[key])
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "bio": user.bio, "expertise_tags": user.expertise_tags, "social_links": user.social_links}


@router.get("/{user_id}/articles")
def user_articles(user_id: int, db: Session = Depends(get_db)):
    return db.query(Article).filter(Article.user_id == user_id).all()
