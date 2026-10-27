<script setup lang="ts">
import type { Fragment } from '~~/shared/types/search'

defineProps<{
  suggestions: Fragment[]
  status: 'idle' | 'loading' | 'error'
  selectedIds: string[]
}>()
const emit = defineEmits<{ toggle: [id: string]; retry: [] }>()
</script>

<template>
  <div class="space-y-3">
    <template v-if="status === 'loading'">
      <USkeleton v-for="n in 3" :key="n" class="h-24 w-full" />
    </template>
    <div v-else-if="status === 'error'" class="space-y-2">
      <UAlert
        color="error"
        icon="i-lucide-triangle-alert"
        title="La búsqueda ha fallado"
        description="Vuelve a intentarlo."
      />
      <UButton variant="outline" @click="emit('retry')">
        Reintentar
      </UButton>
    </div>
    <p v-else-if="suggestions.length === 0" class="text-(--ui-text-muted)">
      Aún no hay sugerencias — busca arriba un tema para empezar ↑
    </p>
    <template v-else>
      <FragmentCard
        v-for="f in suggestions"
        :key="f.id"
        :fragment="f"
        :included="selectedIds.includes(f.id)"
        @toggle="(id: string) => emit('toggle', id)"
      />
    </template>
  </div>
</template>
