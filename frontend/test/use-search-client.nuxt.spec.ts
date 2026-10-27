import { describe, it, expect } from 'vitest'
import { registerEndpoint } from '@nuxt/test-utils/runtime'
import { useSearchClient } from '~/composables/useSearchClient'

let searchOk = true
registerEndpoint('/api/search', {
  method: 'POST',
  handler: () => {
    if (!searchOk) return { ok: false, error: 'engine failed', code: 1 }
    return {
      ok: true,
      fragments: [
        { id: 'ep1@0-10', episode: 1, date: '2020-01-01', start: 0, end: 10, duration: 10, name: 'Test fragment', score: 0.5, reason: 'because' },
      ],
    }
  },
})

describe('useSearchClient', () => {
  it('posts the query and returns the search response', async () => {
    searchOk = true
    const { search } = useSearchClient()
    const res = await search('mars')
    expect(res.ok).toBe(true)
    expect(res.fragments).toHaveLength(1)
    expect(res.fragments[0].name).toBe('Test fragment')
  })

  it('rejects an ok:false payload even with HTTP 200', async () => {
    searchOk = false
    const { search } = useSearchClient()
    await expect(search('mars')).rejects.toThrow('engine failed')
  })
})
