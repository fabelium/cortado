import { describe, it, expect } from 'vitest'
import { readBody } from 'h3'
import { registerEndpoint } from '@nuxt/test-utils/runtime'
import { useGenerateClient } from '~/composables/useGenerateClient'
import { useChatClient } from '~/composables/useChatClient'

// Queued actions answer 202 with a job ref; the client polls /jobs/{id}.
registerEndpoint('/api/generate', {
  method: 'POST',
  handler: () => ({ ok: true, job: { id: 'job-gen', action: 'generate', status: 'queued' } }),
})
registerEndpoint('/api/transcribe', {
  method: 'POST',
  handler: () => ({ ok: true, job: { id: 'job-tr', action: 'transcribe', status: 'queued' } }),
})
registerEndpoint('/api/book', {
  method: 'POST',
  handler: () => ({ ok: true, job: { id: 'job-book', action: 'book', status: 'queued' } }),
})
registerEndpoint('/api/jobs/job-gen', () => ({
  ok: true,
  job: {
    id: 'job-gen',
    action: 'generate',
    status: 'done',
    result: { ok: true, artifacts: [{ path: 'output/x.mp3', duration: 10, size_bytes: 100 }] },
    error: null,
    code: null,
  },
}))
registerEndpoint('/api/jobs/job-tr', () => ({
  ok: true,
  job: {
    id: 'job-tr',
    action: 'transcribe',
    status: 'done',
    result: { ok: true, transcripts: [{ source: 'output/x.mp3', txt: 'output/x.txt', srt: 'output/x.srt' }] },
    error: null,
    code: null,
  },
}))
registerEndpoint('/api/jobs/job-book', () => ({
  ok: true,
  job: {
    id: 'job-book',
    action: 'book',
    status: 'failed',
    result: null,
    error: 'pandoc unavailable',
    code: 1,
  },
}))

let chatOk = true
let chatBody: Record<string, unknown> | undefined
registerEndpoint('/api/chat', {
  method: 'POST',
  handler: async (event) => {
    chatBody = await readBody(event)
    if (!chatOk) return { ok: false, error: 'engine failed', code: 1 }
    return { ok: true, answer: 'hi', sources: [{ episode: 1, date: '2020-01-01', topic: 'a' }] }
  },
})

describe('output clients', () => {
  it('generate queues a job and resolves with the polled artifacts', async () => {
    const { generate } = useGenerateClient()
    const res = await generate('q', ['a'], { intro: true, disclaimer: true, split: null })
    expect(res.artifacts[0]!.path).toBe('output/x.mp3')
  })

  it('transcribe queues a job and resolves with the polled transcripts', async () => {
    const { transcribe } = useGenerateClient()
    const res = await transcribe(['output/x.mp3'])
    expect(res.transcripts[0]!.txt).toBe('output/x.txt')
  })

  it('makeBook surfaces the job error when the job fails', async () => {
    const { makeBook } = useGenerateClient()
    await expect(makeBook('q', ['a'])).rejects.toThrow('pandoc unavailable')
  })

  it('sendMessage posts the contract body {query, selection} and returns answer + sources', async () => {
    chatOk = true
    const { sendMessage } = useChatClient()
    const res = await sendMessage(['a'], 'hello')
    expect(chatBody).toEqual({ query: 'hello', selection: ['a'] })
    expect(res.answer).toBe('hi')
    expect(res.sources).toEqual([{ episode: 1, date: '2020-01-01', topic: 'a' }])
  })

  it('sendMessage rejects an ok:false payload even with HTTP 200', async () => {
    chatOk = false
    const { sendMessage } = useChatClient()
    await expect(sendMessage(['a'], 'hello')).rejects.toThrow('engine failed')
  })
})
