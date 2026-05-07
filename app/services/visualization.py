"""可视化生成：Plotly 2D Contour + 3D Volume"""
import numpy as np
import plotly.graph_objects as go
from app.config.settings import get_settings

settings = get_settings()

# 参考标准色阶 (blue-white-red)
COLORSCALE = [
    [0.0, "rgb(5,48,97)"],
    [0.1, "rgb(33,102,172)"],
    [0.2, "rgb(67,147,195)"],
    [0.3, "rgb(146,197,222)"],
    [0.4, "rgb(209,229,240)"],
    [0.5, "rgb(247,247,247)"],
    [0.6, "rgb(253,219,199)"],
    [0.7, "rgb(244,165,130)"],
    [0.8, "rgb(214,96,77)"],
    [0.9, "rgb(178,24,43)"],
    [1.0, "rgb(103,0,31)"],
]

INDICATOR_LABELS = {
    "chlorophyll": ("叶绿素", "µg/L"),
    "dissolved_oxygen": ("溶解氧", "mg/L"),
    "temperature": ("水温", "°C"),
    "ph": ("pH", ""),
    "turbidity": ("浊度", "NTU"),
}

# Short codes used in anomaly records → labels for hover display
INDICATOR_SHORT_MAP = {
    "chl": "叶绿素", "odo": "溶解氧", "temp": "水温", "ph": "pH", "turb": "浊度",
}


def contour_html(grid: dict, indicator: str, depth: float, anomaly_points=None) -> str:
    label, unit = INDICATOR_LABELS.get(indicator, (indicator, ""))
    x, y, z = grid["x"], grid["y"], np.array(grid["z"])

    fig = go.Figure()
    fig.add_trace(go.Contour(
        z=z, x=x, y=y,
        colorscale=COLORSCALE,
        contours=dict(showlabels=True),
        colorbar=dict(title=dict(text=f"{label} ({unit})" if unit else label)),
        hovertemplate=f"Lon=%{{x:.4f}}<br>Lat=%{{y:.4f}}<br>{label}=%{{z:.2f}} {unit}<extra></extra>",
    ))
    if anomaly_points:
        short_code = {"chlorophyll": "chl", "dissolved_oxygen": "odo",
                      "temperature": "temp", "ph": "ph", "turbidity": "turb"}.get(indicator, indicator)
        filtered = [p for p in anomaly_points if p.get("indicator") == short_code]
        if filtered:
            # Split by value sign for visual distinction
            hover_texts = [
                f"{INDICATOR_SHORT_MAP.get(p.get('indicator',''), p.get('indicator',''))}: {p.get('value','?')}"
                for p in filtered
            ]
            fig.add_trace(go.Scatter(
                x=[p["lon"] for p in filtered],
                y=[p["lat"] for p in filtered],
                mode="markers",
                marker=dict(color="red", size=10, symbol="x", line=dict(width=1, color="darkred")),
                text=hover_texts,
                hovertemplate="<b>⚠ 异常点</b><br>%{text}<br>Lon=%{x:.4f}<br>Lat=%{y:.4f}<extra></extra>",
                name="异常点",
            ))
    fig.update_layout(
        title=dict(text=f"{label} 等值线图 — 深度 {depth}m"),
        xaxis=dict(title="经度"),
        yaxis=dict(title="纬度"),
        height=500,
        margin=dict(l=40, r=40, t=50, b=40),
        dragmode="pan",
    )
    return fig.to_html(full_html=True, include_plotlyjs="cdn")


def build_volume(layer_grids: dict, indicator: str):
    """将多层2D插值网格堆叠为3D体数据"""
    depths = sorted(layer_grids.keys())
    if len(depths) < 2:
        return None

    first = layer_grids[depths[0]]
    nx, ny = len(first["x"]), len(first["y"])
    nz = len(depths)

    values = np.zeros((nz, ny, nx))
    for i, d in enumerate(depths):
        z_grid = np.array(layer_grids[d]["z"])
        values[i, :, :] = z_grid

    lon_vec = np.array(first["x"])
    lat_vec = np.array(first["y"])
    depth_vec = np.array(depths)

    X, Y, Z = np.meshgrid(lon_vec, lat_vec, depth_vec, indexing="xy")
    V = values.transpose(1, 2, 0)

    return {
        "x": X.flatten(),
        "y": Y.flatten(),
        "z": Z.flatten(),
        "value": V.flatten(order="F"),
        "depths": depths,
        "indicator": indicator,
    }


