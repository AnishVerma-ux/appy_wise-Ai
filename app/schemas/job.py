from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class JobCreate(BaseModel):
    company_name: str = Field(
        min_length=2,
        max_length=150,
    )

    job_title: str = Field(
        min_length=2,
        max_length=150,
    )

    job_description: str = Field(
        min_length=20,
        max_length=50000,
    )

    location: str | None = Field(
        default=None,
        max_length=150,
    )

    job_url: HttpUrl | None = Field(
        default=None,
        max_length=2048,
    )

    @field_validator(
        "company_name",
        "job_title",
        "job_description",
    )
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Value must not be empty")

        return cleaned

    @field_validator("location")
    @classmethod
    def clean_location(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None


class JobUpdate(BaseModel):
    company_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    job_title: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    job_description: str | None = Field(
        default=None,
        min_length=20,
        max_length=50000,
    )

    location: str | None = Field(
        default=None,
        max_length=150,
    )

    job_url: HttpUrl | None = Field(
        default=None,
        max_length=2048,
    )

    @field_validator(
        "company_name",
        "job_title",
        "job_description",
    )
    @classmethod
    def clean_required_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("Value must not be empty")

        return cleaned

    @field_validator("location")
    @classmethod
    def clean_location(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "JobUpdate":
        if not self.model_fields_set:
            raise ValueError(
                "At least one field must be provided"
            )

        if (
            "company_name" in self.model_fields_set
            and self.company_name is None
        ):
            raise ValueError(
                "Company name cannot be null"
            )

        if (
            "job_title" in self.model_fields_set
            and self.job_title is None
        ):
            raise ValueError(
                "Job title cannot be null"
            )

        if (
            "job_description" in self.model_fields_set
            and self.job_description is None
        ):
            raise ValueError(
                "Job description cannot be null"
            )

        return self


class JobResponse(BaseModel):
    id: int
    company_name: str
    job_title: str
    job_description: str
    location: str | None
    job_url: HttpUrl | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)