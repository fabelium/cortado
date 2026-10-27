import { defineVitestConfig } from '@nuxt/test-utils/config'

export default defineVitestConfig({
  test: {
    environment: 'nuxt',
    setupFiles: ['./vitest.setup.ts'],
    // The nuxt environment builds the whole app per worker; parallel workers
    // can push that past vitest's 10s default hook timeout.
    hookTimeout: 30000,
    environmentOptions: {
      nuxt: {
        overrides: {
          runtimeConfig: {
            public: {
              // Tests hit same-origin registerEndpoint mocks, not Laravel.
              apiBase: '/api',
            },
          },
        },
      },
    },
  },
})
