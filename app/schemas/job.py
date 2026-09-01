from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProcessingJobResponse(BaseModel):
    id: int
    job_type: str
    status: str

    total_items: int
    processed_items: int
    failed_items: int

    error_message: str | None

    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )
