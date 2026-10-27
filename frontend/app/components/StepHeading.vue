<script setup lang="ts">
defineProps<{
  step?: number
  title: string
  subtitle?: string
  accent?: boolean
}>()
</script>

<template>
  <div class="space-y-1">
    <h2 class="font-extrabold tracking-tight flex items-center gap-2">
      <StepBadge v-if="step" :step="step" :accent="accent" />
      <span>{{ title }}</span>
    </h2>
    <p v-if="subtitle" class="text-sm text-(--ui-text-muted)">{{ subtitle }}</p>
  </div>
</template>
