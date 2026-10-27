import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mockNuxtImport } from '@nuxt/test-utils/runtime'
import type { RouteLocationNormalized } from 'vue-router'
import authGuard from '~/middleware/auth.global'
import { useAuthStore } from '~/stores/auth'

const { navigateToMock } = vi.hoisted(() => ({ navigateToMock: vi.fn() }))
mockNuxtImport('navigateTo', () => navigateToMock)

function route(path: string): RouteLocationNormalized {
  return { path } as RouteLocationNormalized
}

describe('auth.global middleware', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    navigateToMock.mockClear()
  })

  it('redirects unauthenticated users to /login', () => {
    authGuard(route('/'), route('/'))
    expect(navigateToMock).toHaveBeenCalledWith('/login')
  })

  it('lets unauthenticated users reach /login and /register', () => {
    authGuard(route('/login'), route('/'))
    authGuard(route('/register'), route('/'))
    expect(navigateToMock).not.toHaveBeenCalled()
  })

  it('redirects authenticated users away from /login to /', () => {
    useAuthStore().user = { id: 1, name: 'Ana', email: 'ana@example.com' }
    authGuard(route('/login'), route('/'))
    expect(navigateToMock).toHaveBeenCalledWith('/')
  })

  it('lets authenticated users through', () => {
    useAuthStore().user = { id: 1, name: 'Ana', email: 'ana@example.com' }
    authGuard(route('/'), route('/'))
    expect(navigateToMock).not.toHaveBeenCalled()
  })
})
