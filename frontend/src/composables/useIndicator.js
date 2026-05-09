const INDICATOR_OPTIONS = [
  { label: '叶绿素 (Chl)', value: 'chlorophyll' },
  { label: '溶解氧 (DO)', value: 'dissolved_oxygen' },
  { label: '水温 (Temp)', value: 'temperature' },
  { label: 'pH', value: 'ph' },
  { label: '浊度 (Turb)', value: 'turbidity' },
]

const INDICATOR_LABEL = {
  chlorophyll: '叶绿素', dissolved_oxygen: '溶解氧',
  temperature: '水温', ph: 'pH', turbidity: '浊度',
}

const INDICATOR_SHORT = {
  chlorophyll: 'chl', dissolved_oxygen: 'odo',
  temperature: 'temp', ph: 'ph', turbidity: 'turb',
}

const INDICATOR_UNIT = {
  chlorophyll: 'µg/L', dissolved_oxygen: 'mg/L',
  temperature: '°C', ph: '', turbidity: 'NTU',
}

const INDICATOR_COLOR = {
  chlorophyll: '#67c23a', dissolved_oxygen: '#409eff',
  temperature: '#e6a23c', ph: '#f56c6c', turbidity: '#909399',
}

export function useIndicator() {
  function shortLabel(code) {
    return INDICATOR_LABEL[code] || code
  }
  function shortCode(full) {
    return INDICATOR_SHORT[full] || 'chl'
  }
  function indicatorUnit(full) {
    return INDICATOR_UNIT[full] || ''
  }
  function indicatorColor(code) {
    return INDICATOR_COLOR[code] || '#909399'
  }

  return { shortLabel, shortCode, indicatorUnit, indicatorColor, INDICATOR_OPTIONS }
}
