import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { registerEndpoint } from '@nuxt/test-utils/runtime'
import { useGenerationStore } from '~/stores/generation'
import { useCurationStore } from '~/stores/curation'
import * as genClient from '~/composables/useGenerateClient'
import * as chatClient from '~/composables/useChatClient'
import type { Fragment } from '~~/shared/types/search'

const A: Fragment = { id: 'ep1@0-10', episode: 1, date: '2020-01-01', start: 0, end: 10, duration: 10, name: 'A', score: 0.9, reason: 'ra' }

// Queued actions answer 202 with a job ref; the client polls /jobs/{id}.
function acceptJob(id: string, action: string) {
  return { ok: true, job: { id, action, status: 'queued' } }
}
function doneJob(id: string, action: string, result: object) {
  return { ok: true, job: { id, action, status: 'done', result, error: null, code: null } }
}
registerEndpoint('/api/generate', { method: 'POST', handler: () => acceptJob('job-gen', 'generate') })
registerEndpoint('/api/transcribe', { method: 'POST', handler: () => acceptJob('job-tr', 'transcribe') })
registerEndpoint('/api/book', { method: 'POST', handler: () => acceptJob('job-book', 'book') })
registerEndpoint('/api/jobs/job-gen', () => doneJob('job-gen', 'generate', { ok: true, artifacts: [{ path: 'output/a.mp3', duration: 10, size_bytes: 100 }] }))
registerEndpoint('/api/jobs/job-tr', () => doneJob('job-tr', 'transcribe', { ok: true, transcripts: [{ source: 'output/a.mp3', txt: 'output/a.txt', srt: 'output/a.srt' }] }))
registerEndpoint('/api/jobs/job-book', () => doneJob('job-book', 'book', { ok: true, artifacts: [{ path: 'output/b.md', format: 'markdown' }] }))
registerEndpoint('/api/chat', { method: 'POST', handler: () => ({ ok: true, answer: 'pong', sources: [{ episode: 1, date: '2020-01-01', topic: 'A' }] }) })

function withSelection() {
  const cur = useCurationStore()
  cur.suggestions = [A]
  cur.query = 'topic'
  cur.toggleInclude('ep1@0-10')
}

