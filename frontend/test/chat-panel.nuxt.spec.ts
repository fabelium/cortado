import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mountSuspended, registerEndpoint } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import ChatPanel from '~/components/ChatPanel.vue'
import { useCurationStore } from '~/stores/curation'
import { useGenerationStore } from '~/stores/generation'
import type { Fragment } from '~~/shared/types/search'

const A: Fragment = { id: 'ep1@0-10', episode: 1, date: '2020-01-01', start: 0, end: 10, duration: 10, name: 'A', score: 0.9, reason: 'ra' }

registerEndpoint('/api/chat', { method: 'POST', handler: () => ({ ok: true, answer: 'pong', sources: [{ episode: 1, date: '2020-01-01', topic: 'astrofísica' }] }) })

describe('ChatPanel', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('prompts to curate when the selection is empty', async () => {
    const c = await mountSuspended(ChatPanel)
    expect(c.text()).toContain('Cuando tengas fragmentos elegidos')
  })

  it('shows no input form when the selection is empty', async () => {
    const c = await mountSuspended(ChatPanel)
    expect(c.text()).toContain('Cuando tengas fragmentos elegidos')
    expect(c.find('form').exists()).toBe(false)
  })

  it('sends a message and shows the assistant answer', async () => {
    const c = await mountSuspended(ChatPanel)
    const cur = useCurationStore()
    cur.suggestions = [A]
    cur.toggleInclude('ep1@0-10')
    await flushPromises()
    await c.find('input').setValue('ping')
    await c.find('form').trigger('submit.prevent')
    // The mock fetch transport resolves on macrotasks — poll instead of one flush.
    await vi.waitFor(() => expect(c.text()).toContain('pong'))
    expect(c.text()).toContain('ping')
    // Contract sources are {episode, date, topic} objects — render episode + topic.
    expect(c.text()).toContain('Ep. 1')
    expect(c.text()).toContain('astrofísica')
  })

  it('ignores submit while already sending', async () => {
    const c = await mountSuspended(ChatPanel)
    const cur = useCurationStore()
    cur.suggestions = [A]
    cur.toggleInclude('ep1@0-10')
    await flushPromises()
    const g = useGenerationStore()
    g.chat.status = 'sending'
    await c.find('input').setValue('ping')
    await c.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(g.chat.messages).toEqual([])
  })

  it('does not send a blank message', async () => {
    const c = await mountSuspended(ChatPanel)
    const cur = useCurationStore()
    cur.suggestions = [A]
    cur.toggleInclude('ep1@0-10')
    await flushPromises()
    await c.find('input').setValue('   ')
    await c.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(c.text()).not.toContain('pong')
    const g = useGenerationStore()
    expect(g.chat.messages).toEqual([])
  })
})
