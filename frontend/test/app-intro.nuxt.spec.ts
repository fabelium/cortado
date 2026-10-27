import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import AppIntro from '~/components/AppIntro.vue'

describe('AppIntro', () => {
  it('renders the editorial claim and the one-liner', async () => {
    const c = await mountSuspended(AppIntro)
    expect(c.text()).toContain('Tu recopilación de')
    expect(c.text()).toContain('Coffee Break')
    expect(c.text()).toContain('recién hecha')
    expect(c.text()).toContain('Busca un tema, elige fragmentos reales del podcast')
  })
})
