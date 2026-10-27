// Defense for the sync action envelopes: the API signals controlled engine
// failures with ok:false — never trust a 2xx status alone.
export function expectOk<T extends { ok: boolean }>(res: T & { error?: string | null }): T {
  if (!res.ok) throw new Error(res.error ?? 'The API reported a failure.')
  return res
}
