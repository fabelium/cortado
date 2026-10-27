import { describe, it, expect } from 'vitest'
import { formatDuration } from '~/utils/formatDuration'

describe('formatDuration', () => {
  it('formats seconds as m:ss', () => {
    expect(formatDuration(540)).toBe('9:00')
    expect(formatDuration(65)).toBe('1:05')
  })
  it('returns a dash for null or negative', () => {
    expect(formatDuration(null)).toBe('—')
    expect(formatDuration(-1)).toBe('—')
  })
})
