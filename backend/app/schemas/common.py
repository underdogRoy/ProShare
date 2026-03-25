"""Common response schemas."""
from pydantic import BaseModel


class APIError(BaseModel):
    code: str
    message: str
