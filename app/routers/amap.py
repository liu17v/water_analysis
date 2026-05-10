"""高德地图 API 代理控制器 — 转发前端请求，解决浏览器 CORS 限制"""
import httpx
from fastapi import APIRouter, Query
from app.config.settings import get_settings
from app.config.response import success, fail
from app.config.logging import get_logger

logger = get_logger("routers.amap")
settings = get_settings()
amap_router = APIRouter(tags=["高德地图代理"])


@amap_router.get("/api/weather", summary="高德天气代理")
async def proxy_weather(city: str = Query(..., description="城市名或 adcode")):
    if not settings.AMAP_API_KEY:
        return fail("未配置高德 API 密钥")

    params = {"key": settings.AMAP_API_KEY, "city": city, "extensions": "base", "output": "JSON"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://restapi.amap.com/v3/weather/weatherInfo", params=params)
            data = resp.json()
        if data.get("status") == "1" and data.get("lives"):
            return success(datas=data["lives"])
        logger.warning(f"高德天气 API 返回异常: city={city} resp={data}")
        return fail("暂无天气数据")
    except Exception as e:
        logger.error(f"高德天气 API 请求失败: city={city} err={e}")
        return fail("天气服务暂不可用")


@amap_router.get("/api/geocode", summary="高德地理编码代理")
async def proxy_geocode(address: str = Query(...), city: str = Query("")):
    if not settings.AMAP_API_KEY:
        return fail("未配置高德 API 密钥")

    params = {"key": settings.AMAP_API_KEY, "address": address, "output": "JSON"}
    if city:
        params["city"] = city
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://restapi.amap.com/v3/geocode/geo", params=params)
            data = resp.json()
        if data.get("status") == "1" and data.get("geocodes"):
            items = []
            for g in data["geocodes"]:
                lon, lat = g["location"].split(",")
                items.append({
                    "lon": float(lon),
                    "lat": float(lat),
                    "name": g["formatted_address"],
                    "address": g["formatted_address"],
                })
            return success(datas={"items": items})
        return fail("未找到匹配位置")
    except Exception as e:
        logger.error(f"高德地理编码 API 请求失败: address={address} err={e}")
        return fail("地理编码服务暂不可用")
