from pydantic import BaseModel


class SimilarTaskOut(BaseModel):
    task_id: str
    similarity: float
    reservoir: str
    date: str
    report_url: str


class ReportOut(BaseModel):
    report_url: str
