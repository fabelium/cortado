import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import AppLogo from '~/components/AppLogo.vue'

describe('AppLogo', () => {
  it('renders the brand name', async () => {
    const component = await mountSuspended(AppLogo)
    expect(component.text()).toContain('Un cortado, por favor')
  })
})
