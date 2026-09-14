from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.application import ApplicationStatus


class ApplicationCreate(BaseModel):
    job_id: int = Field(gt=0)
    resume_id: int = Field(gt=0)

    notes: str | None = Field(
        default=None,
        max_length=5000,
    )

    @field_validator("notes")
    @classmethod
    def clean_notes(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return value.strip() or None


class ApplicationNotesUpdate(BaseModel):
    notes: str | None = Field(
        default=None,
        max_length=5000,
    )

    @field_validator("notes")
    @classmethod
    def clean_notes(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        return value.strip() or None

    @model_validator(mode="after")
    def require_notes_field(self) -> "ApplicationNotesUpdate":
        if "notes" not in self.model_fields_set:
            raise ValueError("Notes field must be provided")

        return self


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationHistoryResponse(BaseModel):
    id: int
    old_status: ApplicationStatus | None
    new_status: ApplicationStatus
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    resume_id: int
    status: ApplicationStatus
    match_score: float
    notes: str | None
    applied_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationDetailResponse(ApplicationResponse):
    history: list[ApplicationHistoryResponse]