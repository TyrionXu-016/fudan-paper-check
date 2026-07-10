import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useTaskStore } from '../../src/stores/task'

vi.mock('../../src/api/checkApi', () => ({
  uploadAndCheck: vi.fn(async (_file: File, _ruleId: string, onProgress: (p: number) => void) => {
    onProgress(100)
    return { taskId: 'task-1' }
  }),
  getResult: vi.fn(async () => ({ status: 'DONE', stage: 'DONE', percent: 100, issueCount: 0 })),
  getRuleBases: vi.fn(async () => []),
  fetchDocument: vi.fn(async () => null),
}))

vi.mock('../../src/api/sse', () => ({
  subscribeProgress: vi.fn(() => ({ close: vi.fn() })),
}))

describe('task store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('enters uploading and records file metadata', async () => {
    const task = useTaskStore()
    const file = new File(['abc'], 'demo.pdf', { type: 'application/pdf' })
    const promise = task.startUpload(file)
    expect(task.taskState).toBe('uploading')
    expect(task.fileName).toBe('demo.pdf')
    await promise
    expect(task.currentTaskId).toBe('task-1')
  })

  it('reset clears transient progress and errors', () => {
    const task = useTaskStore()
    task.setState('error')
    task.reset()
    expect(task.taskState).toBe('idle')
    expect(task.lastError).toBe('')
    expect(task.uploadPct).toBe(0)
  })
})
