from typing import Any
from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    status: int = Field(default=1, description="1=成功, 0=失败")
    messages: str = Field(default="操作成功")
    datas: Any = Field(default=None)


def success(datas: Any = None, messages: str = "操作成功"):
    return ApiResponse(status=1, messages=messages, datas=datas)


def fail(messages: str = "操作失败", status: int = 0):
    return ApiResponse(status=status, messages=messages, datas=None)


class BusinessException(Exception):
    def __init__(self, msg: str = "业务异常", code: int = 404):
        self.msg = msg
        self.code = code
        super().__init__(self.msg)
