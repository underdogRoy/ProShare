from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str


class ProfileUpdate(BaseModel):
    bio: str = ""
    expertise_tags: str = ""
    links: str = ""


class UserOut(BaseModel):
    id: int
    email: str
    username: str
    bio: str
    expertise_tags: str
    links: str
    is_admin: bool

    class Config:
        from_attributes = True


class ArticleCreate(BaseModel):
    title: str
    content: str
    tags: str = ""
    status: str = "draft"


class ArticleUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: str | None = None
    status: str | None = None


class CommentCreate(BaseModel):
    content: str


class SummaryFeedbackIn(BaseModel):
    helpful: bool
    feedback: str = ""


class ReportIn(BaseModel):
    target_type: str
    target_id: int
    reason: str


class SummaryResponse(BaseModel):
    article_id: int
    tldr: str
    takeaways: List[str]
    cached: bool


class ArticleDetail(BaseModel):
    id: int
    title: str
    content: str
    tags: str
    status: str
    author_id: int
    like_count: int
    comment_count: int
    bookmarked: bool
    created_at: datetime
    updated_at: datetime


class CommentOut(BaseModel):
    id: int
    article_id: int
    user_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
