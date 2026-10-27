<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useGenerationStore } from '~/stores/generation'
import type { GeneratableOutput } from '~~/shared/types/outputs'

const gen = useGenerationStore()
const { selectedOutputs, audioOptions, jobs, canGenerate, isGenerating } = storeToRefs(gen)

const OUTPUTS: { kind: GeneratableOutput, label: string, help: string }[] = [
  { kind: 'audio', label: 'Audio', help: 'Un MP3 con tus fragmentos hilados (la intro hablada es opcional).' },
  { kind: 'transcript', label: 'Transcripción', help: 'El texto y los subtítulos del audio generado.' },
  { kind: 'book', label: 'Librito', help: 'Un librito con capítulos a partir de tus fragmentos.' },
]

const showAudioOptions = computed(() =>
  selectedOutputs.value.includes('audio') || selectedOutputs.value.includes('transcript'),
)
</script>

<template>
  <UCard :ui="{ root: 'border-t-[3px] border-t-primary' }">
    <template #header>
      <StepHeading :step="3" accent title="Sirve tu cortado" subtitle="Elige formato y dale a Preparar." />
    </template>

    <div class="space-y-4">
      <div class="flex flex-wrap gap-2">
        <UTooltip v-for="o in OUTPUTS" :key="o.kind" :text="o.help">
          <UButton
            :color="selectedOutputs.includes(o.kind) ? 'primary' : 'neutral'"
            :variant="selectedOutputs.includes(o.kind) ? 'solid' : 'outline'"
            :aria-pressed="selectedOutputs.includes(o.kind)"
            size="sm"
            @click="gen.toggleOutput(o.kind)"
          >
            {{ o.label }}
          </UButton>
        </UTooltip>
      </div>

      <AudioOptions
        v-if="showAudioOptions"
        :intro="audioOptions.intro"
        :disclaimer="audioOptions.disclaimer"
        :split="audioOptions.split"
        @update:intro="(v) => (audioOptions.intro = v)"
        @update:disclaimer="(v) => (audioOptions.disclaimer = v)"
        @update:split="(v) => (audioOptions.split = v)"
      />

      <UButton
        :disabled="!canGenerate"
        :loading="isGenerating"
        icon="i-lucide-wand-sparkles"
        @click="gen.generate()"
      >
        Preparar
      </UButton>

      <p v-if="!canGenerate" class="text-sm text-(--ui-text-muted)">
        Elige al menos un formato y algún fragmento para servir.
      </p>

      <div class="space-y-4">
        <OutputResult
          v-for="o in OUTPUTS.filter(x => selectedOutputs.includes(x.kind) && jobs[x.kind].status !== 'idle')"
          :key="o.kind"
          :kind="o.kind"
          :status="jobs[o.kind].status"
          :progress="jobs[o.kind].progress"
          :result="jobs[o.kind].result"
          :error="jobs[o.kind].error"
          @retry="gen.retryOutput(o.kind)"
        />
      </div>
    </div>
  </UCard>
</template>
