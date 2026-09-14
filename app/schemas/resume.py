from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    id: int
    original_filename: str
    file_type: str
    file_size: int
    processing_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)