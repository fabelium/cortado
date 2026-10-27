import { useAuthStore } from '~/stores/auth'

export default defineNuxtPlugin(async (nuxtApp) => {
  // SSR already hydrated the pinia payload; skip the duplicate client fetch.
  if (import.meta.client && nuxtApp.payload.serverRendered) return
  await useAuthStore().fetchUser()
})
