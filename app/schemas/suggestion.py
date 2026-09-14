from pydantic import BaseModel, Field


class SuggestionRequest(BaseModel):
    resume_id: int = Field(gt=0)
    job_id: int = Field(gt=0)


class SuggestionContent(BaseModel):
    overall_assessment: str = Field(
        description=(
            "A concise assessment of the candidate's "
            "current fit for the job."
        )
    )

    strengths: list[str] = Field(
        description=(
            "Strengths supported by the resume and "
            "matched skills."
        )
    )

    resume_improvements: list[str] = Field(
        description=(
            "Honest resume improvements that do not "
            "invent experience."
        )
    )

    learning_recommendations: list[str] = Field(
        description=(
            "Skills or topics the candidate should learn "
            "or practise before applying."
        )
    )


class SuggestionResponse(SuggestionContent):
    resume_id: int
    job_id: int
    match_score: float = Field(ge=0, le=100)
    required_skill_count: int = Field(ge=1)
    matched_skills: list[str]
    missing_skills: list[str]
    provider: str
    model: str