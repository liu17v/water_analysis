const STATUS_MAP = {
  pending: '待处理', processing: '处理中',
  success: '已完成', failed: '失败',
}

const STATUS_TYPE_MAP = {
  pending: 'info', processing: 'warning',
  success: 'success', failed: 'danger',
}

export function useStatus() {
  function statusLabel(s) {
    return STATUS_MAP[s] || s
  }
  function statusType(s) {
    return STATUS_TYPE_MAP[s] || 'info'
  }
  return { statusLabel, statusType }
}
