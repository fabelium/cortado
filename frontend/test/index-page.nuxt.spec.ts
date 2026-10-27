import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mountSuspended, registerEndpoint } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import IndexPage from '~/pages/index.vue'

registerEndpoint('/api/search', {
  method: 'POST',
  handler: () => ({
    ok: true,
    fragments: [
      { id: 'a', episode: 1, date: '2020-01-01', start: 0, end: 10, duration: 10, name: 'Black holes 101', score: 0.7, reason: 'r' },
    ],
  }),
})

describe('index page', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders the brand header, the intro and the guided panels', async () => {
    const c = await mountSuspended(IndexPage)
    expect(c.text()).toContain('Un cortado, por favor')
    expect(c.text()).toContain('Tu recopilación de')
    expect(c.text()).toContain('recién hecha')
    expect(c.text()).toContain('Aún no hay sugerencias')
    // Numbered badges live inside the panel headings now.
    const curationHeading = c.findAll('h2').find(h => h.text().includes('Elige los fragmentos'))
    expect(curationHeading!.text()).toContain('2')
    const outputsHeading = c.findAll('h2').find(h => h.text().includes('Sirve tu cortado'))
    expect(outputsHeading!.text()).toContain('3')
  })

  it('searches and shows a suggestion, then includes it', async () => {
    const c = await mountSuspended(IndexPage)
    await c.find('input').setValue('black holes')
    await c.find('form').trigger('submit.prevent')
    // The mock fetch transport resolves on macrotasks — poll instead of one flush.
    await vi.waitFor(() => expect(c.text()).toContain('Black holes 101'))

    // Include the suggestion (the first "Include" button in the suggestions list).
    const includeBtn = c.findAll('button').find(b => b.text().includes('Incluir'))
    expect(includeBtn).toBeTruthy()
    await includeBtn!.trigger('click')
    await flushPromises()
    expect(c.text()).toContain('Tu selección (1)')
    // Only the numbered steps are h2; the selection is a sub-part of step 2.
    expect(c.findAll('h2').some(h => h.text().includes('Tu selección'))).toBe(false)
  })

  it('renders the production column (outputs + chat)', async () => {
    const c = await mountSuspended(IndexPage)
    expect(c.text()).toContain('Sirve tu cortado')
    expect(c.text()).toContain('Charla con tu selección')
  })
})
