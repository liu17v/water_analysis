"""13 维特征向量提取"""
import numpy as np
from app.config.settings import get_settings

settings = get_settings()
FEATURE_COLS = ["chlorophyll", "dissolved_oxygen", "temperature", "ph", "turbidity"]


def extract_features(rows) -> list[float]:
    feats = []
    for col in FEATURE_COLS:
        vals = [getattr(r, col) for r in rows if getattr(r, col) is not None]
        feats.append(float(np.mean(vals)) if vals else 0.0)
    for col in FEATURE_COLS:
        vals = [getattr(r, col) for r in rows if getattr(r, col) is not None]
        feats.append(float(np.std(vals)) if vals else 0.0)

    anomaly_idx = set()
    for i, r in enumerate(rows):
        for col, lo, hi in [
            ("chlorophyll", settings.CHL_MIN, settings.CHL_MAX),
            ("dissolved_oxygen", settings.ODO_MIN, settings.ODO_MAX),
            ("ph", settings.PH_MIN, settings.PH_MAX),
            ("turbidity", settings.TURB_MIN, settings.TURB_MAX),
            ("temperature", settings.TEMP_MIN, settings.TEMP_MAX),
        ]:
            v = getattr(r, col, None)
            if v is not None and (v < lo or v > hi):
                anomaly_idx.add(i)
    feats.append(len(anomaly_idx) / len(rows) if rows else 0.0)

    lons = [r.lon for r in rows]
    lats = [r.lat for r in rows]
    feats.append(float(np.var(lons)) if len(lons) > 1 else 0.0)
    feats.append(float(np.var(lats)) if len(lats) > 1 else 0.0)
    return feats


def normalize(feats: list[float]) -> list[float]:
    arr = np.array(feats)
    rng = arr.max() - arr.min()
    if rng < 1e-10:
        return [0.5] * len(feats)
    return ((arr - arr.min()) / rng).tolist()
