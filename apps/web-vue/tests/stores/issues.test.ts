import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useIssuesStore } from '../../src/stores/issues'
import { ISSUES } from '../../src/data/paper'

describe('issues store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('records accept/reject decisions and supports undo', () => {
    const issues = useIssuesStore()
    issues.setIssues(ISSUES)
    const first = issues.issues[0]
    issues.decide(first.id, 'accept')
    expect(issues.acceptedCount).toBe(1)
    expect(issues.decidedCount).toBe(1)
    issues.undo()
    expect(issues.decidedCount).toBe(0)
  })

  it('filters issues by keyword and type', () => {
    const issues = useIssuesStore()
    issues.setIssues(ISSUES)
    issues.filterType = 'FORMAT'
    expect(issues.filtered.every((issue) => issue.type === 'FORMAT')).toBe(true)
    issues.searchQuery = '__no_match__'
    expect(issues.filtered).toHaveLength(0)
  })
})
