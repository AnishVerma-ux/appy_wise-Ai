from pydantic import BaseModel, Field


class DashboardResponse(BaseModel):
    total_applications: int = Field(ge=0)
    interviews: int = Field(ge=0)
    offers: int = Field(ge=0)
    rejections: int = Field(ge=0)
    average_match_score: float = Field(ge=0, le=100)