def volume_html(volume: dict, indicator: str, anomaly_points=None) -> str:
    label, unit = INDICATOR_LABELS.get(indicator, (indicator, ""))
    v = volume["value"]
    vmin, vmax = float(np.nanmin(v)), float(np.nanmax(v))

    fig = go.Figure()
    fig.add_trace(go.Volume(
        x=volume["x"],
        y=volume["y"],
        z=volume["z"],
        value=volume["value"],
        isomin=vmin,
        isomax=vmax,
        opacity=0.2,
        surface_count=12,
        caps=dict(x=dict(show=False), y=dict(show=False), z=dict(show=False)),
        colorscale=COLORSCALE,
        colorbar=dict(title=dict(text=f"{label} ({unit})" if unit else label)),
    ))
    if anomaly_points:
        short_code = {"chlorophyll": "chl", "dissolved_oxygen": "odo",
                      "temperature": "temp", "ph": "ph", "turbidity": "turb"}.get(indicator, indicator)
        filtered = [p for p in anomaly_points if p.get("indicator") == short_code]
        if filtered:
            hover_texts = [
                f"{INDICATOR_SHORT_MAP.get(p.get('indicator',''), p.get('indicator',''))}: {p.get('value','?')}"
                for p in filtered
            ]
            fig.add_trace(go.Scatter3d(
                x=[p["lon"] for p in filtered],
                y=[p["lat"] for p in filtered],
                z=[p["depth"] for p in filtered],
                mode="markers",
                marker=dict(color="red", size=5, symbol="x", line=dict(width=1, color="darkred")),
                text=hover_texts,
                hovertemplate="<b>⚠ 异常点</b><br>%{text}<br>Lon=%{x:.4f}<br>Lat=%{y:.4f}<br>Depth=%{z}m<extra></extra>",
                name="异常点",
            ))
    fig.update_layout(
        title=dict(text=f"{label} 三维体渲染"),
        scene=dict(
            xaxis_title="经度",
            yaxis_title="纬度",
            zaxis_title="深度 (m)",
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.0)),
        ),
        height=700,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig.to_html(full_html=True, include_plotlyjs="cdn")


def generate_3d_html(rows, indicator, anomaly_points=None) -> str:
    """生成3D体渲染HTML（兼容旧接口）"""
    from app.services.interpolation import interpolate_all_layers

    grids = interpolate_all_layers(rows, indicator)
    if not grids or len(grids) < 2:
        return _fallback_scatter(rows, indicator, anomaly_points)

    volume = build_volume(grids, indicator)
    if not volume:
        return _fallback_scatter(rows, indicator, anomaly_points)

    return volume_html(volume, indicator, anomaly_points[:200] if anomaly_points else None)


def _fallback_scatter(rows, indicator, anomaly_points=None) -> str:
    """深度层不足时的散点回退方案"""
    label, unit = INDICATOR_LABELS.get(indicator, (indicator, ""))
    lons = [r.lon for r in rows if getattr(r, indicator) is not None]
    lats = [r.lat for r in rows if getattr(r, indicator) is not None]
    depths = [r.depth_m for r in rows if getattr(r, indicator) is not None]
    vals = [getattr(r, indicator) for r in rows if getattr(r, indicator) is not None]

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=lons, y=lats, z=depths,
        mode="markers",
        marker=dict(
            size=3, color=vals,
            colorscale=COLORSCALE,
            colorbar=dict(title=dict(text=f"{label} ({unit})" if unit else label)),
        ),
        hovertemplate=f"Lon=%{{x:.4f}}<br>Lat=%{{y:.4f}}<br>Depth=%{{z}}m<br>{label}=%{{marker.color:.2f}}<extra></extra>",
    ))
    # Overlay anomaly points if any
    if anomaly_points:
        short_code = {"chlorophyll": "chl", "dissolved_oxygen": "odo",
                      "temperature": "temp", "ph": "ph", "turbidity": "turb"}.get(indicator, indicator)
        filtered = [p for p in anomaly_points if p.get("indicator") == short_code]
        if filtered:
            hover_texts = [
                f"{INDICATOR_SHORT_MAP.get(p.get('indicator',''), p.get('indicator',''))}: {p.get('value','?')}"
                for p in filtered
            ]
            fig.add_trace(go.Scatter3d(
                x=[p["lon"] for p in filtered],
                y=[p["lat"] for p in filtered],
                z=[p["depth"] for p in filtered],
                mode="markers",
                marker=dict(color="red", size=5, symbol="x", line=dict(width=1, color="darkred")),
                text=hover_texts,
                hovertemplate="<b>⚠ 异常点</b><br>%{text}<br>Lon=%{x:.4f}<br>Lat=%{y:.4f}<br>Depth=%{z}m<extra></extra>",
                name="异常点",
            ))
    fig.update_layout(
        title=dict(text=f"{label} 三维散点图"),
        scene=dict(xaxis_title="经度", yaxis_title="纬度", zaxis_title="深度 (m)"),
        height=700,
    )
    return fig.to_html(full_html=True, include_plotlyjs="cdn")


def export_image(fig: go.Figure, path: str):
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.write_image(path, format="png", width=800, height=500, scale=2)
