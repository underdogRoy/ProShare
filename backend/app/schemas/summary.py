from pydantic import BaseModel


class SummaryRequest(BaseModel):
    method: str = "abstractive"
    regenerate: bool = False


class SummaryFeedbackRequest(BaseModel):
    rating: str
    feedback_text: str | None = None
