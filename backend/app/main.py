from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from .auth import create_access_token, get_current_user, hash_password, require_admin, verify_password
from .database import Base, engine, get_db
from .models import Article, ArticleLike, Bookmark, Comment, Report, Summary, SummaryFeedback, User
from .schemas import (
    ArticleCreate,
    ArticleDetail,
    ArticleUpdate,
    CommentCreate,
    CommentOut,
    LoginRequest,
    ProfileUpdate,
    RegisterRequest,
    ReportIn,
    SummaryFeedbackIn,
    SummaryResponse,
    TokenResponse,
    UserOut,
)
from .summarizer import source_hash, summarize

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ProShare API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"ok": True}


@app.post("/auth/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter((User.email == payload.email) | (User.username == payload.username)).first():
        raise HTTPException(status_code=400, detail="Email or username already exists")

    user = User(
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(str(user.id)))


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(str(user.id)))


@app.get("/users/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@app.put("/users/me", response_model=UserOut)
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.bio = payload.bio
    user.expertise_tags = payload.expertise_tags
    user.links = payload.links
    db.commit()
    db.refresh(user)
    return user


@app.post("/articles", response_model=ArticleDetail)
def create_article(payload: ArticleCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    article = Article(
        title=payload.title,
        content=payload.content,
        tags=payload.tags,
        status=payload.status,
        author_id=user.id,
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return _article_detail(db, article, user.id)


@app.put("/articles/{article_id}", response_model=ArticleDetail)
def update_article(
    article_id: int,
    payload: ArticleUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.author_id != user.id:
        raise HTTPException(status_code=403, detail="Only author can edit")

    for field in ["title", "content", "tags", "status"]:
        value = getattr(payload, field)
        if value is not None:
            setattr(article, field, value)

    db.commit()
    db.refresh(article)
    return _article_detail(db, article, user.id)


@app.get("/articles/{article_id}", response_model=ArticleDetail)
def get_article(article_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id, Article.hidden.is_(False)).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.status != "published" and article.author_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Draft is private")
    return _article_detail(db, article, user.id)


@app.get("/feeds/recent", response_model=list[ArticleDetail])
def recent_feed(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(Article)
        .filter(Article.status == "published", Article.hidden.is_(False))
        .order_by(desc(Article.created_at))
        .limit(30)
        .all()
    )
    return [_article_detail(db, row, user.id) for row in rows]


@app.get("/feeds/trending", response_model=list[ArticleDetail])
def trending_feed(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(
            Article,
            (func.count(func.distinct(ArticleLike.id)) + func.count(func.distinct(Comment.id)) * 2).label("score"),
        )
        .outerjoin(ArticleLike, ArticleLike.article_id == Article.id)
        .outerjoin(Comment, Comment.article_id == Article.id)
        .filter(Article.status == "published", Article.hidden.is_(False))
        .group_by(Article.id)
        .order_by(desc("score"), desc(Article.created_at))
        .limit(30)
        .all()
    )
    return [_article_detail(db, row[0], user.id) for row in rows]


@app.get("/search", response_model=list[ArticleDetail])
def search(q: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = f"%{q.lower()}%"
    rows = (
        db.query(Article)
        .filter(
            Article.status == "published",
            Article.hidden.is_(False),
            (func.lower(Article.title).like(query))
            | (func.lower(Article.content).like(query))
            | (func.lower(Article.tags).like(query)),
        )
        .order_by(desc(Article.created_at))
        .all()
    )
    return [_article_detail(db, row, user.id) for row in rows]


@app.post("/articles/{article_id}/like")
def like_article(article_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(ArticleLike).filter_by(article_id=article_id, user_id=user.id).first()
    if not existing:
        db.add(ArticleLike(article_id=article_id, user_id=user.id))
        db.commit()
    return {"ok": True}


@app.post("/articles/{article_id}/bookmark")
def bookmark_article(article_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(Bookmark).filter_by(article_id=article_id, user_id=user.id).first()
    if not existing:
        db.add(Bookmark(article_id=article_id, user_id=user.id))
        db.commit()
    return {"ok": True}


@app.post("/articles/{article_id}/comments", response_model=CommentOut)
def add_comment(article_id: int, payload: CommentCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    comment = Comment(article_id=article_id, user_id=user.id, content=payload.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@app.get("/articles/{article_id}/comments", response_model=list[CommentOut])
def list_comments(article_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Comment).filter(Comment.article_id == article_id).order_by(Comment.created_at).all()


@app.post("/articles/{article_id}/summary", response_model=SummaryResponse)
def get_summary(article_id: int, regenerate: bool = False, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id, Article.hidden.is_(False)).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    current_hash = source_hash(article.content)
    summary = db.query(Summary).filter(Summary.article_id == article_id).first()

    if summary and summary.source_hash == current_hash and not regenerate:
        return SummaryResponse(article_id=article_id, tldr=summary.tldr, takeaways=summary.takeaways.split("\n"), cached=True)

    tldr, takeaways = summarize(article.content)

    if summary:
        summary.tldr = tldr
        summary.takeaways = "\n".join(takeaways)
        summary.source_hash = current_hash
    else:
        summary = Summary(article_id=article_id, tldr=tldr, takeaways="\n".join(takeaways), source_hash=current_hash)
        db.add(summary)

    db.commit()
    db.refresh(summary)
    return SummaryResponse(article_id=article_id, tldr=summary.tldr, takeaways=summary.takeaways.split("\n"), cached=False)


@app.post("/articles/{article_id}/summary/feedback")
def summary_feedback(article_id: int, payload: SummaryFeedbackIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    summary = db.query(Summary).filter(Summary.article_id == article_id).first()
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")

    feedback = SummaryFeedback(summary_id=summary.id, user_id=user.id, helpful=payload.helpful, feedback=payload.feedback)
    db.add(feedback)
    db.commit()
    return {"ok": True}


@app.post("/reports")
def create_report(payload: ReportIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    report = Report(
        target_type=payload.target_type,
        target_id=payload.target_id,
        reason=payload.reason,
        reporter_id=user.id,
    )
    db.add(report)
    db.commit()
    return {"ok": True}


@app.post("/admin/articles/{article_id}/hide")
def hide_article(article_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.hidden = True
    db.commit()
    return {"ok": True}


def _article_detail(db: Session, article: Article, current_user_id: int) -> ArticleDetail:
    like_count = db.query(func.count(ArticleLike.id)).filter(ArticleLike.article_id == article.id).scalar() or 0
    comment_count = db.query(func.count(Comment.id)).filter(Comment.article_id == article.id).scalar() or 0
    bookmarked = db.query(Bookmark).filter_by(article_id=article.id, user_id=current_user_id).first() is not None

    return ArticleDetail(
        id=article.id,
        title=article.title,
        content=article.content,
        tags=article.tags,
        status=article.status,
        author_id=article.author_id,
        like_count=like_count,
        comment_count=comment_count,
        bookmarked=bookmarked,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )
