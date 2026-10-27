import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mountSuspended, registerEndpoint, mockNuxtImport } from '@nuxt/test-utils/runtime'
import AppHeader from '~/components/AppHeader.vue'
import { useAuthStore } from '~/stores/auth'

const { navigateToMock } = vi.hoisted(() => ({ navigateToMock: vi.fn() }))
mockNuxtImport('navigateTo', () => navigateToMock)

registerEndpoint('/api/logout', { method: 'POST', handler: () => '' })

describe('AppHeader', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    navigateToMock.mockClear()
  })

  it('shows no user controls when logged out', async () => {
    const c = await mountSuspended(AppHeader)
    expect(c.text()).not.toContain('Salir')
  })

  it('shows the user email and logs out', async () => {
    const c = await mountSuspended(AppHeader)
    const auth = useAuthStore()
    auth.user = { id: 1, name: 'Ana', email: 'ana@example.com' }
    await vi.waitFor(() => expect(c.text()).toContain('ana@example.com'))
    const logout = c.findAll('button').find(b => b.text().includes('Salir'))
    expect(logout).toBeTruthy()
    await logout!.trigger('click')
    await vi.waitFor(() => expect(auth.user).toBeNull())
    expect(navigateToMock).toHaveBeenCalledWith('/login')
  })
})
