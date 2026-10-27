import { describe, it, expect } from 'vitest'
import { registerEndpoint } from '@nuxt/test-utils/runtime'
import { apiOrigin, ensureCsrf } from '~/utils/csrf'

describe('csrf helper', () => {
  it('apiOrigin strips a trailing /api from apiBase', () => {
    expect(apiOrigin('http://localhost:8000/api')).toBe('http://localhost:8000')
    expect(apiOrigin('http://localhost:8000/api/')).toBe('http://localhost:8000')
    expect(apiOrigin('/api')).toBe('')
  })

  it('ensureCsrf requests the sanctum csrf-cookie endpoint with credentials', async () => {
    let hits = 0
    registerEndpoint('/sanctum/csrf-cookie', () => {
      hits++
      return ''
    })
    await ensureCsrf('/api')
    expect(hits).toBe(1)
  })
})
