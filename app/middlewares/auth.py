import os
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
from app.utils.jwt_util import verify_token
from app.config.logging import get_logger

load_dotenv()

logger = get_logger("system")

WHITE_LIST = [
    "/",
    "/api/health",
    "/api/auth/login",
    "/api/auth/register",
    "/docs",
    "/redoc",
    "/openapi.json",
]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if os.getenv("USER_AUTHORIZATION") != "True":
            return await call_next(request)

        path = request.url.path

        if path.startswith("/static/") or path.startswith("/ui/") or path == "/ui" or path == "/favicon.ico" or path.startswith("/reports/"):
            return await call_next(request)

        for white in WHITE_LIST:
            if path == white or path.startswith(white + "/") or path.startswith(white + "?"):
                return await call_next(request)

        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("authorization", "")
            if auth_header.lower().startswith("bearer "):
                token = auth_header[7:]

        if not token:
            return Response("未提供认证Token", status_code=401)

        user_info = verify_token(token)
        if not user_info:
            return Response("Token无效或已过期", status_code=401)

        request.state.user = user_info
        return await call_next(request)


def get_current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        token = request.cookies.get("token")
        if not token:
            auth_header = request.headers.get("authorization", "")
            if auth_header.lower().startswith("bearer "):
                token = auth_header[7:]
        if token:
            user = verify_token(token)
            if user:
                request.state.user = user
    return user


def require_admin(request: Request):
    user = get_current_user(request)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="请先登录")
    if user.get("role") != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
