import { describe, it, expect } from 'vitest'
import { registerEndpoint } from '@nuxt/test-utils/runtime'
import { readXsrfCookie, buildApiHeaders } from '~/utils/apiHeaders'

// NOTE: the registerEndpoint in-process transport does not deliver request
// headers to handlers, so the XSRF/cookie wiring is unit-tested on the pure
// header helpers below; the real round-trip is covered by the manual E2E
// against `php artisan serve` (see the auth slice plan, Task 10).
registerEndpoint('/api/ping', { method: 'POST', handler: () => ({ ok: true }) })

describe('api header helpers', () => {
  it('readXsrfCookie extracts and URL-decodes the XSRF-TOKEN cookie', () => {
    expect(readXsrfCookie('XSRF-TOKEN=abc%3D123')).toBe('abc=123')
    expect(readXsrfCookie('other=1; XSRF-TOKEN=tok; more=2')).toBe('tok')
  })

  it('readXsrfCookie returns null when the cookie is absent or empty', () => {
    expect(readXsrfCookie('')).toBeNull()
    expect(readXsrfCookie('other=1')).toBeNull()
    expect(readXsrfCookie('XSRF-TOKEN=')).toBeNull()
  })

  it('buildApiHeaders sets X-XSRF-TOKEN and preserves base headers', () => {
    const h = buildApiHeaders({ accept: 'application/json' }, 'tok', undefined)
    expect(h.get('X-XSRF-TOKEN')).toBe('tok')
    expect(h.get('accept')).toBe('application/json')
  })

  it('buildApiHeaders forwards SSR cookie and referer, skipping absent values', () => {
    // Sanctum only treats requests as stateful when referer/origin matches
    // SANCTUM_STATEFUL_DOMAINS — SSR calls must carry both cookie and referer.
    const ssr = buildApiHeaders(undefined, null, { cookie: 'laravel_session=xyz', referer: 'http://localhost:3000' })
    expect(ssr.get('cookie')).toBe('laravel_session=xyz')
    expect(ssr.get('referer')).toBe('http://localhost:3000')
    expect(ssr.get('X-XSRF-TOKEN')).toBeNull()
    const bare = buildApiHeaders(undefined, null, undefined)
    expect(bare.get('cookie')).toBeNull()
    expect(bare.get('referer')).toBeNull()
  })
})

describe('$api plugin', () => {
  it('provides a working $fetch instance at apiBase', async () => {
    const { $api } = useNuxtApp()
    const res = await $api<{ ok: boolean }>('/ping', { method: 'POST' })
    expect(res.ok).toBe(true)
  })

  // NOTE: nuxtApp.$api is a non-configurable getter, so it cannot be spied
  // on to assert the data clients route through it; that wiring is verified
  // by the existing client tests (behavior unchanged) and the manual E2E,
  // where authenticated calls fail without $api's XSRF handling.
})
