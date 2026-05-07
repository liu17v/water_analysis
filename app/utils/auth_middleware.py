import os
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv
from .jwt_util import verify_token
from .log_config import get_logger

load_dotenv()

logger = get_logger("system")

WHITE_LIST = [
    "/",
    "/api/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/upload",
]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if os.getenv("USER_AUTHORIZATION") != "True":
            return await call_next(request)

        path = request.url.path

        # Static files
        if path.startswith("/static/") or path.startswith("/reports/"):
            return await call_next(request)

        # Whitelist
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
