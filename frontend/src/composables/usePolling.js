import { ref, onUnmounted } from 'vue'

/**
 * 通用轮询 composable
 * @param {Function} fn - 轮询执行的异步函数，返回 true 时停止轮询
 * @param {number} interval - 轮询间隔（ms）
 * @param {number} maxDuration - 最大轮询时长（ms），默认不限制
 * @returns {{ start: Function, stop: Function, isPolling: Ref<boolean>, elapsed: Ref<number> }}
 */
export function usePolling(fn, interval = 2000, maxDuration = 0) {
  const isPolling = ref(false)
  const elapsed = ref(0)
  let timer = null
  let startTime = null
  let durationTimer = null

  function start() {
    if (isPolling.value) return
    isPolling.value = true
    elapsed.value = 0
    startTime = Date.now()

    const tick = async () => {
      if (!isPolling.value) return
      const shouldStop = await fn()
      elapsed.value = Date.now() - startTime
      if (shouldStop || (maxDuration > 0 && elapsed.value >= maxDuration)) {
        stop()
        return
      }
      timer = setTimeout(tick, interval)
    }

    tick()

    if (maxDuration > 0) {
      durationTimer = setTimeout(() => {
        if (isPolling.value) stop()
      }, maxDuration)
    }
  }

  function stop() {
    isPolling.value = false
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    if (durationTimer) {
      clearTimeout(durationTimer)
      durationTimer = null
    }
  }

  onUnmounted(stop)

  return { start, stop, isPolling, elapsed }
}
