import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import OutputResult from '~/components/OutputResult.vue'

describe('OutputResult', () => {
  it('shows the audio artifact path when done', async () => {
    const c = await mountSuspended(OutputResult, {
      props: { kind: 'audio', status: 'done', progress: 100, error: null, result: [{ path: 'output/a.mp3', duration: 10, size_bytes: 100 }] },
    })
    expect(c.text()).toContain('output/a.mp3')
  })

  it('shows the book artifact paths and formats when done', async () => {
    const c = await mountSuspended(OutputResult, {
      props: { kind: 'book', status: 'done', progress: 100, error: null, result: [{ path: 'output/b.md', format: 'markdown' as const }] },
    })
    expect(c.text()).toContain('output/b.md')
    expect(c.text()).toContain('markdown')
  })

  it('labels the running state in Spanish', async () => {
    const c = await mountSuspended(OutputResult, {
      props: { kind: 'audio', status: 'running', progress: 40, error: null, result: null },
    })
    expect(c.text()).toContain('Preparando…')
  })

  it('shows an error and a retry button when failed', async () => {
    const c = await mountSuspended(OutputResult, {
      props: { kind: 'book', status: 'error', progress: 0, error: 'Book generation failed.', result: null },
    })
    expect(c.text()).toContain('Book generation failed.')
    const retry = c.findAll('button').find(b => b.text().includes('Reintentar'))
    expect(retry).toBeTruthy()
    await retry!.trigger('click')
    expect(c.emitted('retry')).toBeTruthy()
  })
})
