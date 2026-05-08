"""异常点查询控制器"""
import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config.database import get_db
from app.config.response import success, BusinessException
from app.models.anomaly import AnomalyRecord
from app.models.task import Task
from app.services.data_service import DataService
from app.utils.log_config import get_logger

logger = get_logger("controllers.anomaly")
anomaly_router = APIRouter(tags=["异常管理"])

INDICATOR_SHORT = ["chl", "odo", "temp", "ph", "turb"]


@anomaly_router.get("/api/anomalies", summary="全部异常点列表（跨任务）")
async def get_all_anomalies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    indicator: str = Query(None),
    task_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    base = select(AnomalyRecord)
    if indicator and indicator in INDICATOR_SHORT:
        base = base.where(AnomalyRecord.indicator == indicator)
    if task_id:
        base = base.where(AnomalyRecord.task_id == task_id)

    count_q = select(func.count()).select_from(base.subquery())
    result = await db.execute(count_q)
    total = result.scalar()

    result = await db.execute(
        base.order_by(AnomalyRecord.id.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    data = [
        {"id": r.id, "task_id": r.task_id, "lon": r.lon, "lat": r.lat, "depth": r.depth,
         "indicator": r.indicator, "value": r.value, "method": r.method}
        for r in result.scalars().all()
    ]
    return success(datas={"total": total, "items": data})


@anomaly_router.get("/api/task/{task_id}/anomalies", summary="异常点列表")
async def get_anomalies(
    task_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)

    result = await db.execute(
        select(func.count()).select_from(AnomalyRecord).where(AnomalyRecord.task_id == task_id)
    )
    total = result.scalar()

    result = await db.execute(
        select(AnomalyRecord).where(AnomalyRecord.task_id == task_id)
        .offset((page - 1) * page_size).limit(page_size)
    )
    data = [
        {"id": r.id, "lon": r.lon, "lat": r.lat, "depth": r.depth,
         "indicator": r.indicator, "value": r.value, "method": r.method}
        for r in result.scalars().all()
    ]
    return success(datas={"total": total, "items": data})


@anomaly_router.get("/api/task/{task_id}/anomalies/export", summary="导出异常CSV")
async def export_anomalies(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)

    result = await db.execute(
        select(AnomalyRecord).where(AnomalyRecord.task_id == task_id)
    )
    rows = result.scalars().all()

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["lon", "lat", "depth", "indicator", "value", "method"])
    w.writeheader()
    w.writerows([
        {"lon": r.lon, "lat": r.lat, "depth": r.depth,
         "indicator": r.indicator, "value": r.value, "method": r.method}
        for r in rows
    ])
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={task_id}_anomalies.csv"},
    )
