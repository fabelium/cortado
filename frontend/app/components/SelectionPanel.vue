<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useSortable } from '@vueuse/integrations/useSortable'
import type { Fragment } from '~~/shared/types/search'
import { formatDuration } from '~/utils/formatDuration'

const props = defineProps<{ fragments: Fragment[] }>()
const emit = defineEmits<{ toggle: [id: string], reorder: [from: number, to: number] }>()

const container = ref<HTMLElement | null>(null)
const list = ref<Fragment[]>([...props.fragments])
watch(() => props.fragments, (v) => { list.value = [...v] })

onMounted(() => {
  // SortableJS needs a real element; guard so it never breaks SSR/tests.
  if (!container.value) return
  try {
    useSortable(container, list, {
      animation: 150,
      onUpdate(e: { oldIndex?: number, newIndex?: number }) {
        if (e.oldIndex === undefined || e.newIndex === undefined) return
        emit('reorder', e.oldIndex, e.newIndex)
      },
    })
  }
  catch {
    // useSortable may throw in test environments (happy-dom); drag is a
    // progressive enhancement — silently ignore and keep the feature available
    // in a real browser.
  }
})
</script>

<template>
  <div class="space-y-3">
    <p class="text-sm text-(--ui-text-muted)">{{ list.length }} elegidos</p>
    <p v-if="list.length === 0" class="text-(--ui-text-muted)">
      Incluye sugerencias para montar tu selección.
    </p>
    <div ref="container" class="space-y-2">
      <UCard v-for="f in list" :key="f.id" class="cursor-move">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="font-medium">{{ f.name }}</p>
            <p class="text-sm text-(--ui-text-muted)">
              Ep. {{ f.episode }} · {{ formatDuration(f.duration) }}
            </p>
          </div>
          <UButton
            icon="i-lucide-x"
            color="error"
            variant="ghost"
            size="sm"
            aria-label="Quitar de la selección"
            @click="emit('toggle', f.id)"
          />
        </div>
      </UCard>
    </div>
  </div>
</template>
