/**
 * 坐标系统转换工具
 * WGS-84（GPS 标准） ↔ GCJ-02（高德/火星坐标系）
 *
 * 高德地图瓦片使用 GCJ-02 坐标系，而标准 GPS 设备/CSV 数据通常使用 WGS-84。
 * 如果不做转换，直接绘制会有 300~700 米的偏移。
 */

const PI = Math.PI
const xPI = (PI * 3000) / 180
const A = 6378245 // 长半轴
const EE = 0.00669342162296594323 // 扁率

function isOutOfChina(lat, lon) {
  return lon < 72.004 || lon > 137.8347 || lat < 0.8293 || lat > 55.8271
}

function transformLat(x, y) {
  let ret = -100 + 2 * x + 3 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x))
  ret += ((20 * Math.sin(6 * x * PI) + 20 * Math.sin(2 * x * PI)) * 2) / 3
  ret += ((20 * Math.sin(y * PI) + 40 * Math.sin((y / 3) * PI)) * 2) / 3
  ret += ((160 * Math.sin((y / 12) * PI) + 320 * Math.sin((y * PI) / 30)) * 2) / 3
  return ret
}

function transformLon(x, y) {
  let ret = 300 + x + 2 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x))
  ret += ((20 * Math.sin(6 * x * PI) + 20 * Math.sin(2 * x * PI)) * 2) / 3
  ret += ((20 * Math.sin(x * PI) + 40 * Math.sin((x / 3) * PI)) * 2) / 3
  ret += ((150 * Math.sin((x / 12) * PI) + 300 * Math.sin((x / 30) * PI)) * 2) / 3
  return ret
}

/**
 * WGS-84 → GCJ-02（火星坐标系）
 * 适用于：将标准 GPS 坐标绘制到高德地图上
 * @param {number} lat - WGS-84 纬度
 * @param {number} lon - WGS-84 经度
 * @returns {[number, number]} [gcjLat, gcjLon]
 */
export function wgs84ToGcj02(lat, lon) {
  if (isOutOfChina(lat, lon)) return [lat, lon]

  let dlat = transformLat(lon - 105, lat - 35)
  let dlon = transformLon(lon - 105, lat - 35)
  const radLat = (lat / 180) * PI
  let magic = Math.sin(radLat)
  magic = 1 - EE * magic * magic
  const sqrtMagic = Math.sqrt(magic)
  dlat = (dlat * 180) / (((A * (1 - EE)) / (magic * sqrtMagic)) * PI)
  dlon = (dlon * 180) / ((A / sqrtMagic) * Math.cos(radLat) * PI)

  return [lat + dlat, lon + dlon]
}

/**
 * GCJ-02 → WGS-84
 * 适用于：将高德坐标转换为标准 GPS 坐标
 * @param {number} lat - GCJ-02 纬度
 * @param {number} lon - GCJ-02 经度
 * @returns {[number, number]} [wgsLat, wgsLon]
 */
export function gcj02ToWgs84(lat, lon) {
  if (isOutOfChina(lat, lon)) return [lat, lon]

  let dlat = transformLat(lon - 105, lat - 35)
  let dlon = transformLon(lon - 105, lat - 35)
  const radLat = (lat / 180) * PI
  let magic = Math.sin(radLat)
  magic = 1 - EE * magic * magic
  const sqrtMagic = Math.sqrt(magic)
  dlat = (dlat * 180) / (((A * (1 - EE)) / (magic * sqrtMagic)) * PI)
  dlon = (dlon * 180) / ((A / sqrtMagic) * Math.cos(radLat) * PI)

  return [lat - dlat, lon - dlon]
}
