<script setup lang="ts">
defineProps<{ intro: boolean, disclaimer: boolean, split: number | null }>()
const emit = defineEmits<{
  'update:intro': [boolean]
  'update:disclaimer': [boolean]
  'update:split': [number | null]
}>()

function onSplit(value: string | number) {
  const n = typeof value === 'number' ? value : Number(value)
  emit('update:split', Number.isFinite(n) && n > 0 ? n : null)
}
</script>

<template>
  <div class="space-y-3">
    <UTooltip text="Añade una presentación locutada al principio">
      <USwitch
        :model-value="intro"
        label="Intro hablada"
        @update:model-value="(v: boolean) => emit('update:intro', v)"
      />
    </UTooltip>
    <UTooltip text="Incluye el aviso hablado sobre el origen de los clips">
      <USwitch
        :model-value="disclaimer"
        label="Aviso educativo"
        @update:model-value="(v: boolean) => emit('update:disclaimer', v)"
      />
    </UTooltip>
    <UFormField label="Trocear (minutos, opcional)" help="Divide el audio en partes de esta duración">
      <UInput
        :model-value="split ?? undefined"
        type="number"
        placeholder="Sin trocear"
        min="1"
        @update:model-value="onSplit"
      />
    </UFormField>
  </div>
</template>
