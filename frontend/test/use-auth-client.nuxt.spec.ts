import { describe, it, expect, beforeEach } from 'vitest'
import { createError } from 'h3'
import { registerEndpoint } from '@nuxt/test-utils/runtime'
import { useAuthClient } from '~/composables/useAuthClient'

let csrfHits = 0
let loginAttempts = 0
let failLoginWith419Once = false

registerEndpoint('/sanctum/csrf-cookie', () => {
  csrfHits++
  return ''
})
registerEndpoint('/api/login', {
  method: 'POST',
  handler: () => {
    loginAttempts++
    if (failLoginWith419Once && loginAttempts === 1) {
      throw createError({ statusCode: 419 })
    }
    return ''
  },
})
registerEndpoint('/api/logout', { method: 'POST', handler: () => '' })
registerEndpoint('/api/user', () => ({ id: 1, name: 'Ana', email: 'ana@example.com' }))

describe('useAuthClient', () => {
  beforeEach(() => {
    csrfHits = 0
    loginAttempts = 0
    failLoginWith419Once = false
  })

  it('login fetches the csrf cookie before posting credentials', async () => {
    const { login } = useAuthClient()
    await login({ email: 'ana@example.com', password: 'secret' })
    expect(csrfHits).toBe(1)
    expect(loginAttempts).toBe(1)
  })

  it('login refreshes the csrf cookie and retries once on 419', async () => {
    failLoginWith419Once = true
    const { login } = useAuthClient()
    await login({ email: 'ana@example.com', password: 'secret' })
    expect(csrfHits).toBe(2)
    expect(loginAttempts).toBe(2)
  })

  it('getUser returns the authenticated user', async () => {
    const { getUser } = useAuthClient()
    expect(await getUser()).toEqual({ id: 1, name: 'Ana', email: 'ana@example.com' })
  })
})
