from typing import Literal

from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    resume_id: int = Field(gt=0)
    job_id: int = Field(gt=0)


class MatchResponse(BaseModel):
    resume_id: int
    job_id: int

    match_score: float = Field(
        ge=0,
        le=100,
    )

    required_skill_count: int
    matched_skills: list[str]
    missing_skills: list[str]
    additional_resume_skills: list[str]
    resume_skills: list[str]
    required_skills: list[str]

    algorithm: Literal["keyword_and_alias"] = (
        "keyword_and_alias"
    )