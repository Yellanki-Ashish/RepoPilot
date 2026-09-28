from typing import Any, Optional

from pydantic import BaseModel, Field


class RoadmapRequest(BaseModel):
    repository: str = Field(..., min_length=1, examples=["psf_requests"])
    include_ai_summary: bool = True


class RoadmapDay(BaseModel):
    day: int
    title: str
    description: str
    tasks: list[str]
    files: list[str] = []


class ReadingItem(BaseModel):
    file: str
    reason: str


class Difficulty(BaseModel):
    level: str
    reasons: list[str]


class RoadmapResponse(BaseModel):
    repository: str
    difficulty: Difficulty
    architecture_overview: str
    reading_order: list[ReadingItem]
    days: list[RoadmapDay]
    contribution_steps: list[str]
    suggested_first_issue: Optional[dict[str, Any]] = None
    ai_summary: Optional[str] = None
    notes: list[str] = []
