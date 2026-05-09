"""智能报告控制器 — 纯 DB 生命周期，Milvus 熔断快速失败"""
import asyncio
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config.database import get_db, AsyncSessionMaker
from app.config.response import success, BusinessException
from app.schemas.report import SimilarTaskOut
from app.models.task import Task, TaskStatus
from app.models.anomaly import AnomalyRecord
from app.services.data_service import DataService
from app.services.feature_extractor import extract_features, normalize
from app.services.milvus_service import connect as milvus_connect, search as milvus_search
from app.config.settings import get_settings
from app.services.report_generator import generate as generate_docx

settings = get_settings()
from app.config.logging import get_logger

logger = get_logger("routers.report")
report_router = APIRouter(tags=["智能报告"])

# 独立线程池（Milvus 专用），与 FastAPI 默认池隔离，防止互相影响
_MILVUS_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="milvus_")
_MILVUS_TIMEOUT = 6

# 轻量内存缓存：仅缓存线程池回调的实时百分比，DB 管控生命周期
_gen_live_pct: dict = {}  # task_id -> int (0-100)
_gen_live_lock = threading.Lock()
_background_tasks: set = set()


def _url_from_path(fs_path: str, task_id: str) -> str:
    if not fs_path:
        return ""
    return f"/reports/{task_id}.docx"


def _call_milvus(func, *args, timeout: float = _MILVUS_TIMEOUT):
    """在独立线程池中调用 Milvus 函数，带超时保护。失败抛出异常由调用方处理。"""
    future = _MILVUS_EXECUTOR.submit(func, *args)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError:
        future.cancel()
        raise TimeoutError(f"Milvus 调用超时 ({timeout}s): {func.__name__}")
    except Exception:
        future.cancel()
        raise


# ═══════════════════════════════════════════════════════════════
# 报告列表 / 删除
# ═══════════════════════════════════════════════════════════════

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
         "report_path": _url_from_path(t.report_path or "", t.id),
         "total_points": t.total_points,
         "anomaly_count": t.anomaly_count, "created_at": str(t.created_at or "")}
        for t in result.scalars().all()
    ]
    return success(datas={"total": total, "items": items})


@report_router.delete("/api/report/{task_id}", summary="删除报告")
async def delete_report(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)

    if task.report_path and os.path.exists(task.report_path):
        os.remove(task.report_path)
    pdf_path = os.path.join(settings.REPORT_DIR, f"{task_id}.pdf")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    task.report_path = None
    await db.commit()
    logger.info(f"报告已删除 | task_id={task_id}")
    return success(messages="报告已删除")


# ═══════════════════════════════════════════════════════════════
# 报告状态（纯 DB，不依赖内存）
# ═══════════════════════════════════════════════════════════════

@report_router.get("/api/task/{task_id}/report_status", summary="获取报告状态")
async def report_status(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)

    has_report = bool(task.report_path)
    generating = task.report_phase is not None

    # 检测服务器重启导致的中断：DB 标记为生成中但进度为 0 且无报告文件
    if generating and task.progress == 0 and not has_report:
        task.report_phase = None
        task.progress = 100
        await db.commit()
        return success(datas={
            "has_report": False,
            "generating": False,
            "progress": -1,
            "phase": "服务器重启导致生成中断，请点击按钮重新生成",
            "report_path": "",
            "doc_url": f"/reports/{task_id}.docx",
            "pdf_url": f"/reports/{task_id}.pdf",
        })

    with _gen_live_lock:
        live_pct = _gen_live_pct.get(task_id, 0)

    if generating:
        return success(datas={
            "has_report": has_report,
            "generating": True,
            "progress": live_pct,
            "phase": task.report_phase or "",
            "report_path": _url_from_path(task.report_path or "", task_id),
            "doc_url": f"/reports/{task_id}.docx",
            "pdf_url": f"/reports/{task_id}.pdf",
        })

    return success(datas={
        "has_report": has_report,
        "generating": False,
        "progress": 0,
        "phase": "",
        "report_path": _url_from_path(task.report_path or "", task_id),
        "doc_url": f"/reports/{task_id}.docx",
        "pdf_url": f"/reports/{task_id}.pdf",
    })


# ═══════════════════════════════════════════════════════════════
# 相似案例检索（独立线程池 + 快速失败）
# ═══════════════════════════════════════════════════════════════

@report_router.post("/api/task/{task_id}/similar", summary="检索相似案例")
async def search_similar(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)

    rows = await DataService.get_raw_data(db, task_id)
    t0 = time.time()

    # 特征提取（纯计算，直接在默认 executor 执行）
    loop = asyncio.get_running_loop()
    feats = await loop.run_in_executor(None, extract_features, rows)
    norm_feats = await loop.run_in_executor(None, normalize, feats)
    logger.info(f"特征提取完成 | task_id={task_id} | elapsed={time.time()-t0:.2f}s")

    # Milvus 检索（独立线程池，熔断器保护，最多 10s）
    similar = []
    try:
        _call_milvus(milvus_connect, timeout=_MILVUS_TIMEOUT)
        results = _call_milvus(milvus_search, norm_feats, 5, timeout=_MILVUS_TIMEOUT)
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
                    report_url=_url_from_path(t.report_path or "", r["task_id"]),
                ).model_dump())
        logger.info(f"相似案例检索完成 | task_id={task_id} | similar={len(similar)} | elapsed={time.time()-t0:.2f}s")
    except Exception as e:
        logger.warning(f"Milvus检索失败（{time.time()-t0:.1f}s）| task_id={task_id} | {type(e).__name__}: {e}")

    return success(datas={"similar_tasks": similar})


