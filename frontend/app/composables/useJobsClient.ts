import type { Job, JobEnvelope } from '~~/shared/types/jobs'

export interface PollOptions {
  intervalMs?: number
  timeoutMs?: number
}

const DEFAULT_INTERVAL_MS = 1500
// Generous ceiling: whisper over long audio is slow, but a job stuck beyond
// this is effectively lost — surface it instead of polling forever.
const DEFAULT_TIMEOUT_MS = 30 * 60 * 1000

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function useJobsClient() {
  const { $api } = useNuxtApp()

  async function getJob<TResult = unknown>(id: string): Promise<Job<TResult>> {
    const res = await $api<JobEnvelope<TResult>>(`/jobs/${id}`)
    return res.job
  }

  async function pollJob<TResult = unknown>(id: string, options: PollOptions = {}): Promise<TResult> {
    const intervalMs = options.intervalMs ?? DEFAULT_INTERVAL_MS
    const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
    const deadline = Date.now() + timeoutMs

    for (;;) {
      const job = await getJob<TResult>(id)
      if (job.status === 'done' && job.result !== null) return job.result
      if (job.status === 'failed') throw new Error(job.error ?? `Job ${id} failed.`)
      if (Date.now() >= deadline) throw new Error(`Job ${id} timed out after ${timeoutMs}ms.`)
      await sleep(intervalMs)
    }
  }

  return { getJob, pollJob }
}
