import { describe, it, expect, beforeEach } from 'vitest'
import { registerEndpoint } from '@nuxt/test-utils/runtime'
import { useJobsClient } from '~/composables/useJobsClient'

// Job state machine per contract/openapi/openapi.yaml: queued|running|done|failed.
let polls = 0
let sequence: Array<{ status: string, result?: object | null, error?: string | null, code?: number | null }> = []

registerEndpoint('/api/jobs/job-1', () => {
  const step = sequence[Math.min(polls, sequence.length - 1)]!
  polls++
  return {
    ok: true,
    job: {
      id: 'job-1',
      action: 'generate',
      status: step.status,
      result: step.result ?? null,
      error: step.error ?? null,
      code: step.code ?? null,
    },
  }
})

describe('useJobsClient', () => {
  beforeEach(() => {
    polls = 0
    sequence = []
  })

  it('getJob returns the job envelope', async () => {
    sequence = [{ status: 'queued' }]
    const { getJob } = useJobsClient()
    const job = await getJob('job-1')
    expect(job.id).toBe('job-1')
    expect(job.status).toBe('queued')
  })

  it('pollJob polls until done and returns the result', async () => {
    sequence = [
      { status: 'queued' },
      { status: 'running' },
      { status: 'done', result: { ok: true, artifacts: [{ path: 'a.mp3' }] } },
    ]
    const { pollJob } = useJobsClient()
    const result = await pollJob<{ ok: boolean, artifacts: { path: string }[] }>('job-1', { intervalMs: 1 })
    expect(polls).toBe(3)
    expect(result.artifacts[0]!.path).toBe('a.mp3')
  })

  it('pollJob throws the job error on failed', async () => {
    sequence = [
      { status: 'running' },
      { status: 'failed', error: 'engine exploded', code: 1 },
    ]
    const { pollJob } = useJobsClient()
    await expect(pollJob('job-1', { intervalMs: 1 })).rejects.toThrow('engine exploded')
  })

  it('pollJob gives up after timeoutMs', async () => {
    sequence = [{ status: 'running' }]
    const { pollJob } = useJobsClient()
    await expect(pollJob('job-1', { intervalMs: 5, timeoutMs: 20 })).rejects.toThrow(/timed out/i)
  })
})
