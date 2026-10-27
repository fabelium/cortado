import { describe, it, expect } from 'vitest'

describe('editorial theme', () => {
  it('uses the terracotta/stone palette', () => {
    const ui = useAppConfig().ui as { colors?: { primary?: string, neutral?: string } }
    expect(ui?.colors?.primary).toBe('orange')
    expect(ui?.colors?.neutral).toBe('stone')
  })
})
