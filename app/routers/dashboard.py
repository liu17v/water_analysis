"""仪表盘聚合统计控制器"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.config.database import get_db
from app.config.response import success
from app.models.task import Task, TaskStatus as TS
from app.models.anomaly import AnomalyRecord

dashboard_router = APIRouter(tags=["仪表盘"])

INDICATOR_SHORT = ["chl", "odo", "temp", "ph", "turb"]
INDICATOR_LABEL = {"chl": "叶绿素", "odo": "溶解氧", "temp": "水温", "ph": "pH", "turb": "浊度"}


@dashboard_router.get("/api/dashboard/stats", summary="仪表盘聚合统计")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    # Total tasks
    result = await db.execute(select(func.count()).select_from(Task))
    total_tasks = result.scalar() or 0

    # Tasks by status
    result = await db.execute(
        select(Task.status, func.count()).group_by(Task.status)
    )
    status_map = {s: c for s, c in result.all()}
    status_counts = {
        "success": status_map.get(TS.success, 0),
        "processing": status_map.get(TS.processing, 0),
        "pending": status_map.get(TS.pending, 0),
        "failed": status_map.get(TS.failed, 0),
    }

    # Total anomalies
    result = await db.execute(select(func.count()).select_from(AnomalyRecord))
    total_anomalies = result.scalar() or 0

    # Anomalies by indicator
    result = await db.execute(
        select(AnomalyRecord.indicator, func.count()).group_by(AnomalyRecord.indicator)
    )
    anomaly_by_indicator = {ind: cnt for ind, cnt in result.all()}

    # Tasks by day (last 14 days)
    fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
    result = await db.execute(
        select(func.date(Task.created_at), func.count())
        .where(Task.created_at >= fourteen_days_ago)
        .group_by(func.date(Task.created_at))
        .order_by(func.date(Task.created_at))
    )
    task_trend = [{"date": str(d), "count": c} for d, c in result.all()]

    # Success rate
    success_rate = round(status_counts["success"] / total_tasks * 100, 1) if total_tasks else 0

    # Recent anomalies (last 5)
    result = await db.execute(
        select(AnomalyRecord).order_by(AnomalyRecord.id.desc()).limit(5)
    )
    recent_anomalies = [
        {"task_id": r.task_id, "indicator": r.indicator, "value": round(r.value, 2),
         "depth": r.depth, "method": r.method}
        for r in result.scalars().all()
    ]

    return success(datas={
        "total_tasks": total_tasks,
        "status_counts": status_counts,
        "total_anomalies": total_anomalies,
        "anomaly_by_indicator": {
            INDICATOR_LABEL.get(k, k): anomaly_by_indicator.get(k, 0)
            for k in INDICATOR_SHORT
        },
        "task_trend": task_trend,
        "success_rate": success_rate,
        "recent_anomalies": recent_anomalies,
    })
