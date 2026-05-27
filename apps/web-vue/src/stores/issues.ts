import { defineStore } from 'pinia'
import { computed, reactive, ref } from 'vue'
import type { Decision, DecisionAction, Issue, IssueTypeKey } from '../types'
import { GROUP_ORDER, ISSUES, SPAN_INDEX } from '../data/paper'
import { useVersionStore } from './version'
import { useUiStore } from './ui'

interface UndoCmd {
  label: string
  undo: () => void
  redo: () => void
}

export const useIssuesStore = defineStore('issues', () => {
  const issues = ref<Issue[]>(ISSUES)
  const decisions = reactive<Record<string, Decision>>({})
  const activeIssueId = ref<string | null>(null)
  const searchQuery = ref('')
  const filterType = ref<'ALL' | IssueTypeKey>('ALL')

  const undoStack = ref<UndoCmd[]>([])
  const redoStack = ref<UndoCmd[]>([])

  // ---------- derived counts ----------
  const totalIssues = computed(() => issues.value.length)
  const decidedCount = computed(() => Object.keys(decisions).length)
  const pendingCount = computed(() => totalIssues.value - decidedCount.value)
  const acceptedCount = computed(
    () => Object.values(decisions).filter((d) => d.action === 'accept').length,
  )
  const customCount = computed(
    () => Object.values(decisions).filter((d) => d.action === 'custom').length,
  )
  const rejectedCount = computed(
    () => Object.values(decisions).filter((d) => d.action === 'reject').length,
  )

  // ---------- filtering & grouping ----------
  const filtered = computed(() => {
    const q = searchQuery.value.trim().toLowerCase()
    return issues.value.filter((i) => {
      if (filterType.value !== 'ALL' && i.type !== filterType.value) return false
      if (!q) return true
      return (
        i.summary.toLowerCase().includes(q) ||
        i.before.toLowerCase().includes(q) ||
        i.after.toLowerCase().includes(q) ||
        i.location.toLowerCase().includes(q)
      )
    })
  })

  const grouped = computed(() => {
    const map: Partial<Record<IssueTypeKey, Issue[]>> = {}
    for (const i of filtered.value) {
      ;(map[i.type] = map[i.type] || []).push(i)
    }
    return map
  })

  const groupKeys = computed(() =>
    GROUP_ORDER.filter((t) => (grouped.value[t]?.length ?? 0) > 0),
  )

  const firstPending = computed(() => issues.value.find((i) => !decisions[i.id]) ?? null)

  // ---------- core decision logic ----------
  function applyDecision(
    issueId: string,
    action: DecisionAction,
    customContent?: string,
    recordUndo = true,
    manual = false,
  ) {
    const version = useVersionStore()
    const issue = issues.value.find((i) => i.id === issueId)
    if (!issue) return
    const spanId = issue.spanId
    const prevDecision = decisions[issueId] ? { ...decisions[issueId] } : undefined
    const prevVersions = spanId ? [...(version.versions[spanId] || [])] : null

    decisions[issueId] = { action, customContent }

    if (spanId && (action === 'accept' || action === 'custom')) {
      const node = SPAN_INDEX[spanId]
      const newContent = action === 'accept' ? node?.suggested ?? issue.after : customContent ?? ''
      const source = manual ? 'manual' : action === 'accept' ? 'ai' : 'custom'
      const note = manual ? '手动编辑' : action === 'accept' ? `AI 建议：${issue.summary}` : '用户自定义修改'
      version.push(spanId, newContent, source, note)
    }

    if (recordUndo) {
      const cmd: UndoCmd = {
        label: action === 'accept' ? '接受' : action === 'reject' ? '拒绝' : '自定义',
        undo: () => {
          if (prevDecision) decisions[issueId] = prevDecision
          else delete decisions[issueId]
          if (spanId && prevVersions) version.setHistory(spanId, prevVersions)
        },
        redo: () => applyDecision(issueId, action, customContent),
      }
      undoStack.value = [...undoStack.value.slice(-19), cmd]
      redoStack.value = []
    }
  }

  function decide(issueId: string, action: DecisionAction, customContent?: string) {
    const ui = useUiStore()
    applyDecision(issueId, action, customContent)
    activeIssueId.value = issueId
    const issue = issues.value.find((i) => i.id === issueId)
    if (!issue) return
    if (action === 'accept') ui.toast(`已接受：${issue.summary}`, 'success')
    else if (action === 'custom') ui.toast('自定义修改已应用', 'info')
  }

  // 手动编辑：把预览区某个 span 的新内容（可含 <b>/<i>/<u> 等格式）写入版本历史
  function applyManualEdit(spanId: string, html: string) {
    const version = useVersionStore()
    const ui = useUiStore()
    const plain = html.replace(/<[^>]+>/g, '').trim()
    if (!plain) return // 不接受清空
    if (html === version.current(spanId)) return // 无变化
    const issue = issues.value.find((i) => i.spanId === spanId)
    if (issue) {
      applyDecision(issue.id, 'custom', html, true, true)
      activeIssueId.value = issue.id
    } else {
      version.push(spanId, html, 'manual', '手动编辑')
    }
    ui.toast('已记录手动编辑', 'success')
  }

  function undoIssue(issueId: string) {
    const ui = useUiStore()
    const version = useVersionStore()
    if (!decisions[issueId]) return
    const issue = issues.value.find((i) => i.id === issueId)
    delete decisions[issueId]
    if (issue?.spanId) version.popLast(issue.spanId)
    if (issue) ui.toast(`已撤销：${issue.summary}`)
  }

  function batchAccept(type: IssueTypeKey) {
    const ui = useUiStore()
    const targets = issues.value.filter((i) => i.type === type && !decisions[i.id])
    targets.forEach((i) => applyDecision(i.id, 'accept'))
    ui.toast(`已接受 ${targets.length} 项`, 'success')
  }

  function batchReject(type: IssueTypeKey) {
    const ui = useUiStore()
    const targets = issues.value.filter((i) => i.type === type && !decisions[i.id])
    targets.forEach((i) => applyDecision(i.id, 'reject'))
    ui.toast(`已拒绝 ${targets.length} 项`)
  }

  function undo() {
    const ui = useUiStore()
    const top = undoStack.value[undoStack.value.length - 1]
    if (!top) return
    top.undo()
    undoStack.value = undoStack.value.slice(0, -1)
    redoStack.value = [...redoStack.value, top]
    ui.toast('已撤销')
  }

  function redo() {
    const top = redoStack.value[redoStack.value.length - 1]
    if (!top) return
    top.redo()
    redoStack.value = redoStack.value.slice(0, -1)
  }

  function navigate(dir: 'up' | 'down') {
    const idx = issues.value.findIndex((i) => i.id === activeIssueId.value)
    const next =
      dir === 'down'
        ? issues.value[Math.min(issues.value.length - 1, idx + 1)]
        : issues.value[Math.max(0, idx - 1)]
    if (next) activeIssueId.value = next.id
  }

  function setActive(id: string | null) {
    activeIssueId.value = id
  }

  function reset() {
    for (const k of Object.keys(decisions)) delete decisions[k]
    undoStack.value = []
    redoStack.value = []
    activeIssueId.value = null
  }

  return {
    issues,
    decisions,
    activeIssueId,
    searchQuery,
    filterType,
    undoStack,
    redoStack,
    totalIssues,
    decidedCount,
    pendingCount,
    acceptedCount,
    customCount,
    rejectedCount,
    filtered,
    grouped,
    groupKeys,
    firstPending,
    decide,
    applyManualEdit,
    undoIssue,
    batchAccept,
    batchReject,
    undo,
    redo,
    navigate,
    setActive,
    reset,
  }
})
