import type { SearchResponse } from '~~/shared/types/search'
import { expectOk } from '~/utils/expectOk'

export function useSearchClient() {
  const { $api } = useNuxtApp()

  async function search(query: string): Promise<SearchResponse> {
    return expectOk(await $api<SearchResponse>('/search', {
      method: 'POST',
      body: { query },
    }))
  }

  return { search }
}
