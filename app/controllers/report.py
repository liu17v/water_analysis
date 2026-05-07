"""智能报告控制器"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

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
report_router = APIRouter()


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

    if path and path.endswith(".pdf"):
        task.report_path = path
        await db.commit()

    return success(datas=ReportOut(report_url=f"/reports/{task_id}.pdf" if path else "").model_dump())
