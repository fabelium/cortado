import { defineStore } from 'pinia'
import { useSearchClient } from '~/composables/useSearchClient'
import type { Fragment } from '~~/shared/types/search'

export const useCurationStore = defineStore('curation', {
  state: () => ({
    query: '',
    suggestions: [] as Fragment[],
    selectedIds: [] as string[],
    status: 'idle' as 'idle' | 'loading' | 'error',
    error: null as string | null,
  }),
  getters: {
    selectedFragments(state): Fragment[] {
      return state.selectedIds
        .map(id => state.suggestions.find(f => f.id === id))
        .filter((f): f is Fragment => f !== undefined)
    },
    selectedCount(state): number {
      return state.selectedIds.length
    },
    isIncluded: state => (id: string) => state.selectedIds.includes(id),
  },
  actions: {
    async search(query: string) {
      this.query = query
      this.status = 'loading'
      this.error = null
      try {
        const { search } = useSearchClient()
        const res = await search(query)
        this.suggestions = res.fragments
        this.selectedIds = []
        this.status = 'idle'
      }
      catch {
        this.suggestions = []
        this.status = 'error'
        this.error = 'La búsqueda ha fallado. Vuelve a intentarlo.'
      }
    },
    toggleInclude(id: string) {
      const i = this.selectedIds.indexOf(id)
      if (i === -1) this.selectedIds.push(id)
      else this.selectedIds.splice(i, 1)
    },
    reorder(from: number, to: number) {
      const n = this.selectedIds.length
      if (from < 0 || to < 0 || from >= n || to >= n) return
      const [moved] = this.selectedIds.splice(from, 1)
      this.selectedIds.splice(to, 0, moved)
    },
    clear() {
      this.query = ''
      this.suggestions = []
      this.selectedIds = []
      this.status = 'idle'
      this.error = null
    },
  },
})
