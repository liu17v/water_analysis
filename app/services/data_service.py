"""CSV 解析、校验、数据入库"""
import csv
import io
import uuid
import os
from datetime import datetime
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import AsyncSessionMaker
from app.config.settings import get_settings
from app.config.response import BusinessException
from app.models.task import Task, TaskStatus
from app.models.raw_data import RawData
from app.utils.log_config import get_logger

logger = get_logger("services.data")
settings = get_settings()

ENCODINGS = ["utf-8", "gbk", "gb2312", "iso-8859-1", "latin1"]

FIELD_ALIASES = {
    "lon": "lon", "lat": "lat", "depth_m": "depth_m",
    "temp": "temperature", "temperature": "temperature", "temp c": "temperature",
    "cond": "conductivity", "conductivity": "conductivity", "cond (us/cm)": "conductivity",
    "salt": "salinity", "salinity": "salinity",
    "ph": "ph",
    "turb": "turbidity", "turbidity": "turbidity", "turb ntu": "turbidity",
    "chl": "chlorophyll", "chlorophyll": "chlorophyll", "chl(ug/l)": "chlorophyll",
    "odo": "dissolved_oxygen", "dissolved_oxygen": "dissolved_oxygen", "odo(mg/l)": "dissolved_oxygen",
}

TARGET_FIELDS = {"lon", "lat", "depth_m", "temperature", "conductivity", "salinity", "ph", "turbidity", "chlorophyll", "dissolved_oxygen"}


class DataService:
    @staticmethod
    def detect_encoding(content: bytes) -> str:
        for enc in ENCODINGS:
            try:
                content.decode(enc)
                return enc
            except (UnicodeDecodeError, LookupError):
                continue
        return "latin1"

    @staticmethod
    def normalize_header(raw: str) -> str:
        cleaned = raw.strip().lower().replace("﻿", "")
        for alias, target in FIELD_ALIASES.items():
            if alias in cleaned:
                return target
        return cleaned

    @staticmethod
    def parse_csv(content: bytes) -> list[dict]:
        encoding = DataService.detect_encoding(content)
        text = content.decode(encoding, errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        col_map = {h: DataService.normalize_header(h) for h in (reader.fieldnames or [])}
        col_map = {k: v for k, v in col_map.items() if v in TARGET_FIELDS}

        rows = []
        for row in reader:
            mapped = {}
            for raw_key, target in col_map.items():
                val = row.get(raw_key, "").strip()
                try:
                    mapped[target] = float(val) if val else None
                except ValueError:
                    mapped[target] = None
            if "lon" in mapped and "lat" in mapped and "depth_m" in mapped:
                mapped["_suspicious"] = DataService._validate(mapped)
                rows.append(mapped)
        return rows

    @staticmethod
    def _validate(row: dict) -> int:
        lon, lat, depth = row.get("lon"), row.get("lat"), row.get("depth_m")
        if lon and (lon < settings.LON_MIN or lon > settings.LON_MAX):
            return 1
        if lat and (lat < settings.LAT_MIN or lat > settings.LAT_MAX):
            return 1
        if depth and (depth < settings.DEPTH_MIN or depth > settings.DEPTH_MAX):
            return 1
        checks = [
            ("chlorophyll", settings.CHL_MIN, settings.CHL_MAX),
            ("dissolved_oxygen", settings.ODO_MIN, settings.ODO_MAX),
            ("ph", settings.PH_MIN, settings.PH_MAX),
            ("turbidity", settings.TURB_MIN, settings.TURB_MAX),
            ("temperature", settings.TEMP_MIN, settings.TEMP_MAX),
        ]
        for field, lo, hi in checks:
            val = row.get(field)
            if val is not None and (val < lo or val > hi):
                return 1
        return 0

    @staticmethod
    async def create_task(db: AsyncSession, filename: str, file_path: str,
                          total_points: int, reservoir_name: str = "", user_id: int = None) -> str:
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id, user_id=user_id, reservoir_name=reservoir_name,
            original_filename=filename, file_path=file_path,
            total_points=total_points, status=TaskStatus.pending,
        )
        db.add(task)
        await db.commit()
        logger.info(f"任务创建 | task_id={task_id} | rows={total_points}")
        return task_id

    @staticmethod
    async def save_raw_data(db: AsyncSession, task_id: str, rows: list[dict]):
        for row in rows:
            rd = RawData(
                task_id=task_id,
                lon=row.get("lon"), lat=row.get("lat"), depth_m=row.get("depth_m"),
                temperature=row.get("temperature"), conductivity=row.get("conductivity"),
                salinity=row.get("salinity"), ph=row.get("ph"),
                turbidity=row.get("turbidity"), chlorophyll=row.get("chlorophyll"),
                dissolved_oxygen=row.get("dissolved_oxygen"),
                suspicious=row.get("_suspicious", 0),
            )
            db.add(rd)
        await db.commit()
        logger.info(f"原始数据入库 | task_id={task_id} | rows={len(rows)}")

    @staticmethod
    async def get_task(db: AsyncSession, task_id: str):
        result = await db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_raw_data(db: AsyncSession, task_id: str) -> list[RawData]:
        result = await db.execute(
            select(RawData).where(RawData.task_id == task_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update_task_status(db: AsyncSession, task_id: str, status: str,
                                 progress: int = 0, anomaly_count: int = None,
                                 report_path: str = None):
        task = await DataService.get_task(db, task_id)
        if not task:
            return
        task.status = status
        task.progress = progress
        if anomaly_count is not None:
            task.anomaly_count = anomaly_count
        if report_path is not None:
            task.report_path = report_path
        if status in ("success", "failed"):
            task.finished_at = datetime.utcnow()
        await db.commit()

    @staticmethod
    async def update_task_status_nothrow(task_id: str, status: str,
                                         progress: int = 0, anomaly_count: int = None):
        """独立会话更新状态，不抛异常（用于流水线中的进度更新）"""
        from app.config.database import AsyncSessionMaker
        try:
            async with AsyncSessionMaker() as db:
                await DataService.update_task_status(
                    db, task_id, status, progress, anomaly_count=anomaly_count)
        except Exception as e:
            import logging
            logging.getLogger("app").warning(f"update_task_status_nothrow failed: {e}")
