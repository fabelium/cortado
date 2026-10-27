<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useGenerationStore } from '~/stores/generation'
import { useCurationStore } from '~/stores/curation'

const gen = useGenerationStore()
const curation = useCurationStore()
const { chat } = storeToRefs(gen)
const { selectedCount } = storeToRefs(curation)

const draft = ref('')

async function send() {
  const text = draft.value.trim()
  if (!text || selectedCount.value === 0 || chat.value.status === 'sending') return
  draft.value = ''
  await gen.sendChatMessage(text)
}
</script>

<template>
  <UCard :ui="{ root: 'border-t-[3px] border-t-primary' }">
    <template #header>
      <StepHeading title="Charla con tu selección" subtitle="Pregunta lo que quieras; responde solo con tus fragmentos." />
    </template>

    <p v-if="selectedCount === 0" class="text-sm text-(--ui-text-muted)">
      Cuando tengas fragmentos elegidos podrás preguntarles lo que quieras.
    </p>

    <template v-else>
      <div class="space-y-3">
        <div v-if="chat.messages.length === 0" class="text-sm text-(--ui-text-muted)">
          Pregunta lo que quieras sobre el material elegido.
        </div>
        <div
          v-for="(m, i) in chat.messages"
          :key="i"
          class="text-sm"
          :class="m.role === 'user' ? 'text-right' : 'text-left'"
        >
          <span
            class="inline-block rounded px-3 py-2"
            :class="m.role === 'user' ? 'bg-primary/10' : 'bg-(--ui-bg-elevated)'"
          >{{ m.content }}</span>
          <div
            v-if="m.role === 'assistant' && m.sources?.length"
            class="text-xs text-(--ui-text-muted) mt-1"
          >
            Fuentes: {{ m.sources.map(s => `Ep. ${s.episode} (${s.date}) — ${s.topic}`).join(' · ') }}
          </div>
        </div>

        <UAlert
          v-if="chat.status === 'error'"
          color="error"
          icon="i-lucide-triangle-alert"
          :title="chat.error ?? 'No se pudo enviar'"
        />

        <form class="flex gap-2" @submit.prevent="send">
          <UInput v-model="draft" placeholder="Pregunta sobre tu selección…" class="flex-1" />
          <UButton type="submit" :loading="chat.status === 'sending'" icon="i-lucide-send">
            Enviar
          </UButton>
        </form>
      </div>
    </template>
  </UCard>
</template>
