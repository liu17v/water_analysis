"""数据上传控制器"""
import os
import asyncio
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.response import success, fail, BusinessException
from app.schemas.upload import UploadOut
from app.services.data_service import DataService
from app.services.celery_tasks import process_csv, run_task_local
from app.config.settings import get_settings
from app.utils.log_config import get_logger

logger = get_logger("controllers.upload")
settings = get_settings()
upload_router = APIRouter(tags=["数据上传"])


@upload_router.post("/api/upload", summary="上传CSV数据")
async def upload_csv(
    file: UploadFile = File(...),
    reservoir_name: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext != ".csv":
        raise BusinessException(msg="仅支持 CSV 格式文件", code=400)

    content = await file.read()
    if not content:
        raise BusinessException(msg="文件为空", code=400)

    rows = DataService.parse_csv(content)
    if not rows:
        raise BusinessException(msg="CSV 无有效数据行，请检查 lon/lat/depth_m 字段", code=400)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    task_id = await DataService.create_task(
        db, file.filename or "unknown.csv", file_path,
        len(rows), reservoir_name,
    )
    await DataService.save_raw_data(db, task_id, rows)

    # 本地异步处理（开发/单机环境无需 Celery worker）
    asyncio.create_task(run_task_local(task_id))
    logger.info(f"CSV上传完成 | task_id={task_id} | rows={len(rows)}")

    return success(datas=UploadOut(task_id=task_id).model_dump())
