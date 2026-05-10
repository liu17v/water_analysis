/**
 * 高德地图 (Amap) 工具模块
 * 提供 Leaflet 高德瓦片图层、地理编码等功能
 */

// 高德瓦片服务 — 无需 key 也可用（瓦片 CDN），带上 key 确保稳定
const KEY = '5d13c57bc39b994130a6d23c68c69a35'

// 子域名轮询（1-4）
const SUBDOMAINS = ['1', '2', '3', '4']

/**
 * 高德矢量街道图瓦片 URL（Leaflet 用）
 * 格式: https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}
 */
export function roadTileUrl() {
  return `https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&key=${KEY}&x={x}&y={y}&z={z}`
}

/**
 * 高德卫星图瓦片 URL（Leaflet 用）
 */
export function satelliteTileUrl() {
  return `https://webst0{s}.is.autonavi.com/appmaptile?style=6&key=${KEY}&x={x}&y={y}&z={z}`
}

/**
 * 高德卫星+路网标注瓦片 URL（Leaflet 用）
 */
export function hybridTileUrl() {
  return `https://webst0{s}.is.autonavi.com/appmaptile?style=8&key=${KEY}&x={x}&y={y}&z={z}`
}

/**
 * Leaflet 高德瓦片图层配置
 * 返回三个图层: 街道图、卫星图、卫星+标注
 */
export function createAmapLayers(L) {
  return {
    road: L.tileLayer(roadTileUrl(), {
      subdomains: SUBDOMAINS,
      attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
      maxZoom: 18,
    }),
    satellite: L.tileLayer(satelliteTileUrl(), {
      subdomains: SUBDOMAINS,
      attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
      maxZoom: 18,
    }),
    hybrid: L.tileLayer(hybridTileUrl(), {
      subdomains: SUBDOMAINS,
      attribution: '&copy; <a href="https://www.amap.com/">高德地图</a>',
      maxZoom: 18,
    }),
  }
}

/**
 * 高德地理编码 — 地名 → 坐标
 * https://restapi.amap.com/v3/geocode/geo
 */
export async function amapGeocode(address, city = '') {
  const params = new URLSearchParams({ key: KEY, address, output: 'JSON' })
  if (city) params.set('city', city)
  try {
    const res = await fetch(`https://restapi.amap.com/v3/geocode/geo?${params}`)
    const data = await res.json()
    if (data.status === '1' && data.geocodes?.length) {
      const [lon, lat] = data.geocodes[0].location.split(',').map(Number)
      return { lon, lat, name: data.geocodes[0].formatted_address }
    }
    return null
  } catch {
    return null
  }
}

/**
 * 高德逆地理编码 — 坐标 → 地名
 * @returns {{ address: string, city: string, adcode: string, province: string, district: string } | null}
 */
export async function amapRegeo(lon, lat) {
  const params = new URLSearchParams({ key: KEY, location: `${lon},${lat}`, output: 'JSON' })
  try {
    const res = await fetch(`https://restapi.amap.com/v3/geocode/regeo?${params}`)
    const data = await res.json()
    if (data.status === '1' && data.regeocode) {
      const ac = data.regeocode.addressComponent || {}
      return {
        address: data.regeocode.formatted_address,
        city: ac.city || ac.province || '',
        adcode: ac.adcode || '',
        province: ac.province || '',
        district: ac.district || '',
      }
    }
    return null
  } catch {
    return null
  }
}

/**
 * 高德天气查询 — 实时天气
 * https://restapi.amap.com/v3/weather/weatherInfo
 * @param {string} city - 城市名（如 "武汉市"）或 adcode（如 "420100"）
 * @returns {{ temperature, humidity, weather, winddirection, windpower, city, adcode } | null}
 */
export async function amapWeather(city) {
  const params = new URLSearchParams({
    key: KEY,
    city,
    extensions: 'base',
    output: 'JSON',
  })
  try {
    const res = await fetch(`https://restapi.amap.com/v3/weather/weatherInfo?${params}`)
    const data = await res.json()
    if (data.status === '1' && data.lives?.length) {
      const live = data.lives[0]
      return {
        temperature: live.temperature,
        humidity: live.humidity,
        weather: live.weather,
        winddirection: live.winddirection,
        windpower: live.windpower,
        city: live.city,
        adcode: live.adcode,
      }
    }
    return null
  } catch {
    return null
  }
}
