"""水质三维智能监测与分析系统 - 应用入口"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.config.database import engine
from app.config.response import BusinessException
from app.config.settings import get_settings
from app.models import init_tables
from app.services.milvus_service import connect as milvus_connect, init_collection
from app.middlewares.auth import AuthMiddleware
from app.handlers.error_handlers import (
    business_exception_handler,
    http_exception_handler,
    server_exception_handler,
)
from app.config.logging import setup_logging, get_logger

# 日志系统最先初始化
setup_logging()
logger = get_logger("system")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("应用启动中...")
    await init_tables()
    logger.info("数据库表初始化完成")

    try:
        milvus_connect()
        init_collection()
        logger.info("Milvus 集合初始化完成")
    except Exception as e:
        logger.warning(f"Milvus 初始化失败（可能未部署）: {e}")

    logger.info(f"【{settings.APP_NAME}】启动成功")
    yield
    await engine.dispose()
    logger.info("数据库连接池已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "系统", "description": "健康检查等系统级接口。"},
        {"name": "认证与用户管理", "description": "用户注册、登录、登出，以及管理员对用户的增删改查操作。"},
        {"name": "仪表盘", "description": "系统全局统计概览：任务总量、异常分布、成功率、近期趋势。"},
        {"name": "数据上传", "description": "CSV 文件上传，字段自动解析，触发后台分析流水线。"},
        {"name": "任务管理", "description": "分析任务全生命周期管理：状态查询、统计、可视化、原始数据浏览、删除与重处理。"},
        {"name": "异常管理", "description": "异常点查询与筛选（按指标/方法/深度/数值），支持 CSV 导出。"},
        {"name": "智能报告", "description": "报告生成、相似案例检索、报告状态查询与删除。"},
    ],
)

# 异常处理
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, server_exception_handler)

# 路由注册
from app.routers.upload import upload_router
from app.routers.task import task_router
from app.routers.anomaly import anomaly_router
from app.routers.report import report_router
from app.routers.auth import auth_router
from app.routers.dashboard import dashboard_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(upload_router)
api_router.include_router(task_router)
api_router.include_router(anomaly_router)
api_router.include_router(report_router)
app.include_router(api_router)


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")


# 静态文件
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR, html=True), name="static")
app.mount("/reports", StaticFiles(directory=settings.REPORT_DIR), name="reports")
app.mount("/3d", StaticFiles(directory=settings.THREED_DIR), name="3d")

# 中间件（注册顺序在后，优先执行）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)


@app.get("/api/health", summary="健康检查", tags=["系统"])
def health():
    return {"status": "ok", "app": settings.APP_NAME}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
