import type { FetchError } from 'ofetch'
import type { User, LoginRequest, RegisterRequest } from '~~/shared/types/auth'
import { ensureCsrf } from '~/utils/csrf'

export function useAuthClient() {
  const { $api } = useNuxtApp()
  const apiBase = useRuntimeConfig().public.apiBase

  // Sanctum: fetch the XSRF cookie before a mutating auth call; a 419 means
  // the token expired mid-session — refresh it and retry exactly once.
  async function withCsrf<T>(run: () => Promise<T>): Promise<T> {
    await ensureCsrf(apiBase)
    try {
      return await run()
    }
    catch (e) {
      if ((e as FetchError).statusCode === 419) {
        await ensureCsrf(apiBase)
        return await run()
      }
      throw e
    }
  }

  async function login(payload: LoginRequest): Promise<void> {
    await withCsrf(() => $api('/login', { method: 'POST', body: payload }))
  }

  async function register(payload: RegisterRequest): Promise<void> {
    await withCsrf(() => $api('/register', { method: 'POST', body: payload }))
  }

  async function logout(): Promise<void> {
    await $api('/logout', { method: 'POST' })
  }

  async function getUser(): Promise<User> {
    return await $api<User>('/user')
  }

  return { login, register, logout, getUser }
}
