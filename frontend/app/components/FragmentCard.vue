<script setup lang="ts">
import type { Fragment } from '~~/shared/types/search'
import { formatDuration } from '~/utils/formatDuration'

const props = defineProps<{ fragment: Fragment, included: boolean }>()
const emit = defineEmits<{ toggle: [id: string] }>()
</script>

<template>
  <UCard>
    <div class="flex items-start justify-between gap-4">
      <div class="space-y-1">
        <p class="font-medium">{{ props.fragment.name }}</p>
        <p class="text-sm text-(--ui-text-muted)">
          Ep. {{ props.fragment.episode }} · {{ props.fragment.date }} · {{ formatDuration(props.fragment.duration) }}
        </p>
        <p v-if="props.fragment.reason" class="text-sm">{{ props.fragment.reason }}</p>
      </div>
      <div class="flex flex-col items-end gap-2">
        <UTooltip v-if="props.fragment.score !== null" text="Relevancia estimada para tu tema">
          <UBadge
            :label="props.fragment.score.toFixed(2)"
            color="primary"
            variant="subtle"
          />
        </UTooltip>
        <UButton
          :icon="props.included ? 'i-lucide-check' : 'i-lucide-plus'"
          :color="props.included ? 'success' : 'neutral'"
          :variant="props.included ? 'solid' : 'outline'"
          size="sm"
          @click="emit('toggle', props.fragment.id)"
        >
          {{ props.included ? 'Incluida' : 'Incluir' }}
        </UButton>
      </div>
    </div>
  </UCard>
</template>
