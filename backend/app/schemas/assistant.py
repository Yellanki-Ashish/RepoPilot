from typing import Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    repository: str = Field(..., min_length=1, examples=["psf_requests"])
    question: str = Field(..., min_length=3, max_length=2000, examples=["How does authentication work?"])
    top_k: Optional[int] = Field(None, ge=1, le=20)


class Source(BaseModel):
    file: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    section: Optional[str] = None
    language: Optional[str] = None
    relevance: Optional[float] = None


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    agents_used: list[str]
    intent: Optional[str] = None
