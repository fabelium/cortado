// Throwaway: fakes generation progress until real websocket progress (Reverb)
// exists. Isolated here so the cutover replaces only this file — the store sets
// job.progress through the same callback regardless of the source.
export function useSimulatedProgress(onProgress: (p: number) => void, stepMs = 120) {
  let timer: ReturnType<typeof setInterval> | null = null
  let value = 0

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  function start() {
    stop()
    value = 0
    onProgress(0)
    timer = setInterval(() => {
      value = Math.min(90, value + 10)
      onProgress(value)
      if (value >= 90) stop()
    }, stepMs)
  }

  function finish() {
    stop()
    onProgress(100)
  }

  return { start, finish, stop }
}
