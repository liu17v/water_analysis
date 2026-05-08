"""认证相关 Pydantic 模型"""
from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=32)
    password: str = Field(..., min_length=6, max_length=64)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=32)
    password: str = Field(..., min_length=6, max_length=64)


class AdminCreateUserRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=32)
    password: str = Field(..., min_length=6, max_length=64)
    role: str = Field("user", pattern="^(admin|user)$")


class UpdateRoleRequest(BaseModel):
    role: Optional[str] = Field(None, pattern="^(admin|user)$")
    username: Optional[str] = Field(None, min_length=2, max_length=32)
    password: Optional[str] = Field(None, min_length=6, max_length=64)


class UserOut(BaseModel):
    id: int
    username: str
    role: str
