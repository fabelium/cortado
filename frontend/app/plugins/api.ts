import { readXsrfCookie, buildApiHeaders } from '~/utils/apiHeaders'

export default defineNuxtPlugin(() => {
  // Captured at plugin setup: useRequestHeaders/useRequestURL need the Nuxt
  // context, which is not guaranteed inside onRequest. The referer makes
  // Sanctum treat SSR calls as coming from the stateful frontend domain.
  const ssr = import.meta.server
    ? { cookie: useRequestHeaders(['cookie']).cookie, referer: useRequestURL().origin }
    : undefined

  const api = $fetch.create({
    baseURL: useRuntimeConfig().public.apiBase,
    credentials: 'include',
    onRequest({ options }) {
      const xsrf = import.meta.server ? null : readXsrfCookie(document.cookie)
      options.headers = buildApiHeaders(options.headers as HeadersInit | undefined, xsrf, ssr)
    },
  })

  return { provide: { api } }
})
