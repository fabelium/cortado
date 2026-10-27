import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

// Privacy: fonts must be self-hosted (@nuxt/fonts, bundled with Nuxt UI) —
// linking Google Fonts sends every visitor's IP to Google.
describe('fonts', () => {
  it('does not load fonts from Google at runtime', () => {
    const config = readFileSync(resolve(process.cwd(), 'nuxt.config.ts'), 'utf8')
    expect(config).not.toMatch(/fonts\.(googleapis|gstatic)\.com/)
  })

  // The editorial headings use font-extrabold/black (800/900). @nuxt/fonts only
  // self-hosts the weights it is told about (default: 400).
  it('self-hosts every Inter weight the design uses', () => {
    const config = readFileSync(resolve(process.cwd(), 'nuxt.config.ts'), 'utf8')
    expect(config).toMatch(/weights:\s*\[[^\]]*800[^\]]*900[^\]]*\]/)
  })
})
