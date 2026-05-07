"""任务管理控制器"""
import math
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.config.database import get_db
from app.config.response import success, BusinessException
from app.schemas.task import TaskStatusOut, TaskListItem, VisualizationOut
from app.models.task import Task, TaskStatus as TS
from app.models.raw_data import RawData
from app.models.anomaly import AnomalyRecord
from app.services.data_service import DataService
from app.services.interpolation import interpolate_all_layers
from app.services.visualization import contour_html, INDICATOR_LABELS
from app.services.milvus_service import delete as milvus_delete
from app.utils.log_config import get_logger

logger = get_logger("controllers.task")
task_router = APIRouter()


@task_router.get("/api/task/{task_id}/status", summary="获取任务状态")
async def task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)
    return success(datas=TaskStatusOut(
        task_id=task.id, status=task.status, progress=task.progress,
        total_points=task.total_points, anomaly_count=task.anomaly_count,
    ).model_dump())


@task_router.get("/api/tasks", summary="任务列表")
async def task_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(func.count()).select_from(Task))
    total = result.scalar()
    result = await db.execute(
        select(Task).order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    tasks = result.scalars().all()
    data = [
        TaskListItem(
            task_id=t.id, reservoir_name=t.reservoir_name or "",
            original_filename=t.original_filename or "", status=t.status,
            total_points=t.total_points, anomaly_count=t.anomaly_count,
            created_at=str(t.created_at or ""),
        ).model_dump()
        for t in tasks
    ]
    return success(datas={"total": total, "items": data})


@task_router.get("/api/task/{task_id}/visualization", summary="获取可视化数据")
async def get_visualization(
    task_id: str,
    indicator: str = Query("chlorophyll"),
    depth: float = Query(None),
    db: AsyncSession = Depends(get_db),
):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)
    if task.status != TS.success:
        raise BusinessException(msg="任务尚未完成分析", code=400)

    rows = await DataService.get_raw_data(db, task_id)
    if not rows:
        raise BusinessException(msg="无数据", code=404)

    if indicator not in INDICATOR_LABELS:
        raise BusinessException(msg=f"不支持的指标: {indicator}", code=400)

    grids = interpolate_all_layers(rows, indicator)
    depths = sorted(grids.keys())
    d = depth if depth is not None else (depths[0] if depths else 0)
    grid = grids.get(d)
    if not grid:
        raise BusinessException(msg=f"深度 {d}m 无插值数据", code=404)

    result = await db.execute(
        select(AnomalyRecord.lon, AnomalyRecord.lat, AnomalyRecord.depth,
               AnomalyRecord.indicator, AnomalyRecord.value)
        .where(AnomalyRecord.task_id == task_id)
    )
    anomaly_points = [
        {"lon": r.lon, "lat": r.lat, "depth": r.depth, "indicator": r.indicator, "value": r.value}
        for r in result.fetchall()
    ]

    html = contour_html(grid, indicator, d, anomaly_points)
    return success(datas=VisualizationOut(
        contour_html=html, grid=grid,
        contour_url=f"/api/task/{task_id}/contour_html?indicator={indicator}&depth={d}",
        volume_3d_url=f"/3d/{task_id}_{indicator}.html",
        depths=list(depths),
    ).model_dump())


