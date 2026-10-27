import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { createError } from 'h3'
import { mountSuspended, registerEndpoint, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import LoginForm from '~/components/LoginForm.vue'

const { navigateToMock } = vi.hoisted(() => ({ navigateToMock: vi.fn() }))
mockNuxtImport('navigateTo', () => navigateToMock)

const USER = { id: 1, name: 'Ana', email: 'ana@example.com' }
let sessionActive = false
let rejectLogin = false

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
registerEndpoint('/api/user', () => {
  if (!sessionActive) throw createError({ statusCode: 401 })
  return USER
})

async function fillAndSubmit(c: Awaited<ReturnType<typeof mountSuspended>>) {
  await c.find('input[type="email"]').setValue(USER.email)
  await c.find('input[type="password"]').setValue('secret')
  await c.find('form').trigger('submit.prevent')
  await flushPromises()
}

describe('LoginForm', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionActive = false
    rejectLogin = false
    navigateToMock.mockClear()
  })

  it('logs in and navigates home on success', async () => {
    const c = await mountSuspended(LoginForm)
    await fillAndSubmit(c)
    // The mock fetch transport resolves on macrotasks — poll instead of one flush.
    await vi.waitFor(() => expect(navigateToMock).toHaveBeenCalledWith('/'))
  })

  it('shows the API error message on 422 and stays', async () => {
    rejectLogin = true
    const c = await mountSuspended(LoginForm)
    await fillAndSubmit(c)
    await vi.waitFor(() => expect(c.text()).toContain('These credentials do not match our records.'))
    expect(navigateToMock).not.toHaveBeenCalled()
  })

  it('links to the register page', async () => {
    const c = await mountSuspended(LoginForm)
    expect(c.find('a[href="/register"]').exists()).toBe(true)
  })
})
