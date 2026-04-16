import os
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime, Integer, String, Text, desc, func
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, sessionmaker

from services.shared.app.database import build_engine
from services.shared.app.security import decode_token, decode_token_payload

DATABASE_URL = os.getenv("CONTENT_DB_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/proshare_content")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")

engine = build_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()
auth = HTTPBearer()


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    author_id: Mapped[int] = mapped_column(Integer, index=True)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ArticleIn(BaseModel):
    title: str
    content: str
    tags: str = ""
    status: str = "draft"


class ArticlePatch(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: str | None = None
    status: str | None = None


app = FastAPI(title="Content Service")
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


@app.post("/articles")
def create_article(payload: ArticleIn, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    article = Article(**payload.model_dump(), author_id=user_id)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@app.put("/articles/{article_id}")
def update_article(article_id: int, payload: ArticlePatch, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Not found")
    if article.status == "deleted":
        raise HTTPException(status_code=400, detail="Deleted articles cannot be edited")
    if article.author_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    for key, value in payload.model_dump().items():
        if value is not None:
            setattr(article, key, value)
    db.commit()
    db.refresh(article)
    return article


@app.get("/articles/batch")
def batch_articles(ids: str = Query(""), user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    if not ids:
        return []
    id_list = [int(i) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        return []
    return (
        db.query(Article)
        .filter(Article.id.in_(id_list), Article.status == "published", Article.hidden.is_(False))
        .all()
    )


@app.get("/articles/mine")
def my_articles(user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    return (
        db.query(Article)
        .filter(Article.author_id == user_id, Article.status != "deleted")
        .order_by(desc(Article.updated_at))
        .all()
    )


@app.get("/articles/{article_id}")
def get_article(article_id: int, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    article = (
        db.query(Article)
        .filter(Article.id == article_id, Article.hidden.is_(False), Article.status != "deleted")
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Not found")
    if article.status != "published" and article.author_id != user_id:
        raise HTTPException(status_code=403, detail="Private draft")
    return article


@app.get("/feeds/recent")
def recent_feed(db: Session = Depends(get_db)):
    return (
        db.query(Article)
        .filter(Article.status == "published", Article.hidden.is_(False))
        .order_by(desc(Article.created_at))
        .limit(30)
        .all()
    )


@app.get("/search")
def search(q: str = Query(""), db: Session = Depends(get_db)):
    if not q:
        return []
    query = f"%{q.lower()}%"
    return (
        db.query(Article)
        .filter(
            Article.status == "published",
            Article.hidden.is_(False),
            (func.lower(Article.title).like(query))
            | (func.lower(Article.content).like(query))
            | (func.lower(Article.tags).like(query)),
        )
        .order_by(desc(Article.created_at))
        .limit(30)
        .all()
    )


@app.delete("/articles/{article_id}")
def delete_article(article_id: int, user_id: int = Depends(current_user_id), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Not found")
    if article.author_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if article.status == "deleted":
        raise HTTPException(status_code=400, detail="Article already deleted")
    article.status = "deleted"
    article.hidden = True
    db.commit()
    return {"ok": True}


@app.post("/admin/articles/{article_id}/hide")
def hide_article(article_id: int, admin_id: int = Depends(require_admin), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Not found")
    if article.status == "deleted":
        raise HTTPException(status_code=400, detail="Article already removed")
    article.hidden = True
    db.commit()
    return {"ok": True, "action": "hidden", "article_id": article.id, "admin_id": admin_id}


@app.get("/admin/articles/{article_id}")
def admin_get_article(article_id: int, admin_id: int = Depends(require_admin), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": article.id,
        "title": article.title,
        "status": article.status,
        "hidden": article.hidden,
        "author_id": article.author_id,
        "updated_at": article.updated_at,
        "admin_id": admin_id,
    }


@app.post("/admin/articles/{article_id}/unhide")
def unhide_article(article_id: int, admin_id: int = Depends(require_admin), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Not found")
    if article.status == "deleted":
        raise HTTPException(status_code=400, detail="Deleted articles cannot be restored from hide")
    article.hidden = False
    db.commit()
    return {"ok": True, "action": "visible", "article_id": article.id, "admin_id": admin_id}


@app.post("/admin/articles/{article_id}/remove")
def remove_article(article_id: int, admin_id: int = Depends(require_admin), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Not found")
    article.hidden = True
    article.status = "deleted"
    db.commit()
    return {"ok": True, "action": "removed", "article_id": article.id, "admin_id": admin_id}
