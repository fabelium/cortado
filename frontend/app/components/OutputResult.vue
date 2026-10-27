<script setup lang="ts">
import { computed } from 'vue'
import type { GeneratableOutput, Artifact, Transcript, BookArtifact } from '~~/shared/types/outputs'

const props = defineProps<{
  kind: GeneratableOutput
  status: 'idle' | 'running' | 'done' | 'error'
  progress: number
  result: Artifact[] | Transcript[] | BookArtifact[] | null
  error: string | null
}>()
const emit = defineEmits<{ retry: [] }>()

const LABELS: Record<GeneratableOutput, string> = {
  audio: 'Audio',
  transcript: 'Transcripción',
  book: 'Librito',
}

const artifacts = computed(() => (props.kind === 'audio' ? (props.result as Artifact[] | null) ?? [] : []))
const transcripts = computed(() => (props.kind === 'transcript' ? (props.result as Transcript[] | null) ?? [] : []))
const bookArtifacts = computed(() => (props.kind === 'book' ? (props.result as BookArtifact[] | null) ?? [] : []))
</script>

<template>
  <div class="space-y-2">
    <p class="text-sm font-medium">{{ LABELS[kind] }}</p>

    <template v-if="status === 'running'">
      <p class="text-sm text-(--ui-text-muted)">Preparando…</p>
      <UProgress :model-value="progress" :max="100" />
    </template>

    <div v-else-if="status === 'error'" class="space-y-2">
      <UAlert color="error" icon="i-lucide-triangle-alert" :title="error ?? 'No se pudo preparar.'" />
      <UButton variant="outline" size="sm" @click="emit('retry')">Reintentar</UButton>
    </div>

    <template v-else-if="status === 'done'">
      <ul v-if="kind === 'audio'" class="text-sm space-y-1">
        <li v-for="a in artifacts" :key="a.path" class="font-mono">{{ a.path }}</li>
      </ul>
      <ul v-else-if="kind === 'transcript'" class="text-sm space-y-1">
        <li v-for="t in transcripts" :key="t.source" class="font-mono">{{ t.txt }} · {{ t.srt }}</li>
      </ul>
      <ul v-else-if="kind === 'book'" class="text-sm space-y-1">
        <li v-for="a in bookArtifacts" :key="a.path" class="font-mono">{{ a.path }} · {{ a.format }}</li>
      </ul>
    </template>
  </div>
</template>
