import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { mountSuspended, registerEndpoint } from '@nuxt/test-utils/runtime'
import { flushPromises } from '@vue/test-utils'
import OutputsPanel from '~/components/OutputsPanel.vue'
import { useCurationStore } from '~/stores/curation'
import { useGenerationStore } from '~/stores/generation'
import type { Fragment } from '~~/shared/types/search'

const A: Fragment = { id: 'ep1@0-10', episode: 1, date: '2020-01-01', start: 0, end: 10, duration: 10, name: 'A', score: 0.9, reason: 'ra' }

// Queued action: 202 + job ref, then the client polls /jobs/{id}.
registerEndpoint('/api/generate', { method: 'POST', handler: () => ({ ok: true, job: { id: 'job-gen', action: 'generate', status: 'queued' } }) })
registerEndpoint('/api/jobs/job-gen', () => ({
  ok: true,
  job: { id: 'job-gen', action: 'generate', status: 'done', result: { ok: true, artifacts: [{ path: 'output/a.mp3', duration: 10, size_bytes: 100 }] }, error: null, code: null },
}))

describe('OutputsPanel', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('disables Generate until an output is picked with a curated selection', async () => {
    const c = await mountSuspended(OutputsPanel)
    const cur = useCurationStore()
    cur.suggestions = [A]
    cur.toggleInclude('ep1@0-10')
    await flushPromises()
    const genBtn = () => c.findAll('button').find(b => b.text().includes('Preparar'))!
    expect(genBtn().attributes('disabled')).toBeDefined()

    const audioToggle = c.findAll('button').find(b => b.text().includes('Audio'))!
    await audioToggle.trigger('click')
    await flushPromises()
    expect(genBtn().attributes('disabled')).toBeUndefined()
  })

  it('exposes the selected state of each output toggle to assistive tech', async () => {
    const c = await mountSuspended(OutputsPanel)
    const audio = () => c.findAll('button').find(b => b.text().includes('Audio'))!
    expect(audio().attributes('aria-pressed')).toBe('false')
    await audio().trigger('click')
    await flushPromises()
    expect(audio().attributes('aria-pressed')).toBe('true')
  })

  it('Retry re-runs only the failed output', async () => {
    const c = await mountSuspended(OutputsPanel)
    const cur = useCurationStore()
    cur.suggestions = [A]
    cur.toggleInclude('ep1@0-10')
    const g = useGenerationStore()
    g.toggleOutput('book')
    g.jobs.book.status = 'error'
    g.jobs.book.error = 'Book generation failed.'
    const retrySpy = vi.spyOn(g, 'retryOutput').mockResolvedValue()
    await flushPromises()
    const retry = c.findAll('button').find(b => b.text().includes('Reintentar'))!
    await retry.trigger('click')
    expect(retrySpy).toHaveBeenCalledWith('book')
  })

  it('runs generation and shows the audio artifact', async () => {
    const c = await mountSuspended(OutputsPanel)
    const cur = useCurationStore()
    cur.suggestions = [A]
    cur.query = 'topic'
    cur.toggleInclude('ep1@0-10')
    const g = useGenerationStore()
    g.toggleOutput('audio')
    await flushPromises()
    await c.findAll('button').find(b => b.text().includes('Preparar'))!.trigger('click')
    // The mock fetch transport resolves on macrotasks — poll instead of one flush.
    await vi.waitFor(() => expect(c.text()).toContain('output/a.mp3'))
  })
})
