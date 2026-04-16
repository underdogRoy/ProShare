import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker

from services.shared.app.database import build_engine
from services.shared.app.security import decode_token

DATABASE_URL = os.getenv("NOTIFICATIONS_DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/proshare_notifications")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

engine = build_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
auth = HTTPBearer()


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient_user_id: Mapped[int] = mapped_column(Integer, index=True)
    actor_user_id: Mapped[int] = mapped_column(Integer)
    article_id: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(20))  # "like", "bookmark", "comment"
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NotificationIn(BaseModel):
    recipient_user_id: int
    article_id: int
    type: str


app = FastAPI(title="Notifications Service")
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user_id(credentials: HTTPAuthorizationCredentials = Depends(auth)) -> int:
    return decode_token(credentials.credentials, JWT_SECRET)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/notifications")
def create_notification(
    payload: NotificationIn,
    actor_user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db),
):
    # Don't notify users about their own actions
    if payload.recipient_user_id == actor_user_id:
        return {"ok": True, "skipped": True}
    notification = Notification(
        recipient_user_id=payload.recipient_user_id,
        actor_user_id=actor_user_id,
        article_id=payload.article_id,
        type=payload.type,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return {"ok": True, "id": notification.id}


@app.get("/notifications/unread-count")
def unread_count(user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    count = (
        db.query(func.count(Notification.id))
        .filter(Notification.recipient_user_id == user_id, Notification.read == False)  # noqa: E712
        .scalar()
        or 0
    )
    return {"count": count}


@app.get("/notifications")
def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50),
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db),
):
    q = db.query(Notification).filter(Notification.recipient_user_id == user_id)
    if unread_only:
        q = q.filter(Notification.read == False)  # noqa: E712
    notifications = q.order_by(Notification.created_at.desc()).limit(limit).all()
    return [
        {
            "id": n.id,
            "recipient_user_id": n.recipient_user_id,
            "actor_user_id": n.actor_user_id,
            "article_id": n.article_id,
            "type": n.type,
            "read": n.read,
            "created_at": n.created_at,
        }
        for n in notifications
    ]


@app.patch("/notifications/read-all")
def mark_all_read(user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.recipient_user_id == user_id,
        Notification.read == False,  # noqa: E712
    ).update({"read": True})
    db.commit()
    return {"ok": True}


@app.patch("/notifications/{notification_id}/read")
def mark_read(
    notification_id: int,
    user_id: int = Depends(current_user_id),
    db: Session = Depends(get_db),
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.recipient_user_id == user_id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.read = True
    db.commit()
    return {"ok": True}