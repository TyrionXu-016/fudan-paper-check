import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useVersionStore } from '../../src/stores/version'

describe('version store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('tracks span history and can revert to an earlier version', () => {
    const version = useVersionStore()
    const spanId = Object.keys(version.versions)[0]
    const original = version.current(spanId)
    version.push(spanId, 'new content', 'custom', 'test')
    expect(version.current(spanId)).toBe('new content')
    version.applyRevert(spanId, 0)
    expect(version.current(spanId)).toBe(original)
  })

  it('keeps original version while capping span history', () => {
    const version = useVersionStore()
    const spanId = Object.keys(version.versions)[0]
    const original = version.versions[spanId][0].content

    for (let i = 1; i <= 25; i += 1) {
      version.push(spanId, `content ${i}`, 'custom', 'test')
    }

    expect(version.versions[spanId]).toHaveLength(20)
    expect(version.versions[spanId][0].content).toBe(original)
    expect(version.current(spanId)).toBe('content 25')
  })
})
