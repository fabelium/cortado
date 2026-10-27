// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/ui', '@nuxt/eslint', '@pinia/nuxt'],
  css: ['~/assets/css/main.css'],
  // Inter is declared in main.css (--font-sans); @nuxt/fonts (bundled with
  // Nuxt UI) downloads it at build time and self-hosts it — no runtime
  // requests to Google, so visitors' IPs are not leaked. The editorial headings
  // use 800/900, so list the weights (the module's default is only 400).
  fonts: {
    defaults: { weights: [400, 600, 700, 800, 900] },
  },
  ui: {
    // Editorial direction is light-first; disable color-mode switching.
    colorMode: false,
  },
  runtimeConfig: {
    public: {
      // Laravel api/ (php artisan serve + php artisan queue:work). Override
      // with NUXT_PUBLIC_API_BASE; tests pin '/api' (registerEndpoint mocks).
      apiBase: 'http://localhost:8000/api',
    },
  },
})
