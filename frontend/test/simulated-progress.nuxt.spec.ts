import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useSimulatedProgress } from '~/composables/useSimulatedProgress'

describe('useSimulatedProgress', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('climbs toward 90 while running and snaps to 100 on finish', () => {
    const seen: number[] = []
    const p = useSimulatedProgress(v => seen.push(v), 100)
    p.start()
    expect(seen[0]).toBe(0)
    vi.advanceTimersByTime(350)
    const peak = Math.max(...seen)
    expect(peak).toBeGreaterThan(0)
    expect(peak).toBeLessThanOrEqual(90)
    p.finish()
    expect(seen.at(-1)).toBe(100)
  })

  it('stop() halts further updates', () => {
    const seen: number[] = []
    const p = useSimulatedProgress(v => seen.push(v), 100)
    p.start()
    p.stop()
    const count = seen.length
    vi.advanceTimersByTime(500)
    expect(seen.length).toBe(count)
  })
})