@task_router.get("/api/task/{task_id}/contour_html", summary="获取等值线图HTML")
async def get_contour_html(
    task_id: str,
    indicator: str = Query("chlorophyll"),
    depth: float = Query(1.0),
    db: AsyncSession = Depends(get_db),
):
    """返回完整独立HTML，供iframe加载（含Plotly.js CDN）"""
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)

    if indicator not in INDICATOR_LABELS:
        raise BusinessException(msg=f"不支持的指标: {indicator}", code=400)

    rows = await DataService.get_raw_data(db, task_id)
    if not rows:
        raise BusinessException(msg="无数据", code=404)

    grids = interpolate_all_layers(rows, indicator)
    depths = sorted(grids.keys())
    d = depth if depth in depths else (depths[0] if depths else 0)
    grid = grids.get(d)
    if not grid:
        raise BusinessException(msg=f"深度 {d}m 无插值数据", code=404)

    result = await db.execute(
        select(AnomalyRecord.lon, AnomalyRecord.lat, AnomalyRecord.depth,
               AnomalyRecord.indicator, AnomalyRecord.value)
        .where(AnomalyRecord.task_id == task_id)
    )
    anomaly_points = [
        {"lon": r.lon, "lat": r.lat, "depth": r.depth, "indicator": r.indicator, "value": r.value}
        for r in result.fetchall()
    ]

    from app.services.visualization import contour_html as gen_contour
    html = gen_contour(grid, indicator, d, anomaly_points)
    return HTMLResponse(content=html, status_code=200)


INDICATOR_COLS = ["chlorophyll", "dissolved_oxygen", "temperature", "ph", "turbidity"]


@task_router.get("/api/task/{task_id}/statistics", summary="获取指标统计")
async def get_statistics(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)

    rows = await DataService.get_raw_data(db, task_id)
    if not rows:
        raise BusinessException(msg="无数据", code=404)

    result = await db.execute(
        select(func.count()).select_from(AnomalyRecord).where(AnomalyRecord.task_id == task_id)
    )
    total_anomalies = result.scalar() or 0

    total = len(rows)
    stats = {}
    for col in INDICATOR_COLS:
        vals = [getattr(r, col) for r in rows if getattr(r, col) is not None]
        if not vals:
            stats[col] = {"mean": None, "std": None, "min": None, "max": None,
                          "count": 0, "anomaly_count": 0, "anomaly_rate": 0}
            continue
        n = len(vals)
        avg = sum(vals) / n
        variance = sum((v - avg) ** 2 for v in vals) / n
        label, unit = INDICATOR_LABELS.get(col, (col, ""))

        col_anomaly_count = await db.execute(
            select(func.count()).select_from(AnomalyRecord).where(
                AnomalyRecord.task_id == task_id, AnomalyRecord.indicator == col
            )
        )
        ac = col_anomaly_count.scalar() or 0

        stats[col] = {
            "indicator": col, "label": label, "unit": unit,
            "mean": round(avg, 4), "std": round(math.sqrt(variance), 4),
            "min": round(min(vals), 4), "max": round(max(vals), 4),
            "count": n, "anomaly_count": ac,
            "anomaly_rate": round(ac / total * 100, 1) if total else 0,
        }

    return success(datas={"indicators": stats, "total_points": total,
                          "total_anomalies": total_anomalies})


@task_router.get("/api/task/{task_id}/depth_profile", summary="获取深度剖面数据")
async def get_depth_profile(
    task_id: str,
    indicator: str = Query("chlorophyll"),
    db: AsyncSession = Depends(get_db),
):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)

    if indicator not in INDICATOR_LABELS:
        raise BusinessException(msg=f"不支持的指标: {indicator}", code=400)

    rows = await DataService.get_raw_data(db, task_id)
    if not rows:
        raise BusinessException(msg="无数据", code=404)

    depth_map = {}
    for r in rows:
        d = r.depth_m
        val = getattr(r, indicator, None)
        if d is not None and val is not None:
            depth_map.setdefault(d, []).append(val)

    profile = []
    for d in sorted(depth_map.keys()):
        vals = depth_map[d]
        profile.append({
            "depth": d,
            "count": len(vals),
            "mean": round(sum(vals) / len(vals), 4),
            "min": round(min(vals), 4),
            "max": round(max(vals), 4),
            "std": round(math.sqrt(sum((v - sum(vals) / len(vals)) ** 2 for v in vals) / len(vals)), 4),
        })

    label, unit = INDICATOR_LABELS.get(indicator, (indicator, ""))
    return success(datas={"indicator": indicator, "label": label, "unit": unit,
                          "profile": profile, "depths": sorted(depth_map.keys())})


