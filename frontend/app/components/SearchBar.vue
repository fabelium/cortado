<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ loading?: boolean }>()
const emit = defineEmits<{ search: [query: string] }>()

const query = ref('')
const showHint = ref(false)

function submit() {
  const q = query.value.trim()
  if (!q) {
    showHint.value = true
    return
  }
  showHint.value = false
  emit('search', q)
}
</script>

<template>
  <div class="space-y-1">
    <form class="flex gap-2" @submit.prevent="submit">
      <UInput
        v-model="query"
        placeholder="¿De qué tema te apetece el cortado? — p. ej. agujeros negros"
        class="flex-1"
        size="lg"
      />
      <UButton type="submit" :loading="loading" icon="i-lucide-search" size="lg">
        Buscar
      </UButton>
    </form>
    <p v-if="showHint" class="text-sm text-(--ui-text-muted)">
      Escribe un tema para buscar.
    </p>
  </div>
</template>
