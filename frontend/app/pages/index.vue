<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useCurationStore } from '~/stores/curation'

const store = useCurationStore()
const { suggestions, status, selectedIds, selectedFragments, selectedCount } = storeToRefs(store)
</script>

<template>
  <UContainer class="py-8 space-y-8">
    <AppHeader />
    <AppIntro />

    <section class="space-y-3">
      <StepHeading :step="1" title="Busca" subtitle="Escribe un tema y te sugerimos fragmentos del podcast." />
      <SearchBar :loading="status === 'loading'" @search="store.search" />
    </section>

    <div class="grid gap-8 lg:grid-cols-2">
      <!-- Left: curation -->
      <div class="space-y-8">
        <section class="space-y-3 border-t-[3px] border-neutral-900 pt-4">
          <StepHeading :step="2" title="Elige los fragmentos" subtitle="Incluye los que quieras; arrastra para ordenar tu selección." />
          <SuggestionList
            :suggestions="suggestions"
            :status="status"
            :selected-ids="selectedIds"
            @toggle="store.toggleInclude"
            @retry="() => store.search(store.query)"
          />
        </section>
        <section class="space-y-3 border-t-[3px] border-neutral-900 pt-4">
          <h3 class="font-extrabold tracking-tight">Tu selección ({{ selectedCount }})</h3>
          <SelectionPanel
            :fragments="selectedFragments"
            @toggle="store.toggleInclude"
            @reorder="store.reorder"
          />
        </section>
      </div>

      <!-- Right: production -->
      <div class="space-y-8">
        <OutputsPanel />
        <ChatPanel />
      </div>
    </div>
  </UContainer>
</template>
