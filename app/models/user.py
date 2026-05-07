from sqlalchemy import Column, Integer, String, DateTime, Enum as SAEnum
from datetime import datetime
from app.config.database import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(32), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.user)
    created_at = Column(DateTime, default=datetime.utcnow)
