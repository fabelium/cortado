import { describe, it, expect } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import AudioOptions from '~/components/AudioOptions.vue'

describe('AudioOptions', () => {
  it('renders the option labels', async () => {
    const c = await mountSuspended(AudioOptions, { props: { intro: true, disclaimer: true, split: null } })
    expect(c.text()).toContain('Intro hablada')
    expect(c.text()).toContain('Aviso educativo')
    expect(c.text()).toContain('Trocear')
  })

  it('explains the split field with form-field help, not a tooltip wrapper', async () => {
    const c = await mountSuspended(AudioOptions, { props: { intro: true, disclaimer: true, split: null } })
    expect(c.text()).toContain('Divide el audio en partes de esta duración')
  })

  it('emits update:split when the split field changes', async () => {
    const c = await mountSuspended(AudioOptions, { props: { intro: true, disclaimer: true, split: null } })
    await c.find('input[type="number"]').setValue('30')
    expect(c.emitted('update:split')).toBeTruthy()
    expect(c.emitted('update:split')!.at(-1)).toEqual([30])
  })
})
