from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..deps import current_user, get_db
from ..models import User
from ..schemas import ProfileIn

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/batch")
def batch_users(ids: str = Query(""), db: Session = Depends(get_db)):
    if not ids:
        return []

    user_ids = [int(item) for item in ids.split(",") if item.strip().isdigit()]
    if not user_ids:
        return []

    users = db.query(User).filter(User.id.in_(user_ids)).all()
    return [{"id": user.id, "username": user.username} for user in users]


@router.get("/me")
def me(user: User = Depends(current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "bio": user.bio,
        "expertise_tags": user.expertise_tags,
        "links": user.links,
        "is_admin": user.is_admin,
    }


@router.put("/me")
def update_profile(payload: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.bio = payload.bio
    user.expertise_tags = payload.expertise_tags
    user.links = payload.links
    db.commit()
    return {"ok": True}
