import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import StepBadge from '~/components/StepBadge.vue'

describe('StepBadge', () => {
  it('renders the step number on ink by default', async () => {
    const c = await mountSuspended(StepBadge, { props: { step: 2 } })
    expect(c.text()).toBe('2')
    expect(c.find('span').classes().join(' ')).toContain('bg-neutral-900')
  })

  it('accent switches to the terracotta background', async () => {
    const c = await mountSuspended(StepBadge, { props: { step: 3, accent: true } })
    expect(c.find('span').classes().join(' ')).toContain('bg-primary')
  })

  it('lg switches the size', async () => {
    const c = await mountSuspended(StepBadge, { props: { step: 1, size: 'lg' } })
    expect(c.find('span').classes().join(' ')).toContain('size-8')
  })
})
