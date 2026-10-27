// Sanctum's csrf-cookie endpoint lives at the API *origin*, not under /api.
export function apiOrigin(apiBase: string): string {
  return apiBase.replace(/\/api\/?$/, '')
}

export async function ensureCsrf(apiBase: string): Promise<void> {
  await $fetch(`${apiOrigin(apiBase)}/sanctum/csrf-cookie`, { credentials: 'include' })
}
