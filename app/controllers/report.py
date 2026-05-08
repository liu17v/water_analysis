"""智能报告控制器"""
import os
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config.database import get_db
from app.config.response import success, BusinessException
from app.schemas.report import SimilarTaskOut, ReportOut
from app.models.task import Task, TaskStatus
from app.models.anomaly import AnomalyRecord
from app.services.data_service import DataService
from app.services.feature_extractor import extract_features, normalize
from app.services.milvus_service import connect, search as milvus_search
from app.services.report_generator import generate
from app.utils.log_config import get_logger

logger = get_logger("controllers.report")
report_router = APIRouter(tags=["智能报告"])


@report_router.get("/api/reports", summary="报告列表（跨任务）")
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(func.count()).select_from(Task).where(Task.report_path.isnot(None))
    )
    total = result.scalar()

    result = await db.execute(
        select(Task).where(Task.report_path.isnot(None))
        .order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    items = [
        {"task_id": t.id, "reservoir_name": t.reservoir_name or "",
         "report_path": t.report_path or "", "total_points": t.total_points,
         "anomaly_count": t.anomaly_count, "created_at": str(t.created_at or "")}
        for t in result.scalars().all()
    ]
    return success(datas={"total": total, "items": items})


@report_router.delete("/api/report/{task_id}", summary="删除报告")
async def delete_report(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)
    import os
    if task.report_path and os.path.exists(task.report_path):
        os.remove(task.report_path)
    task.report_path = None
    await db.commit()
    logger.info(f"报告已删除 | task_id={task_id}")
    return success(messages="报告已删除")


@report_router.get("/api/task/{task_id}/report_status", summary="获取报告状态")
async def report_status(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)
    has_report = bool(task.report_path)
    return success(datas={"has_report": has_report, "report_path": task.report_path or ""})


@report_router.post("/api/task/{task_id}/similar", summary="检索相似案例")
async def search_similar(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)

    rows = await DataService.get_raw_data(db, task_id)
    feats = extract_features(rows)
    norm_feats = normalize(feats)

    similar = []
    try:
        connect()
        results = milvus_search(norm_feats, top_k=5)
        for r in results:
            if r["task_id"] == task_id:
                continue
            result = await db.execute(select(Task).where(Task.id == r["task_id"]))
            t = result.scalar_one_or_none()
            if t:
                similar.append(SimilarTaskOut(
                    task_id=r["task_id"],
                    similarity=round(1.0 / (1.0 + r["distance"]), 4),
                    reservoir=t.reservoir_name or "未知",
                    date=str(t.created_at or ""),
                    report_url=t.report_path or "",
                ).model_dump())
    except Exception as e:
        logger.warning(f"Milvus检索失败: {e}")

    return success(datas={"similar_tasks": similar})


@report_router.post("/api/task/{task_id}/generate_report", summary="生成分析报告")
async def generate_report(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)
    if task.status != TaskStatus.success:
        raise BusinessException(msg="任务尚未完成分析", code=400)

    rows = await DataService.get_raw_data(db, task_id)
    result = await db.execute(
        select(AnomalyRecord).where(AnomalyRecord.task_id == task_id).limit(20)
    )
    anomalies = [
        {"lon": r.lon, "lat": r.lat, "depth": r.depth,
         "indicator": r.indicator, "value": r.value, "method": r.method}
        for r in result.scalars().all()
    ]

    similar = []
    try:
        feats = extract_features(rows)
        connect()
        results = milvus_search(normalize(feats), top_k=3)
        for r in results:
            if r["task_id"] != task_id:
                similar.append({"reservoir": r.get("reservoir_name", "未知"),
                                "similarity": round(1.0 / (1.0 + r["distance"]), 4)})
    except Exception:
        pass

    depths = sorted(set(r.depth_m for r in rows))
    task_info = {
        "id": task_id,
        "reservoir_name": task.reservoir_name or "",
        "created_at": str(task.created_at or ""),
        "total_points": task.total_points,
        "depth_layers": ", ".join(f"{d}m" for d in depths),
    }

    path = generate(task_info, rows, anomalies, similar)

    if path:
        task.report_path = path
        await db.commit()
        ext = os.path.splitext(path)[1]
        return success(datas=ReportOut(report_url=f"/reports/{task_id}{ext}").model_dump())

    return success(datas=ReportOut(report_url="").model_dump())
