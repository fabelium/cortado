import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import SuggestionList from '~/components/SuggestionList.vue'
import FragmentCard from '~/components/FragmentCard.vue'
import type { Fragment } from '~~/shared/types/search'

const frags: Fragment[] = [
  { id: 'a', episode: 1, date: '2020-01-01', start: 0, end: 10, duration: 10, name: 'A', score: 0.5, reason: 'ra' },
  { id: 'b', episode: 2, date: '2020-02-02', start: 0, end: 20, duration: 20, name: 'B', score: 0.4, reason: 'rb' },
]

describe('SuggestionList', () => {
  it('renders a card per suggestion when idle', async () => {
    const c = await mountSuspended(SuggestionList, {
      props: { suggestions: frags, status: 'idle', selectedIds: [] },
    })
    expect(c.findAllComponents(FragmentCard)).toHaveLength(2)
  })

  it('shows an empty hint when there are no suggestions', async () => {
    const c = await mountSuspended(SuggestionList, {
      props: { suggestions: [], status: 'idle', selectedIds: [] },
    })
    expect(c.text()).toContain('Aún no hay sugerencias')
    expect(c.findAllComponents(FragmentCard)).toHaveLength(0)
  })

  it('bubbles toggle from a card', async () => {
    const c = await mountSuspended(SuggestionList, {
      props: { suggestions: frags, status: 'idle', selectedIds: [] },
    })
    await c.findComponent(FragmentCard).find('button').trigger('click')
    expect(c.emitted('toggle')![0]).toEqual(['a'])
  })

  it('shows a retry button in error state and emits retry on click', async () => {
    const c = await mountSuspended(SuggestionList, {
      props: { suggestions: [], status: 'error', selectedIds: [] },
    })
    const retryBtn = c.find('button')
    expect(retryBtn.exists()).toBe(true)
    expect(retryBtn.text()).toContain('Reintentar')
    await retryBtn.trigger('click')
    expect(c.emitted('retry')).toBeTruthy()
  })
})
