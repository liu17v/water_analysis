from sqlalchemy import Column, Integer, String, Float, ForeignKey
from app.config.database import Base


class RawData(Base):
    __tablename__ = "raw_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    lon = Column(Float, nullable=False)
    lat = Column(Float, nullable=False)
    depth_m = Column(Float, nullable=False)
    temperature = Column(Float, nullable=True)
    conductivity = Column(Float, nullable=True)
    salinity = Column(Float, nullable=True)
    ph = Column(Float, nullable=True)
    turbidity = Column(Float, nullable=True)
    chlorophyll = Column(Float, nullable=True)
    dissolved_oxygen = Column(Float, nullable=True)
    suspicious = Column(Integer, default=0)
