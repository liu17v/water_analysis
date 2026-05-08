const STATUS_MAP = { pending: '待处理', processing: '处理中', success: '已完成', failed: '失败' }
const STATUS_TYPE_MAP = { success: 'success', processing: 'warning', failed: 'danger', pending: 'info' }

const INDICATOR_LABEL = { chl: '叶绿素', odo: '溶解氧', temp: '水温', ph: 'pH', turb: '浊度' }
const INDICATOR_SHORT = { chlorophyll: 'chl', dissolved_oxygen: 'odo', temperature: 'temp', ph: 'ph', turbidity: 'turb' }
const INDICATOR_UNIT = { chlorophyll: 'µg/L', dissolved_oxygen: 'mg/L', temperature: '°C', ph: '', turbidity: 'NTU' }

const INDICATOR_OPTIONS = [
  { label: '叶绿素 (Chl)', value: 'chlorophyll' },
  { label: '溶解氧 (DO)', value: 'dissolved_oxygen' },
  { label: '水温 (Temp)', value: 'temperature' },
  { label: 'pH', value: 'ph' },
  { label: '浊度 (Turb)', value: 'turbidity' },
]

export function useTask() {
  function statusLabel(s) { return STATUS_MAP[s] || s }
  function statusType(s) { return STATUS_TYPE_MAP[s] || 'info' }
  function shortLabel(code) { return INDICATOR_LABEL[code] || code }
  function shortCode(full) { return INDICATOR_SHORT[full] || 'chl' }
  function indicatorUnit(full) { return INDICATOR_UNIT[full] || '' }

  return { statusLabel, statusType, shortLabel, shortCode, indicatorUnit, INDICATOR_OPTIONS }
}
