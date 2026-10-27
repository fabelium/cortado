// Output taxonomy. Audio/transcript/book are produced by the Generate flow;
// chat is a separate interactive panel.
export type GeneratableOutput = 'audio' | 'transcript' | 'book'
export type OutputKind = GeneratableOutput | 'chat'

// --- Frozen contract: generate (audio) ---
// Source of truth: contract/schema/response.generate.schema.json
export interface AudioOptions {
  intro: boolean
  disclaimer: boolean
  split: number | null
}
export interface Artifact {
  path: string
  duration: number | null
  size_bytes: number | null
}
// Consumer type: version/action stripped (the Laravel API returns only the payload).
export interface GenerateResponse {
  ok: boolean
  artifacts: Artifact[]
}

// --- Frozen contract: transcribe ---
// Source of truth: contract/schema/response.transcribe.schema.json
export interface Transcript {
  source: string
  txt: string
  srt: string
}
export interface TranscribeResponse {
  ok: boolean
  transcripts: Transcript[]
}

// --- Frozen contract: book ---
// Source of truth: contract/schema/response.book.schema.json
export type BookFormat = 'markdown' | 'pdf' | 'epub'
export interface BookArtifact {
  path: string
  format: BookFormat
}
export interface BookResponse {
  ok: boolean
  artifacts: BookArtifact[]
}

// --- Frozen contract: chat ---
// Source of truth: contract/schema/response.chat.schema.json
// RAG over the curated selection (fragment ids).
export interface ChatSource {
  episode: number
  date: string
  topic: string
}
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: ChatSource[]
}
export interface ChatResponse {
  ok: boolean
  answer: string
  sources: ChatSource[]
}