# ═══════════════════════════════════════════════════════════════
# 后台报告生成
# ═══════════════════════════════════════════════════════════════

async def _run_report_generation(task_id: str):
    """后台报告生成：DB 管控生命周期，独立线程池跑 Milvus，默认池跑文档生成。"""
    t_start = time.time()
    logger.info(f"报告生成: 开始 | task_id={task_id}")

    async with AsyncSessionMaker() as db:
        try:
            task = await DataService.get_task(db, task_id)
            if not task:
                return

            # 阶段 1: 准备
            task.report_phase = "正在准备..."
            task.progress = 0
            await db.commit()

            task.report_phase = "正在加载数据..."
            await db.commit()
            rows = await DataService.get_raw_data(db, task_id)
            if not rows:
                task.report_phase = None
                task.progress = 100
                await db.commit()
                return
            logger.info(f"报告生成: 数据已加载 | task_id={task_id} | rows={len(rows)}")

            # 阶段 2: 异常记录
            task.report_phase = "正在加载异常记录..."
            await db.commit()
            result = await db.execute(
                select(AnomalyRecord).where(AnomalyRecord.task_id == task_id)
            )
            anomalies = [
                {"lon": r.lon, "lat": r.lat, "depth": r.depth,
                 "indicator": r.indicator, "value": r.value, "method": r.method}
                for r in result.scalars().all()
            ]

            # 阶段 3: 相似案例（独立线程池，快速失败）
            similar = []
            task.report_phase = "正在检索相似案例..."
            await db.commit()
            try:
                loop = asyncio.get_running_loop()
                feats = await asyncio.wait_for(
                    loop.run_in_executor(None, extract_features, rows), timeout=30)
                norm_feats = await asyncio.wait_for(
                    loop.run_in_executor(None, normalize, feats), timeout=5)
                _call_milvus(milvus_connect, timeout=8)
                results = _call_milvus(milvus_search, norm_feats, 3, timeout=15)
                for r in results:
                    if r["task_id"] != task_id:
                        similar.append({
                            "reservoir": r.get("reservoir_name", "未知"),
                            "similarity": round(1.0 / (1.0 + r["distance"]), 4),
                        })
            except Exception:
                logger.warning(f"报告生成: 相似案例检索跳过 | task_id={task_id}")
            logger.info(f"报告生成: 相似案例检索完成 | task_id={task_id} | similar={len(similar)}")

            # 阶段 4: 生成文档
            depths = sorted(set(r.depth_m for r in rows))
            task_info = {
                "id": task_id,
                "reservoir_name": task.reservoir_name or "",
                "created_at": str(task.created_at or ""),
                "total_points": task.total_points,
                "depth_layers": ", ".join(f"{d}m" for d in depths),
            }

            loop = asyncio.get_running_loop()

            def on_progress(pct: int, _phase: str):
                with _gen_live_lock:
                    _gen_live_pct[task_id] = pct

            task.report_phase = "正在生成文档..."
            await db.commit()
            try:
                gen_result = await loop.run_in_executor(
                    None, generate_docx, task_info, rows, anomalies, similar, on_progress
                )
            except Exception as e:
                logger.error(f"报告生成: 文档生成失败 | task_id={task_id} | {type(e).__name__}: {e}")
                task.report_phase = None
                task.progress = 100
                await db.commit()
                with _gen_live_lock:
                    _gen_live_pct.pop(task_id, None)
                return

            docx_path = gen_result.get("docx_path") if isinstance(gen_result, dict) else gen_result
            if not docx_path:
                task.report_phase = None
                task.progress = 100
                await db.commit()
                with _gen_live_lock:
                    _gen_live_pct.pop(task_id, None)
                return

            # 完成
            task.report_path = docx_path
            task.report_phase = None
            task.progress = 100
            await db.commit()
            with _gen_live_lock:
                _gen_live_pct.pop(task_id, None)

            # PDF 后台异步生成
            from app.services.report_generator import convert_pdf
            asyncio.get_running_loop().run_in_executor(None, convert_pdf, docx_path, task_id)

            logger.info(f"报告生成: 完成 | task_id={task_id} | path={docx_path} | elapsed={time.time()-t_start:.1f}s")

        except asyncio.CancelledError:
            logger.warning(f"报告生成: 被取消 | task_id={task_id}")
            try:
                task = await DataService.get_task(db, task_id)
                if task:
                    task.report_phase = None
                    task.progress = 100
                    await db.commit()
            except Exception:
                pass
            with _gen_live_lock:
                _gen_live_pct.pop(task_id, None)
        except Exception as e:
            logger.error(f"报告生成: 异常 | task_id={task_id} | {type(e).__name__}: {e}")
            try:
                task = await DataService.get_task(db, task_id)
                if task:
                    task.report_phase = None
                    task.progress = 100
                    await db.commit()
            except Exception:
                pass
            with _gen_live_lock:
                _gen_live_pct.pop(task_id, None)


# ═══════════════════════════════════════════════════════════════
# 触发报告生成
# ═══════════════════════════════════════════════════════════════

@report_router.post("/api/task/{task_id}/generate_report", summary="生成分析报告")
async def generate_report(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)
    if task.status != TaskStatus.success:
        raise BusinessException(msg="任务尚未完成分析", code=400)
    if task.report_phase is not None:
        raise BusinessException(msg="报告正在生成中，请稍后查看状态", code=400)

    bg_task = asyncio.create_task(_run_report_generation(task_id))
    _background_tasks.add(bg_task)
    bg_task.add_done_callback(_background_tasks.discard)
    logger.info(f"报告生成已启动（后台） | task_id={task_id}")
    return success(messages="报告生成已启动", datas={"status": "started"})
