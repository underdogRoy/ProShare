from pydantic import BaseModel, Field


class GenerateSummaryRequest(BaseModel):
    article_id: int
    content: str = Field(min_length=1)
    method: str = "abstractive"


class GenerateSummaryResponse(BaseModel):
    summary: str
    disclaimer: str = "AI-generated summary; please read full article for complete understanding"
