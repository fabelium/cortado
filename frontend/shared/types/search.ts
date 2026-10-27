export interface Fragment {
  id: string
  episode: number
  date: string
  start: number
  end: number | null
  duration: number | null
  name: string
  score: number | null
  reason: string | null
}

export interface SearchRequest {
  query: string
}

// Consumer type: the Laravel API returns only { ok, fragments }; the engine
// contract's version/action are stripped. See contract/schema/response.search.schema.json
export interface SearchResponse {
  ok: boolean
  fragments: Fragment[]
}
