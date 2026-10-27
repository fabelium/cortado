import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { createError, readBody } from 'h3'
import { registerEndpoint } from '@nuxt/test-utils/runtime'
import { useAuthStore } from '~/stores/auth'

const USER = { id: 1, name: 'Ana', email: 'ana@example.com' }
let sessionActive = false
let rejectLogin = false
let registered: Record<string, unknown> | null = null

registerEndpoint('/sanctum/csrf-cookie', () => '')
registerEndpoint('/api/login', {
  method: 'POST',
  handler: () => {
    if (rejectLogin) {
      throw createError({ statusCode: 422, data: { message: 'These credentials do not match our records.' } })
    }
    sessionActive = true
    return ''
  },
})
registerEndpoint('/api/register', {
  method: 'POST',
  handler: async (event) => {
    registered = await readBody(event)
    return { token: 'bearer-only' } // register does NOT start a session
  },
})
registerEndpoint('/api/logout', {
  method: 'POST',
  handler: () => {
    sessionActive = false
    return ''
  },
})
registerEndpoint('/api/user', () => {
  if (!sessionActive) throw createError({ statusCode: 401 })
  return USER
})

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionActive = false
    rejectLogin = false
    registered = null
  })

  it('login establishes the session and populates user', async () => {
    const auth = useAuthStore()
    await auth.login({ email: USER.email, password: 'secret' })
    expect(auth.user).toEqual(USER)
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.status).toBe('idle')
  })

  it('login surfaces the 422 message and leaves user null', async () => {
    rejectLogin = true
    const auth = useAuthStore()
    await auth.login({ email: USER.email, password: 'wrong' })
    expect(auth.user).toBeNull()
    expect(auth.status).toBe('error')
    expect(auth.error).toBe('These credentials do not match our records.')
  })

  it('register posts the payload then chains into login', async () => {
    const auth = useAuthStore()
    await auth.register({ name: 'Ana', email: USER.email, password: 'secret', password_confirmation: 'secret' })
    expect(registered).toMatchObject({ name: 'Ana', email: USER.email })
    expect(auth.user).toEqual(USER)
  })

  it('logout clears the user', async () => {
    const auth = useAuthStore()
    await auth.login({ email: USER.email, password: 'secret' })
    await auth.logout()
    expect(auth.user).toBeNull()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('fetchUser sets user to null on 401 without erroring', async () => {
    const auth = useAuthStore()
    await auth.fetchUser()
    expect(auth.user).toBeNull()
    expect(auth.status).toBe('idle')
  })
})
