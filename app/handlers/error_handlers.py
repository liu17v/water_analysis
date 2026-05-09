from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from app.config.response import BusinessException
from app.config.logging import get_logger

logger = get_logger("system")


async def business_exception_handler(request: Request, exc: BusinessException):
    logger.warning(f"业务异常 | {exc.msg}")
    return JSONResponse(status_code=exc.code, content={"status": 0, "messages": exc.msg})


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP异常 | {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"status": 0, "messages": str(exc.detail)})


async def server_exception_handler(request: Request, exc: Exception):
    logger.error(f"服务器内部错误 | {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"status": 0, "messages": "服务器内部错误"})
