<script setup lang="ts">
withDefaults(defineProps<{
  step: number
  size?: 'md' | 'lg'
  accent?: boolean
}>(), { size: 'md', accent: false })
</script>

<template>
  <span
    class="inline-flex shrink-0 items-center justify-center rounded-lg font-extrabold text-white"
    :class="[
      size === 'lg' ? 'size-8 text-lg' : 'size-6 text-sm',
      accent ? 'bg-primary' : 'bg-neutral-900',
    ]"
  >{{ step }}</span>
</template>
