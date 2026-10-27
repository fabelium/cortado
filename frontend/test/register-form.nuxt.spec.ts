import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { createError } from 'h3'
import { mountSuspended, registerEndpoint, mockNuxtImport } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import RegisterForm from '~/components/RegisterForm.vue'

const { navigateToMock } = vi.hoisted(() => ({ navigateToMock: vi.fn() }))
mockNuxtImport('navigateTo', () => navigateToMock)

const USER = { id: 1, name: 'Ana', email: 'ana@example.com' }
let sessionActive = false
let rejectRegister = false

registerEndpoint('/sanctum/csrf-cookie', () => '')
registerEndpoint('/api/register', {
  method: 'POST',
  handler: () => {
    if (rejectRegister) {
      throw createError({ statusCode: 422, data: { message: 'The email has already been taken.' } })
    }
    return { token: 'bearer-only' }
  },
})
registerEndpoint('/api/login', {
  method: 'POST',
  handler: () => {
    sessionActive = true
    return ''
  },
})
registerEndpoint('/api/user', () => {
  if (!sessionActive) throw createError({ statusCode: 401 })
  return USER
})

async function fillAndSubmit(c: Awaited<ReturnType<typeof mountSuspended>>) {
  await c.find('input[name="name"]').setValue('Ana')
  await c.find('input[type="email"]').setValue(USER.email)
  await c.find('input[name="password"]').setValue('secret123')
  await c.find('input[name="password_confirmation"]').setValue('secret123')
  await c.find('form').trigger('submit.prevent')
  await flushPromises()
}

describe('RegisterForm', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionActive = false
    rejectRegister = false
    navigateToMock.mockClear()
  })

  it('registers, auto-logs-in and navigates home', async () => {
    const c = await mountSuspended(RegisterForm)
    await fillAndSubmit(c)
    await vi.waitFor(() => expect(navigateToMock).toHaveBeenCalledWith('/'))
  })

  it('shows the API error message on 422 and stays', async () => {
    rejectRegister = true
    const c = await mountSuspended(RegisterForm)
    await fillAndSubmit(c)
    await vi.waitFor(() => expect(c.text()).toContain('The email has already been taken.'))
    expect(navigateToMock).not.toHaveBeenCalled()
  })

  it('links to the login page', async () => {
    const c = await mountSuspended(RegisterForm)
    expect(c.find('a[href="/login"]').exists()).toBe(true)
  })
})
