import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import StepHeading from '~/components/StepHeading.vue'

describe('StepHeading', () => {
  it('renders the badge, title and subtitle', async () => {
    const c = await mountSuspended(StepHeading, {
      props: { step: 2, title: 'Elige los fragmentos', subtitle: 'Incluye los que quieras.' },
    })
    expect(c.find('h2').text()).toContain('2')
    expect(c.find('h2').text()).toContain('Elige los fragmentos')
    expect(c.text()).toContain('Incluye los que quieras.')
  })

  it('omits badge and subtitle when absent', async () => {
    const c = await mountSuspended(StepHeading, {
      props: { title: 'Charla con tu selección' },
    })
    expect(c.find('h2').text()).toBe('Charla con tu selección')
    expect(c.find('p').exists()).toBe(false)
  })
})
