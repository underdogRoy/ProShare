import hashlib
import json
import os
import re
from collections import Counter
from datetime import datetime

import redis
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, create_engine
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker

from services.shared.app.security import decode_token

DATABASE_URL = os.getenv("SUMMARY_DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/proshare_summary")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
auth = HTTPBearer()
cache = redis.Redis.from_url(REDIS_URL, decode_responses=True)


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    article_id: Mapped[int] = mapped_column(Integer, index=True, unique=True)
    source_hash: Mapped[str] = mapped_column(String(64), index=True)
    tldr: Mapped[str] = mapped_column(Text)
    takeaways: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "summary_feedback"
    __table_args__ = (UniqueConstraint("summary_id", "user_id", name="uq_summary_feedback_per_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    summary_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    helpful: Mapped[bool] = mapped_column(Boolean)
    feedback: Mapped[str] = mapped_column(Text, default="")


class SummaryIn(BaseModel):
    article_id: int
    content: str
    regenerate: bool = False


class FeedbackIn(BaseModel):
    article_id: int
    helpful: bool
    feedback: str = ""


app = FastAPI(title="AI Summary Service")
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user_id(credentials: HTTPAuthorizationCredentials = Depends(auth)) -> int:
    return decode_token(credentials.credentials, JWT_SECRET)


def summarize_text(content: str) -> tuple[str, list[str]]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if s.strip()]
    if not sentences:
        return "No content.", []
    words = [w.lower() for w in re.findall(r"[a-zA-Z]{4,}", content)]
    keywords = ", ".join([w for w, _ in Counter(words).most_common(5)])
    bullets = [f"{idx}. {sentence[:140]}" for idx, sentence in enumerate(sentences[:4], start=1)]
    if keywords:
        bullets.append(f"Keywords: {keywords}")
    return " ".join(sentences[:2])[:420], bullets


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/summary/generate")
def generate(payload: SummaryIn, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    throttle_key = f"summary:regen:{user_id}:{payload.article_id}"
    if payload.regenerate and cache.get(throttle_key):
        raise HTTPException(status_code=429, detail="Regenerate is rate-limited")

    content_hash = hashlib.sha256(payload.content.encode("utf-8")).hexdigest()
    cache_key = f"summary:{payload.article_id}:{content_hash}"

    if not payload.regenerate:
        cached = cache.get(cache_key)
        if cached:
            return {"article_id": payload.article_id, "cached": True, **json.loads(cached)}

    row = db.query(Summary).filter(Summary.article_id == payload.article_id).first()
    if row and row.source_hash == content_hash and not payload.regenerate:
        return {
            "article_id": payload.article_id,
            "cached": True,
            "tldr": row.tldr,
            "takeaways": row.takeaways.split("\n"),
        }

    tldr, takeaways = summarize_text(payload.content)
    if row:
        row.source_hash = content_hash
        row.tldr = tldr
        row.takeaways = "\n".join(takeaways)
    else:
        db.add(Summary(article_id=payload.article_id, source_hash=content_hash, tldr=tldr, takeaways="\n".join(takeaways)))
    db.commit()

    response = {"tldr": tldr, "takeaways": takeaways}
    cache.setex(cache_key, 3600, json.dumps(response))
    if payload.regenerate:
        cache.setex(throttle_key, 30, "1")

    return {"article_id": payload.article_id, "cached": False, **response}


@app.post("/summary/feedback")
def feedback(payload: FeedbackIn, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    row = db.query(Summary).filter(Summary.article_id == payload.article_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Summary not found")

    existing = db.query(Feedback).filter(Feedback.summary_id == row.id, Feedback.user_id == user_id).first()
    if existing:
        existing.helpful = payload.helpful
        existing.feedback = payload.feedback
    else:
        db.add(Feedback(summary_id=row.id, user_id=user_id, helpful=payload.helpful, feedback=payload.feedback))
    db.commit()
    return {"ok": True}
