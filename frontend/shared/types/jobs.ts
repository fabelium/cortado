// Queued engine actions (generate/transcribe/book) per contract/openapi/openapi.yaml:
// POST answers 202 with a job ref; poll GET /api/jobs/{id} for the outcome.
export type JobAction = 'generate' | 'transcribe' | 'book'
export type JobStatus = 'queued' | 'running' | 'done' | 'failed'

// Shape of the 202 acceptance payload.
export interface JobRef {
  id: string
  action: JobAction
  status: 'queued'
}
export interface JobAcceptedResponse {
  ok: boolean
  job: JobRef
}

// Full job state from the polling endpoint; `result` is the engine contract
// response on done (e.g. artifacts/transcripts), `error`/`code` on failed.
export interface Job<TResult = unknown> {
  id: string
  action: JobAction
  status: JobStatus
  result: TResult | null
  error: string | null
  code: number | null
}
export interface JobEnvelope<TResult = unknown> {
  ok: boolean
  job: Job<TResult>
}
