from pydantic import BaseModel, Field


class TaskStatusOut(BaseModel):
    task_id: str
    status: str
    progress: int
    total_points: int
    anomaly_count: int


class TaskListItem(BaseModel):
    task_id: str
    reservoir_name: str
    original_filename: str
    status: str
    total_points: int
    anomaly_count: int
    created_at: str


class VisualizationOut(BaseModel):
    contour_html: str = ""
    contour_url: str = ""
    grid: dict = Field(default_factory=dict)
    volume_3d_url: str = ""
    depths: list = Field(default_factory=list)
