import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { registerEndpoint } from '@nuxt/test-utils/runtime'
import { useCurationStore } from '~/stores/curation'
import type { Fragment } from '~~/shared/types/search'

const A: Fragment = { id: 'a', episode: 1, date: '2020-01-01', start: 0, end: 10, duration: 10, name: 'A', score: 0.9, reason: 'ra' }
const B: Fragment = { id: 'b', episode: 2, date: '2020-02-02', start: 0, end: 20, duration: 20, name: 'B', score: 0.8, reason: 'rb' }

registerEndpoint('/api/search', {
  method: 'POST',
  handler: () => ({ ok: true, fragments: [A, B] }),
})

describe('curation store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('search() fills suggestions and resets selection', async () => {
    const s = useCurationStore()
    await s.search('x')
    expect(s.suggestions).toHaveLength(2)
    expect(s.selectedIds).toEqual([])
    expect(s.status).toBe('idle')
  })

  it('toggleInclude adds then removes an id', () => {
    const s = useCurationStore()
    s.suggestions = [A]
    s.toggleInclude('a')
    expect(s.selectedIds).toEqual(['a'])
    s.toggleInclude('a')
    expect(s.selectedIds).toEqual([])
  })

  it('reorder moves an id within the selection', () => {
    const s = useCurationStore()
    s.selectedIds = ['a', 'b', 'c']
    s.reorder(0, 2)
    expect(s.selectedIds).toEqual(['b', 'c', 'a'])
  })

  it('selectedFragments returns the included fragments in order', async () => {
    const s = useCurationStore()
    await s.search('x')
    s.toggleInclude('b')
    s.toggleInclude('a')
    expect(s.selectedFragments.map(f => f.id)).toEqual(['b', 'a'])
    expect(s.selectedCount).toBe(2)
  })
})
