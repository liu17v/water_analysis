"""异常检测：统计阈值 + 孤立森林"""
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from app.config.settings import get_settings

settings = get_settings()

INDICATOR_MAP = {
    "chlorophyll": "chl", "dissolved_oxygen": "odo",
    "temperature": "temp", "ph": "ph", "turbidity": "turb",
}

FEATURE_COLS = ["chlorophyll", "dissolved_oxygen", "temperature", "ph", "turbidity"]

RULES = [
    ("chlorophyll", settings.CHL_MIN, settings.CHL_MAX),
    ("dissolved_oxygen", settings.ODO_MIN, settings.ODO_MAX),
    ("ph", settings.PH_MIN, settings.PH_MAX),
    ("turbidity", settings.TURB_MIN, settings.TURB_MAX),
    ("temperature", settings.TEMP_MIN, settings.TEMP_MAX),
]


def _val(obj, attr):
    v = getattr(obj, attr, None)
    return v if v is not None else None


def detect_threshold(rows):
    anomalies = []
    for r in rows:
        for col, lo, hi in RULES:
            v = _val(r, col)
            if v is not None and (v < lo or v > hi):
                anomalies.append({
                    "lon": r.lon, "lat": r.lat, "depth": r.depth_m,
                    "indicator": INDICATOR_MAP[col], "value": v,
                    "method": "threshold", "threshold_low": lo, "threshold_high": hi,
                })
    return anomalies


def detect_isolation_forest(rows):
    features, valid_idx = [], []
    for i, r in enumerate(rows):
        vals = [_val(r, c) for c in FEATURE_COLS]
        if None not in vals:
            features.append(vals)
            valid_idx.append(i)
    if len(features) < 10:
        return []

    X = StandardScaler().fit_transform(np.array(features))
    model = IsolationForest(contamination=settings.CONTAMINATION, random_state=42, n_estimators=100)
    preds = model.fit_predict(X)

    anomalies = []
    for idx, pred in zip(valid_idx, preds):
        if pred == -1:
            r = rows[idx]
            for col in FEATURE_COLS:
                v = _val(r, col)
                if v is not None:
                    anomalies.append({
                        "lon": r.lon, "lat": r.lat, "depth": r.depth_m,
                        "indicator": INDICATOR_MAP[col], "value": v,
                        "method": "isolation_forest", "threshold_low": None, "threshold_high": None,
                    })
    return anomalies


def merge_anomalies(a, b):
    seen = set()
    merged = []
    for item in a + b:
        key = (round(item["lon"], 6), round(item["lat"], 6), item["depth"], item["indicator"])
        if key not in seen:
            seen.add(key)
            merged.append(item)
    return merged


def run_anomaly_detection(rows):
    return merge_anomalies(detect_threshold(rows), detect_isolation_forest(rows))
