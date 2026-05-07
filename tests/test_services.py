import numpy as np
import pytest
from app.services.feature_extractor import extract_features, normalize
from app.services.interpolation import idw, build_grid


def test_idw_basic():
    x = np.array([0, 1, 2])
    y = np.array([0, 1, 2])
    z = np.array([1, 2, 3])
    xi = np.array([0.5, 1.5])
    yi = np.array([0.5, 1.5])
    result = idw(x, y, z, xi, yi, power=2)
    assert len(result) == 2
    assert all(v > 0 for v in result)


def test_build_grid():
    lons = np.array([114.0, 114.1, 114.2])
    lats = np.array([22.6, 22.7, 22.8])
    xi, yi, lon_vec, lat_vec = build_grid(lons, lats)
    assert xi.shape == (50, 50)
    assert yi.shape == (50, 50)
    assert len(lon_vec) == 50
    assert len(lat_vec) == 50


def test_feature_vector_dim():
    from types import SimpleNamespace
    rows = []
    for lon in [114.0, 114.1, 114.2]:
        for lat in [22.6, 22.7, 22.8]:
            for depth in [1, 2]:
                rows.append(SimpleNamespace(
                    lon=lon, lat=lat, depth_m=depth,
                    temperature=25.0, conductivity=500.0,
                    salinity=0.3, ph=7.5, turbidity=3.0,
                    chlorophyll=5.0, dissolved_oxygen=8.0,
                ))
    feats = extract_features(rows)
    assert len(feats) == 13
    normed = normalize(feats)
    assert all(0 <= v <= 1 for v in normed)
