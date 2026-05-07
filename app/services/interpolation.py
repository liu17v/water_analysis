"""空间插值：IDW / Kriging / Cubic"""
import numpy as np
from scipy.interpolate import griddata
from app.config.settings import get_settings

settings = get_settings()


def idw(x, y, z, xi, yi, power=2):
    xi_f, yi_f = xi.ravel(), yi.ravel()
    zi = np.zeros(len(xi_f))
    for i in range(len(xi_f)):
        dist = np.sqrt((x - xi_f[i])**2 + (y - yi_f[i])**2)
        close = dist < 1e-12
        if np.any(close):
            zi[i] = z[close][0]
        else:
            w = 1.0 / (dist ** power)
            zi[i] = np.sum(w * z) / np.sum(w)
    return zi.reshape(xi.shape)


def build_grid(lons, lats):
    pad = 0.05
    lon_r = lons.max() - lons.min()
    lat_r = lats.max() - lats.min()
    lon_vec = np.linspace(lons.min() - lon_r * pad, lons.max() + lon_r * pad, settings.GRID_RESOLUTION)
    lat_vec = np.linspace(lats.min() - lat_r * pad, lats.max() + lat_r * pad, settings.GRID_RESOLUTION)
    xi, yi = np.meshgrid(lon_vec, lat_vec)
    return xi, yi, lon_vec.tolist(), lat_vec.tolist()


def interpolate_layer(lons, lats, values, method="idw"):
    mask = ~np.isnan(values)
    if mask.sum() < 3:
        return None
    x, y, z = lons[mask], lats[mask], values[mask]
    xi, yi, xv, yv = build_grid(x, y)

    if method == "kriging":
        try:
            from pykrige.ok import OrdinaryKriging
            ok = OrdinaryKriging(x, y, z, variogram_model="spherical")
            zi, _ = ok.execute("grid", xv, yv)
        except Exception:
            zi = griddata((x, y), z, (xi, yi), method="cubic")
    elif method == "idw":
        zi = idw(x, y, z, xi, yi)
    else:
        try:
            zi = griddata((x, y), z, (xi, yi), method="cubic")
        except Exception:
            zi = griddata((x, y), z, (xi, yi), method="linear")

    if zi is None:
        return None
    return {"x": xv, "y": yv, "z": np.nan_to_num(zi).tolist()}


def interpolate_all_layers(rows, indicator, method="idw"):
    depths = sorted(set(r.depth_m for r in rows))
    results = {}
    for d in depths:
        layer = [r for r in rows if r.depth_m == d]
        lons = np.array([r.lon for r in layer])
        lats = np.array([r.lat for r in layer])
        vals = np.array([getattr(r, indicator, None) for r in layer], dtype=float)
        grid = interpolate_layer(lons, lats, vals, method)
        if grid:
            results[d] = grid
    return results