describe('generation store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('toggleOutput adds then removes an output', () => {
    const g = useGenerationStore()
    g.toggleOutput('audio')
    expect(g.selectedOutputs).toEqual(['audio'])
    g.toggleOutput('audio')
    expect(g.selectedOutputs).toEqual([])
  })

  it('canGenerate requires a curated selection and at least one output', () => {
    const g = useGenerationStore()
    expect(g.canGenerate).toBe(false)
    withSelection()
    expect(g.canGenerate).toBe(false)
    g.toggleOutput('audio')
    expect(g.canGenerate).toBe(true)
  })

  it('generate() produces audio then chains transcript on the produced path', async () => {
    withSelection()
    const g = useGenerationStore()
    g.toggleOutput('audio')
    g.toggleOutput('transcript')
    await g.generate()
    expect(g.jobs.audio.status).toBe('done')
    expect((g.jobs.audio.result as { path: string }[])[0]!.path).toBe('output/a.mp3')
    expect(g.jobs.transcript.status).toBe('done')
    expect((g.jobs.transcript.result as { txt: string }[])[0]!.txt).toBe('output/a.txt')
    expect(g.jobs.audio.progress).toBe(100)
    expect(g.jobs.transcript.progress).toBe(100)
  })

  it('generate() runs book independently', async () => {
    withSelection()
    const g = useGenerationStore()
    g.toggleOutput('book')
    await g.generate()
    expect(g.jobs.book.status).toBe('done')
    expect((g.jobs.book.result as { path: string, format: string }[])[0]).toEqual({ path: 'output/b.md', format: 'markdown' })
  })

  it('sendChatMessage appends the user message and the assistant answer with sources', async () => {
    withSelection()
    const g = useGenerationStore()
    await g.sendChatMessage('  ping  ')
    expect(g.chat.messages.map(m => m.role)).toEqual(['user', 'assistant'])
    expect(g.chat.messages[0]!.content).toBe('ping')
    expect(g.chat.messages[1]!.content).toBe('pong')
    expect(g.chat.messages[1]!.sources).toEqual([{ episode: 1, date: '2020-01-01', topic: 'A' }])
    expect(g.chat.status).toBe('idle')
  })

  it('sendChatMessage ignores blank input', async () => {
    const g = useGenerationStore()
    await g.sendChatMessage('   ')
    expect(g.chat.messages).toEqual([])
  })

  it('audio failure marks transcript as skipped', async () => {
    vi.spyOn(genClient, 'useGenerateClient').mockReturnValue({
      generate: () => Promise.reject(new Error('boom')),
      transcribe: () => Promise.resolve({ ok: true, transcripts: [] }),
      makeBook: () => Promise.resolve({ ok: true, artifacts: [{ path: 'b.md', format: 'markdown' as const }] }),
    })
    withSelection()
    const g = useGenerationStore()
    g.toggleOutput('audio')
    g.toggleOutput('transcript')
    await g.generate()
    expect(g.jobs.audio.status).toBe('error')
    expect(g.jobs.transcript.status).toBe('error')
    expect(g.jobs.transcript.error).toBe('Saltado: falló la preparación del audio.')
    vi.restoreAllMocks()
  })

  it('transcript-only selection leaves the audio job idle', async () => {
    withSelection()
    const g = useGenerationStore()
    g.toggleOutput('transcript')
    await g.generate()
    expect(g.jobs.audio.status).toBe('idle')
    expect(g.jobs.transcript.status).toBe('done')
  })

  it('generate() ignores a second call while one is running', async () => {
    let calls = 0
    let release!: () => void
    const gate = new Promise<void>(r => (release = r))
    vi.spyOn(genClient, 'useGenerateClient').mockReturnValue({
      generate: async () => {
        calls++
        await gate
        return { ok: true, artifacts: [{ path: 'a.mp3', duration: 1, size_bytes: 1 }] }
      },
      transcribe: async () => ({ ok: true, transcripts: [] }),
      makeBook: async () => ({ ok: true, artifacts: [] }),
    })
    withSelection()
    const g = useGenerationStore()
    g.toggleOutput('audio')
    const first = g.generate()
    const second = g.generate()
    release()
    await Promise.all([first, second])
    expect(calls).toBe(1)
    vi.restoreAllMocks()
  })

  it('retryOutput("book") re-runs only the failed book', async () => {
    let bookCalls = 0
    let audioCalls = 0
    let failBook = true
    vi.spyOn(genClient, 'useGenerateClient').mockReturnValue({
      generate: async () => {
        audioCalls++
        return { ok: true, artifacts: [{ path: 'a.mp3', duration: 1, size_bytes: 1 }] }
      },
      transcribe: async () => ({ ok: true, transcripts: [] }),
      makeBook: async () => {
        bookCalls++
        if (failBook) throw new Error('boom')
        return { ok: true, artifacts: [{ path: 'b.md', format: 'markdown' as const }] }
      },
    })
    withSelection()
    const g = useGenerationStore()
    g.toggleOutput('audio')
    g.toggleOutput('book')
    await g.generate()
    expect(g.jobs.book.status).toBe('error')
    expect(g.jobs.audio.status).toBe('done')
    failBook = false
    await g.retryOutput('book')
    expect(g.jobs.book.status).toBe('done')
    expect(bookCalls).toBe(2)
    expect(audioCalls).toBe(1)
    vi.restoreAllMocks()
  })

  it('retryOutput("transcript") reuses the produced audio paths', async () => {
    let audioCalls = 0
    let failTranscribe = true
    const transcribeFn = vi.fn(async (selection: string[]) => {
      if (failTranscribe) throw new Error('boom')
      return { ok: true, transcripts: selection.map(s => ({ source: s, txt: 't.txt', srt: 't.srt' })) }
    })
    vi.spyOn(genClient, 'useGenerateClient').mockReturnValue({
      generate: async () => {
        audioCalls++
        return { ok: true, artifacts: [{ path: 'a.mp3', duration: 1, size_bytes: 1 }] }
      },
      transcribe: transcribeFn,
      makeBook: async () => ({ ok: true, artifacts: [] }),
    })
    withSelection()
    const g = useGenerationStore()
    g.toggleOutput('audio')
    g.toggleOutput('transcript')
    await g.generate()
    expect(g.jobs.transcript.status).toBe('error')
    failTranscribe = false
    await g.retryOutput('transcript')
    expect(g.jobs.transcript.status).toBe('done')
    expect(transcribeFn).toHaveBeenLastCalledWith(['a.mp3'])
    expect(audioCalls).toBe(1)
    vi.restoreAllMocks()
  })

  it('reset() stops in-flight progress timers', async () => {
    vi.useFakeTimers()
    vi.spyOn(genClient, 'useGenerateClient').mockReturnValue({
      generate: () => new Promise(() => {}), // never resolves — timers keep ticking
      transcribe: async () => ({ ok: true, transcripts: [] }),
      makeBook: async () => ({ ok: true, artifacts: [] }),
    })
    withSelection()
    const g = useGenerationStore()
    g.toggleOutput('audio')
    void g.generate()
    await vi.advanceTimersByTimeAsync(240)
    expect(g.jobs.audio.progress).toBeGreaterThan(0)
    g.reset()
    await vi.advanceTimersByTimeAsync(600)
    expect(g.jobs.audio.progress).toBe(0)
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('sendChatMessage sets error status when the request fails', async () => {
    vi.spyOn(chatClient, 'useChatClient').mockReturnValue({ sendMessage: () => Promise.reject(new Error('boom')) })
    withSelection()
    const g = useGenerationStore()
    await g.sendChatMessage('ping')
    expect(g.chat.status).toBe('error')
    vi.restoreAllMocks()
  })

  it('sendChatMessage sends the selection and the trimmed query', async () => {
    // Contract body is {query, selection} — no history is sent to the API.
    const sendMessageFn = vi.fn().mockResolvedValue({ ok: true, answer: 'pong', sources: [] })
    vi.spyOn(chatClient, 'useChatClient').mockReturnValue({ sendMessage: sendMessageFn })
    withSelection()
    const g = useGenerationStore()
    await g.sendChatMessage('ping')
    expect(sendMessageFn).toHaveBeenCalledWith(['ep1@0-10'], 'ping')
    vi.restoreAllMocks()
  })
})
