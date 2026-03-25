from datetime import datetime

from pydantic import BaseModel, Field


class ArticleCreate(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    content: str = Field(min_length=1)
    tags: list[str] = []


class ArticleUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None


class ArticleOut(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    status: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None

    model_config = {"from_attributes": True}
