from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum, Float, ForeignKey
from datetime import datetime
from app.config.database import Base
import enum


class TaskStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    success = "success"
    failed = "failed"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reservoir_name = Column(String(64), default="")
    original_filename = Column(String(255))
    file_path = Column(String(512))
    total_points = Column(Integer, default=0)
    anomaly_count = Column(Integer, default=0)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.pending)
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    report_path = Column(String(512), nullable=True)
