import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import SelectionPanel from '~/components/SelectionPanel.vue'
import type { Fragment } from '~~/shared/types/search'

const frags: Fragment[] = [
  { id: 'a', episode: 1, date: '2020-01-01', start: 0, end: 10, duration: 10, name: 'Alpha', score: 0.5, reason: 'ra' },
  { id: 'b', episode: 2, date: '2020-02-02', start: 0, end: 20, duration: 20, name: 'Beta', score: 0.4, reason: 'rb' },
]

describe('SelectionPanel', () => {
  it('renders the selected fragments in order with a count', async () => {
    const c = await mountSuspended(SelectionPanel, { props: { fragments: frags } })
    expect(c.text()).toContain('Alpha')
    expect(c.text()).toContain('Beta')
    expect(c.text()).toContain('2 elegidos')
  })

  it('shows an empty hint when nothing is selected', async () => {
    const c = await mountSuspended(SelectionPanel, { props: { fragments: [] } })
    expect(c.text()).toContain('Incluye sugerencias')
  })

  it('emits toggle when the remove button is clicked', async () => {
    const c = await mountSuspended(SelectionPanel, { props: { fragments: frags } })
    await c.find('button').trigger('click')
    expect(c.emitted('toggle')![0]).toEqual(['a'])
  })
})
