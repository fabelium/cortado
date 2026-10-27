import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import SearchBar from '~/components/SearchBar.vue'

describe('SearchBar', () => {
  it('emits the trimmed query on submit', async () => {
    const c = await mountSuspended(SearchBar)
    await c.find('input').setValue('  black holes  ')
    await c.find('form').trigger('submit.prevent')
    expect(c.emitted('search')).toBeTruthy()
    expect(c.emitted('search')![0]).toEqual(['black holes'])
  })

  it('does not emit when the query is blank', async () => {
    const c = await mountSuspended(SearchBar)
    await c.find('input').setValue('   ')
    await c.find('form').trigger('submit.prevent')
    expect(c.emitted('search')).toBeFalsy()
  })

  it('shows an inline hint on blank/whitespace submit and hides it after a valid submit', async () => {
    const c = await mountSuspended(SearchBar)
    // blank submit → hint visible, no event
    await c.find('input').setValue('   ')
    await c.find('form').trigger('submit.prevent')
    expect(c.text()).toContain('Escribe un tema para buscar.')
    expect(c.emitted('search')).toBeFalsy()
    // valid submit → hint gone, event emitted
    await c.find('input').setValue('black holes')
    await c.find('form').trigger('submit.prevent')
    expect(c.text()).not.toContain('Escribe un tema para buscar.')
    expect(c.emitted('search')).toBeTruthy()
  })
})
