/**
 * Global vitest setup for the Nuxt test environment.
 *
 * Problem: `mountSuspended` reuses the single Nuxt app created by
 * `environment: 'nuxt'`.  That app has its own Pinia instance (injected via
 * `@pinia/nuxt`).  The `setActivePinia(createPinia())` call in each test
 * file's `beforeEach` creates a fresh Pinia, but as soon as any component
 * setup runs `useStore()` inside the Nuxt app context, Pinia's injection
 * resolution (inject(piniaSymbol)) returns the *Nuxt app's* Pinia and calls
 * `setActivePinia(nuxt_pinia)` — overwriting the fresh one.
 *
 * Result: store state from test N leaks into test N+1 in the same file, so
 * toggle actions that should add an item instead remove it.
 *
 * Fix: a global `beforeEach` that resets all registered Options API stores
 * (those with `$reset()`) in whatever Pinia is currently active.  This runs
 * before the test file's own `beforeEach`, so the Nuxt Pinia is clean by the
 * time `mountSuspended` runs.
 */
import { beforeEach } from 'vitest'
import { getActivePinia } from 'pinia'
import { config } from '@vue/test-utils'

// UTooltip needs UApp's TooltipProvider, which isolated component mounts
// don't have — stub it to a passthrough (tooltip copy is not unit-asserted).
config.global.stubs = {
  ...(config.global.stubs as Record<string, unknown>),
  UTooltip: { template: '<span><slot /></span>' },
}

beforeEach(() => {
  const pinia = getActivePinia()
  if (!pinia) return
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  ;(pinia as any)._s?.forEach((store: { $reset?: () => void }) => {
    store.$reset?.()
  })
})
