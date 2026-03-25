import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, create_engine, func
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker

from services.shared.app.security import decode_token

DATABASE_URL = os.getenv("ENGAGEMENT_DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/proshare_engagement")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
auth = HTTPBearer()


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_like"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    article_id: Mapped[int] = mapped_column(Integer, index=True)


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_bookmark"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    article_id: Mapped[int] = mapped_column(Integer, index=True)


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_type: Mapped[str] = mapped_column(String(20))
    target_id: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    reporter_id: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CommentIn(BaseModel):
    content: str


class ReportIn(BaseModel):
    target_type: str
    target_id: int
    reason: str


app = FastAPI(title="Engagement Service")
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


@app.post("/articles/{article_id}/like")
def like(article_id: int, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    if not db.query(Like).filter_by(article_id=article_id, user_id=user_id).first():
        db.add(Like(article_id=article_id, user_id=user_id))
        db.commit()
    return {"ok": True}


@app.post("/articles/{article_id}/bookmark")
def bookmark(article_id: int, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    if not db.query(Bookmark).filter_by(article_id=article_id, user_id=user_id).first():
        db.add(Bookmark(article_id=article_id, user_id=user_id))
        db.commit()
    return {"ok": True}


@app.post("/articles/{article_id}/comments")
def add_comment(article_id: int, payload: CommentIn, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    comment = Comment(article_id=article_id, user_id=user_id, content=payload.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@app.get("/articles/{article_id}/comments")
def list_comments(article_id: int, db: Session = Depends(get_db)):
    return db.query(Comment).filter(Comment.article_id == article_id).order_by(Comment.created_at).all()


@app.get("/articles/{article_id}/stats")
def stats(article_id: int, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    likes = db.query(func.count(Like.id)).filter(Like.article_id == article_id).scalar() or 0
    comments = db.query(func.count(Comment.id)).filter(Comment.article_id == article_id).scalar() or 0
    bookmarked = db.query(Bookmark).filter_by(article_id=article_id, user_id=user_id).first() is not None
    return {"like_count": likes, "comment_count": comments, "bookmarked": bookmarked}


@app.post("/reports")
def report(payload: ReportIn, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    db.add(Report(**payload.model_dump(), reporter_id=user_id))
    db.commit()
    return {"ok": True}
