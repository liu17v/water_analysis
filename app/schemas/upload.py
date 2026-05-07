from pydantic import BaseModel, Field


class UploadOut(BaseModel):
    task_id: str = Field(..., description="Created task UUID")
