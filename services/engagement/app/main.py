import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker

from services.shared.app.database import build_engine
from services.shared.app.security import decode_token, decode_token_payload

DATABASE_URL = os.getenv("ENGAGEMENT_DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/proshare_engagement")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

engine = build_engine(DATABASE_URL)
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


class ReportResolution(Base):
    __tablename__ = "report_resolutions"
    __table_args__ = (UniqueConstraint("report_id", name="uq_report_resolution_report"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(Integer, index=True)
    admin_id: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(20))
    resolved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CommentIn(BaseModel):
    content: str


class ReportIn(BaseModel):
    target_type: str
    target_id: int
    reason: str


class ResolveReportsIn(BaseModel):
    report_id: int
    action: str


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


def require_admin(credentials: HTTPAuthorizationCredentials = Depends(auth)) -> int:
    payload = decode_token_payload(credentials.credentials, JWT_SECRET)
    if not payload["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    return int(payload["sub"])


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


@app.get("/admin/reports")
def list_reports(
    status: str = Query("open"),
    admin_id: int = Depends(require_admin),
    db: Session = Depends(get_db),
):
    resolutions = {row.report_id: row for row in db.query(ReportResolution).all()}
    reports = db.query(Report).order_by(Report.created_at.desc()).all()
    response = []
    for report in reports:
        resolution = resolutions.get(report.id)
        current_status = "resolved" if resolution else "open"
        if status != "all" and current_status != status:
            continue
        response.append(
            {
                "id": report.id,
                "target_type": report.target_type,
                "target_id": report.target_id,
                "reason": report.reason,
                "reporter_id": report.reporter_id,
                "created_at": report.created_at,
                "status": current_status,
                "resolution_action": resolution.action if resolution else None,
                "resolved_at": resolution.resolved_at if resolution else None,
                "resolved_by_admin_id": resolution.admin_id if resolution else None,
                "admin_id": admin_id,
            }
        )
    return response


@app.post("/admin/reports/resolve")
def resolve_report(payload: ResolveReportsIn, admin_id: int = Depends(require_admin), db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == payload.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    existing = db.query(ReportResolution).filter(ReportResolution.report_id == payload.report_id).first()
    if existing:
        existing.action = payload.action
        existing.admin_id = admin_id
        existing.resolved_at = datetime.utcnow()
    else:
        db.add(ReportResolution(report_id=payload.report_id, admin_id=admin_id, action=payload.action))
    db.commit()
    return {"ok": True}


@app.post("/admin/reports/{report_id}/reopen")
def reopen_report(report_id: int, admin_id: int = Depends(require_admin), db: Session = Depends(get_db)):
    resolution = db.query(ReportResolution).filter(ReportResolution.report_id == report_id).first()
    if not resolution:
        raise HTTPException(status_code=404, detail="Report is already open")
    db.delete(resolution)
    db.commit()
    return {"ok": True, "report_id": report_id, "admin_id": admin_id}
