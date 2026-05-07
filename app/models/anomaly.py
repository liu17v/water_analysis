from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.config.database import Base


class AnomalyRecord(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)
    depth = Column(Float, nullable=False)
    indicator = Column(String(32), nullable=False)
    value = Column(Float, nullable=False)
    method = Column(String(32), nullable=False)
    threshold_low = Column(Float, nullable=True)
    threshold_high = Column(Float, nullable=True)
