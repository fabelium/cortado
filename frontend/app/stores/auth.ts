import { defineStore } from 'pinia'
import type { FetchError } from 'ofetch'
import { useAuthClient } from '~/composables/useAuthClient'
import type { User, LoginRequest, RegisterRequest } from '~~/shared/types/auth'

function messageFrom(e: unknown): string {
  // Laravel puts {message} at the body root; h3 test errors nest it in data.
  const err = e as FetchError<{ message?: string, data?: { message?: string } }>
  return err.data?.message ?? err.data?.data?.message ?? 'Algo ha ido mal. Vuelve a intentarlo.'
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    status: 'idle' as 'idle' | 'loading' | 'error',
    error: null as string | null,
  }),
  getters: {
    isAuthenticated: state => state.user !== null,
  },
  actions: {
    async login(payload: LoginRequest) {
      this.status = 'loading'
      this.error = null
      try {
        await useAuthClient().login(payload)
        await this.fetchUser()
        this.status = 'idle'
      }
      catch (e) {
        this.status = 'error'
        this.error = messageFrom(e)
      }
    },
    async register(payload: RegisterRequest) {
      this.status = 'loading'
      this.error = null
      try {
        await useAuthClient().register(payload)
      }
      catch (e) {
        this.status = 'error'
        this.error = messageFrom(e)
        return
      }
      // The API returns a Bearer token only; log in to start the SPA session.
      await this.login({ email: payload.email, password: payload.password })
    },
    async logout() {
      try {
        await useAuthClient().logout()
      }
      finally {
        this.user = null
      }
    },
    async fetchUser() {
      // 401 is the expected "not logged in" answer — never a visible error.
      try {
        this.user = await useAuthClient().getUser()
      }
      catch {
        this.user = null
      }
    },
  },
})
