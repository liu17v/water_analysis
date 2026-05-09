"""Celery 异步任务 + 本地降级：处理 CSV 完整分析流水线"""
import os
import asyncio
import threading
from datetime import datetime
from celery import Celery
from app.config.settings import get_settings
from app.config.database import AsyncSessionMaker
from app.services.data_service import DataService
from app.services.interpolation import interpolate_all_layers
from app.services.anomaly_detector import run_anomaly_detection
from app.services.feature_extractor import extract_features, normalize
from app.services.visualization import generate_3d_html
from app.services.milvus_service import connect, insert
from app.models.task import TaskStatus
from app.models.anomaly import AnomalyRecord
from app.config.logging import get_logger

logger = get_logger("services.celery")
settings = get_settings()

celery_app = Celery(
    "water_analysis",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    task_serializer="json", accept_content=["json"],
    timezone="Asia/Shanghai", enable_utc=True,
    task_track_started=True,
)


async def _run_pipeline_async(task_id: str):
    """核心流水线（单事件循环版本，避免 Windows asyncio.run() 重复调用问题）"""
    logger.info(f"开始处理任务 | task_id={task_id}")

    async with AsyncSessionMaker() as db:
        await DataService.update_task_status(db, task_id, TaskStatus.processing, 5)

        rows = await DataService.get_raw_data(db, task_id)
        if not rows:
            await DataService.update_task_status(db, task_id, TaskStatus.failed, 0)
            return {"error": "无数据"}

        # Anomaly detection (clear existing first to avoid duplicates on re-run)
        await DataService.update_task_status(db, task_id, TaskStatus.processing, 25)
        from sqlalchemy import delete as sa_delete
        await db.execute(sa_delete(AnomalyRecord).where(AnomalyRecord.task_id == task_id))
        anomalies = run_anomaly_detection(rows)
        for a in anomalies:
            db.add(AnomalyRecord(
                task_id=task_id, lon=a["lon"], lat=a["lat"],
                depth=a["depth"], indicator=a["indicator"],
                value=a["value"], method=a["method"],
                threshold_low=a.get("threshold_low"),
                threshold_high=a.get("threshold_high"),
            ))
        await db.commit()

        await DataService.update_task_status(db, task_id, TaskStatus.processing, 45,
                                              anomaly_count=len(anomalies))

        task = await DataService.get_task(db, task_id)

    # 3D visualization (CPU-bound, run in thread)
    loop = asyncio.get_running_loop()
    await DataService.update_task_status_nothrow(task_id, TaskStatus.processing, 60)
    anomaly_points = [{"lon": a["lon"], "lat": a["lat"], "depth": a["depth"],
                       "indicator": a["indicator"], "value": a["value"]} for a in anomalies]
    for ind in ["chlorophyll", "dissolved_oxygen", "temperature", "ph", "turbidity"]:
        html = await loop.run_in_executor(None, generate_3d_html, rows, ind, anomaly_points)
        os.makedirs(settings.THREED_DIR, exist_ok=True)
        with open(os.path.join(settings.THREED_DIR, f"{task_id}_{ind}.html"), "w", encoding="utf-8") as f:
            f.write(html)

    # Feature extraction + Milvus
    await DataService.update_task_status_nothrow(task_id, TaskStatus.processing, 80)
    try:
        feats = await loop.run_in_executor(None, extract_features, rows)
        norm_feats = await loop.run_in_executor(None, normalize, feats)
        connect()
        insert(task_id, norm_feats, int(datetime.utcnow().timestamp()),
               task.reservoir_name if task else "")
    except Exception as e:
        logger.warning(f"Milvus 入库失败: {e}")

    await DataService.update_task_status_nothrow(task_id, TaskStatus.success, 100)
    logger.info(f"任务处理完成 | task_id={task_id} | anomalies={len(anomalies)}")
    return {"status": "success", "anomaly_count": len(anomalies)}


def _run_pipeline(task_id: str):
    """核心流水线同步入口"""
    return asyncio.run(_run_pipeline_async(task_id))


@celery_app.task(bind=True, name="process_csv")
def process_csv(self, task_id: str):
    try:
        return _run_pipeline(task_id)
    except Exception as e:
        logger.error(f"任务处理失败 | task_id={task_id} | {e}", exc_info=True)
        _sync_update(task_id, TaskStatus.failed, 0)
        return {"error": str(e)}


async def run_task_local(task_id: str):
    """本地异步处理流水线（直接在当前 event loop 中运行）"""
    await _run_pipeline_async(task_id)
