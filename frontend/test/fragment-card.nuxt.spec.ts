import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import FragmentCard from '~/components/FragmentCard.vue'
import type { Fragment } from '~~/shared/types/search'

const fragment: Fragment = {
  id: 'ep1@0-540', episode: 237, date: '2019-10-17', start: 0, end: 540,
  duration: 540, name: 'Black holes', score: 0.71, reason: 'About black holes.',
}

describe('FragmentCard', () => {
  it('renders the fragment fields', async () => {
    const c = await mountSuspended(FragmentCard, { props: { fragment, included: false } })
    expect(c.text()).toContain('Black holes')
    expect(c.text()).toContain('237')
    expect(c.text()).toContain('9:00')
    expect(c.text()).toContain('About black holes.')
  })

  it('emits toggle with the id when the button is clicked', async () => {
    const c = await mountSuspended(FragmentCard, { props: { fragment, included: false } })
    await c.find('button').trigger('click')
    expect(c.emitted('toggle')).toBeTruthy()
    expect(c.emitted('toggle')![0]).toEqual(['ep1@0-540'])
  })

  it('labels the toggle in Spanish for both states', async () => {
    const off = await mountSuspended(FragmentCard, { props: { fragment, included: false } })
    expect(off.text()).toContain('Incluir')
    const on = await mountSuspended(FragmentCard, { props: { fragment, included: true } })
    expect(on.text()).toContain('Incluida')
  })

  it('degrades gracefully when score, reason, and duration are null', async () => {
    const nullFragment: Fragment = {
      id: 'ep2@0-0', episode: 1, date: '2020-01-01', start: 0, end: 0,
      duration: null, name: 'Null fields', score: null, reason: null,
    }
    const c = await mountSuspended(FragmentCard, { props: { fragment: nullFragment, included: false } })
    // mount must succeed — no crash
    expect(c.exists()).toBe(true)
    // formatDuration(null) renders the em-dash
    expect(c.text()).toContain('—')
    // no score decimal visible (badge absent)
    expect(c.text()).not.toContain('0.')
    // reason paragraph absent
    expect(c.text()).not.toContain('null')
  })
})
