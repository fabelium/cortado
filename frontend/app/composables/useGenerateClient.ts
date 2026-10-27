import type {
  AudioOptions,
  GenerateResponse,
  TranscribeResponse,
  BookResponse,
} from '~~/shared/types/outputs'
import type { JobAcceptedResponse } from '~~/shared/types/jobs'
import { useJobsClient, type PollOptions } from '~/composables/useJobsClient'

// generate/transcribe/book are queued API actions (202 + job); this client
// hides the queue-and-poll round-trip so callers still get the final payload.
export function useGenerateClient(poll: PollOptions = {}) {
  const { $api } = useNuxtApp()
  const { pollJob } = useJobsClient()

  async function runJob<T>(path: string, body: Record<string, unknown>): Promise<T> {
    const accepted = await $api<JobAcceptedResponse>(path, { method: 'POST', body })
    return await pollJob<T>(accepted.job.id, poll)
  }

  async function generate(query: string, selection: string[], options: AudioOptions): Promise<GenerateResponse> {
    return await runJob<GenerateResponse>('/generate', { query, selection, options })
  }

  async function transcribe(selection: string[]): Promise<TranscribeResponse> {
    return await runJob<TranscribeResponse>('/transcribe', { selection })
  }

  async function makeBook(query: string, selection: string[]): Promise<BookResponse> {
    return await runJob<BookResponse>('/book', { query, selection })
  }

  return { generate, transcribe, makeBook }
}