@task_router.get("/api/task/{task_id}/depth_profile_html", summary="获取深度剖面图HTML")
async def get_depth_profile_html(
    task_id: str,
    indicator: str = Query("chlorophyll"),
    db: AsyncSession = Depends(get_db),
):
    """返回完整独立HTML（Plotly线图），供iframe加载"""
    from plotly import graph_objects as go

    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)
    if indicator not in INDICATOR_LABELS:
        raise BusinessException(msg=f"不支持的指标: {indicator}", code=400)

    rows = await DataService.get_raw_data(db, task_id)
    if not rows:
        raise BusinessException(msg="无数据", code=404)

    # Group by depth
    depth_map = {}
    for r in rows:
        d = r.depth_m
        val = getattr(r, indicator, None)
        if d is not None and val is not None:
            depth_map.setdefault(d, []).append(val)

    depths = sorted(depth_map.keys())
    means = [sum(depth_map[d]) / len(depth_map[d]) for d in depths]
    mins = [min(depth_map[d]) for d in depths]
    maxs = [max(depth_map[d]) for d in depths]

    label, unit = INDICATOR_LABELS.get(indicator, (indicator, ""))
    title = f"{label} 深度剖面" + (f" ({unit})" if unit else "")

    fig = go.Figure()
    # Range band
    fig.add_trace(go.Scatter(
        x=mins + maxs[::-1], y=depths + depths[::-1],
        fill="toself", fillcolor="rgba(64,158,255,0.15)", line=dict(width=0),
        name="范围", showlegend=True,
    ))
    # Mean line
    fig.add_trace(go.Scatter(
        x=means, y=depths, mode="lines+markers",
        line=dict(color="#409eff", width=3), marker=dict(size=8, color="#409eff"),
        name="均值", showlegend=True,
        hovertemplate=f"{label}=%{{x:.2f}} {unit}<br>深度=%{{y}}m<extra></extra>",
    ))
    fig.update_layout(
        title=title, xaxis_title=f"{label}" + (f" ({unit})" if unit else ""),
        yaxis_title="深度 (m)", yaxis=dict(autorange="reversed"),
        height=500, margin=dict(l=60, r=30, t=50, b=50), hovermode="x unified",
    )
    return HTMLResponse(content=fig.to_html(full_html=True, include_plotlyjs="cdn"))
async def get_raw_data_preview(
    task_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)

    result = await db.execute(
        select(func.count()).select_from(RawData).where(RawData.task_id == task_id)
    )
    total = result.scalar()

    result = await db.execute(
        select(RawData).where(RawData.task_id == task_id)
        .offset((page - 1) * page_size).limit(page_size)
    )
    rows = result.scalars().all()

    fields = ["lon", "lat", "depth_m", "temperature", "conductivity",
              "salinity", "ph", "turbidity", "chlorophyll", "dissolved_oxygen"]
    field_labels = ["经度", "纬度", "深度(m)", "温度(°C)", "电导率(µS/cm)",
                    "盐度(‰)", "pH", "浊度(NTU)", "叶绿素(µg/L)", "溶解氧(mg/L)"]

    data = []
    for r in rows:
        item = {}
        for f in fields:
            val = getattr(r, f, None)
            item[f] = round(val, 4) if val is not None else None
        item["suspicious"] = r.suspicious
        data.append(item)

    return success(datas={"total": total, "fields": fields, "field_labels": field_labels,
                          "items": data, "page": page, "page_size": page_size})


@task_router.delete("/api/task/{task_id}", summary="删除任务")
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await DataService.get_task(db, task_id)
    if not task:
        raise BusinessException(msg="任务不存在", code=404)

    await db.execute(text("DELETE FROM raw_data WHERE task_id = :id"), {"id": task_id})
    await db.execute(text("DELETE FROM anomalies WHERE task_id = :id"), {"id": task_id})
    await db.delete(task)
    await db.commit()

    try:
        milvus_delete(task_id)
    except Exception:
        pass

    logger.info(f"任务已删除 | task_id={task_id}")
    return success(messages="删除成功")
