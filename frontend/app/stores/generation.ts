import { defineStore } from 'pinia'
import { useGenerateClient } from '~/composables/useGenerateClient'
import { useChatClient } from '~/composables/useChatClient'
import { useSimulatedProgress } from '~/composables/useSimulatedProgress'
import { useCurationStore } from '~/stores/curation'
import type {
  GeneratableOutput,
  AudioOptions,
  Artifact,
  Transcript,
  BookArtifact,
  ChatMessage,
} from '~~/shared/types/outputs'

type JobStatus = 'idle' | 'running' | 'done' | 'error'

interface Job {
  status: JobStatus
  progress: number
  result: Artifact[] | Transcript[] | BookArtifact[] | null
  error: string | null
}

function emptyJob(): Job {
  return { status: 'idle', progress: 0, result: null, error: null }
}

// Live progress controllers, tracked so reset() can stop in-flight timers.
const activeProgress = new Set<{ stop: () => void }>()

function trackProgress(onProgress: (p: number) => void) {
  const inner = useSimulatedProgress(onProgress)
  const tracked = {
    start: inner.start,
    stop() {
      inner.stop()
      activeProgress.delete(tracked)
    },
    finish() {
      inner.finish()
      activeProgress.delete(tracked)
    },
  }
  activeProgress.add(tracked)
  return tracked
}

export const useGenerationStore = defineStore('generation', {
  state: () => ({
    selectedOutputs: [] as GeneratableOutput[],
    audioOptions: { intro: true, disclaimer: true, split: null } as AudioOptions,
    jobs: {
      audio: emptyJob(),
      transcript: emptyJob(),
      book: emptyJob(),
    } as Record<GeneratableOutput, Job>,
    chat: {
      messages: [] as ChatMessage[],
      status: 'idle' as 'idle' | 'sending' | 'error',
      error: null as string | null,
    },
  }),
  getters: {
    canGenerate(state): boolean {
      const curation = useCurationStore()
      return curation.selectedCount > 0 && state.selectedOutputs.length > 0
    },
    isGenerating(state): boolean {
      return Object.values(state.jobs).some(j => j.status === 'running')
    },
  },
  actions: {
    toggleOutput(kind: GeneratableOutput) {
      const i = this.selectedOutputs.indexOf(kind)
      if (i === -1) this.selectedOutputs.push(kind)
      else this.selectedOutputs.splice(i, 1)
    },
    async generate() {
      if (this.isGenerating) return
      const curation = useCurationStore()
      const selection = curation.selectedFragments.map(f => f.id)
      if (!selection.length || !this.selectedOutputs.length) return

      const query = curation.query
      const wantsAudio = this.selectedOutputs.includes('audio')
      const wantsTranscript = this.selectedOutputs.includes('transcript')
      const wantsBook = this.selectedOutputs.includes('book')

      const tasks: Promise<void>[] = []
      if (wantsAudio || wantsTranscript) {
        tasks.push(this.runAudioChain(query, selection, wantsAudio, wantsTranscript))
      }
      if (wantsBook) tasks.push(this.runBook(query, selection))
      await Promise.all(tasks)
    },
    async retryOutput(kind: GeneratableOutput) {
      if (this.jobs[kind].status === 'running') return
      const curation = useCurationStore()
      const selection = curation.selectedFragments.map(f => f.id)
      if (!selection.length) return
      const query = curation.query

      if (kind === 'book') {
        await this.runBook(query, selection)
        return
      }
      if (kind === 'audio') {
        await this.runAudioChain(query, selection, true, false)
        return
      }
      // Transcript: reuse the audio already produced; rebuild the chain otherwise.
      const audioPaths = ((this.jobs.audio.result as Artifact[] | null) ?? []).map(a => a.path)
      if (audioPaths.length) {
        await this.runTranscribe(audioPaths)
        return
      }
      await this.runAudioChain(query, selection, this.selectedOutputs.includes('audio'), true)
    },
    // Audio first; transcript chains on the produced audio paths.
    async runAudioChain(query: string, selection: string[], wantsAudio: boolean, wantsTranscript: boolean) {
      const { generate } = useGenerateClient()
      const audioProgress = trackProgress(p => (this.jobs.audio.progress = p))
      let audioPaths: string[]
      try {
        this.jobs.audio.status = 'running'
        this.jobs.audio.error = null
        audioProgress.start()
        const res = await generate(query, selection, this.audioOptions)
        audioPaths = res.artifacts.map(a => a.path)
        this.jobs.audio.result = res.artifacts
        audioProgress.finish()
        this.jobs.audio.status = wantsAudio ? 'done' : 'idle'
      }
      catch {
        audioProgress.stop()
        this.jobs.audio.status = 'error'
        this.jobs.audio.error = 'No se pudo preparar el audio.'
        if (wantsTranscript) {
          this.jobs.transcript.status = 'error'
          this.jobs.transcript.error = 'Saltado: falló la preparación del audio.'
        }
        return
      }
      if (wantsTranscript) await this.runTranscribe(audioPaths)
    },
    async runTranscribe(audioPaths: string[]) {
      const { transcribe } = useGenerateClient()
      const progress = trackProgress(p => (this.jobs.transcript.progress = p))
      try {
        this.jobs.transcript.status = 'running'
        this.jobs.transcript.error = null
        progress.start()
        const res = await transcribe(audioPaths)
        this.jobs.transcript.result = res.transcripts
        progress.finish()
        this.jobs.transcript.status = 'done'
      }
      catch {
        progress.stop()
        this.jobs.transcript.status = 'error'
        this.jobs.transcript.error = 'No se pudo transcribir.'
      }
    },
    async runBook(query: string, selection: string[]) {
      const { makeBook } = useGenerateClient()
      const progress = trackProgress(p => (this.jobs.book.progress = p))
      try {
        this.jobs.book.status = 'running'
        this.jobs.book.error = null
        progress.start()
        const res = await makeBook(query, selection)
        this.jobs.book.result = res.artifacts
        progress.finish()
        this.jobs.book.status = 'done'
      }
      catch {
        progress.stop()
        this.jobs.book.status = 'error'
        this.jobs.book.error = 'No se pudo preparar el librito.'
      }
    },
    async sendChatMessage(text: string) {
      const message = text.trim()
      if (!message) return
      const curation = useCurationStore()
      const selection = curation.selectedFragments.map(f => f.id)
      this.chat.messages.push({ role: 'user', content: message })
      this.chat.status = 'sending'
      this.chat.error = null
      try {
        const { sendMessage } = useChatClient()
        const res = await sendMessage(selection, message)
        this.chat.messages.push({ role: 'assistant', content: res.answer, sources: res.sources })
        this.chat.status = 'idle'
      }
      catch {
        this.chat.status = 'error'
        this.chat.error = 'No se pudo enviar. Vuelve a intentarlo.'
      }
    },
    reset() {
      for (const progress of [...activeProgress]) progress.stop()
      this.selectedOutputs = []
      this.jobs = { audio: emptyJob(), transcript: emptyJob(), book: emptyJob() }
      this.chat = { messages: [], status: 'idle', error: null }
    },
  },
})
