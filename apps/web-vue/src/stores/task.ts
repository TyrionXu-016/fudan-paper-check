import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { ISSUES, RULES, STAGES } from '../data/paper'
import type { Rule } from '../types'
import { fetchDocument, getResult, getRuleBases, restartCheck, uploadAndCheck } from '../api/checkApi'
import { adaptReport, type BackendCheckReport } from '../api/adapter'
import { adaptDocument } from '../api/docAdapter'
import { ENABLE_SSE_PROGRESS, MAX_PROGRESS_RETRIES, USE_MOCK } from '../api/env'
import { subscribeProgress, type ProgressStream } from '../api/sse'
import { useUiStore } from './ui'
import { useIssuesStore } from './issues'
import { useDocStore } from './doc'
import { useVersionStore } from './version'

export type TaskState = 'idle' | 'uploading' | 'detecting' | 'retrying' | 'done' | 'error'

const POLL_INTERVAL = 3000

function formatSize(bytes: number): string {
  if (!bytes) return '-'
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${bytes} B`
}

export const useTaskStore = defineStore('task', () => {
  const taskState = ref<TaskState>('idle')
  const fileName = ref('')
  const fileSize = ref(0)
  const uploadPct = ref(0)
  const detectStage = ref('UPLOADING')
  const detectPct = ref(0)
  const lastError = ref('')
  const retryAttempt = ref(0)
  const currentTaskId = ref<string | null>(null)
  const currentFile = ref<File | null>(null)
  const ruleId = ref('fudan_university')
  const rules = ref<Rule[]>(RULES)

  const fileSizeText = computed(() => formatSize(fileSize.value))
  const fileTypeLabel = computed(() => {
    const n = fileName.value.toLowerCase()
    if (n.endsWith('.pdf')) return 'PDF 文档'
    if (n.endsWith('.docx')) return 'Word 文档'
    if (n.endsWith('.md') || n.endsWith('.markdown')) return 'Markdown'
    return '文档'
  })

  let pollToken = 0
  let progressStream: ProgressStream | null = null

  function stopPolling() {
    pollToken += 1
    progressStream?.close()
    progressStream = null
  }

  async function hydrateDone(taskId: string, report?: BackendCheckReport) {
    if (!report) {
      if (USE_MOCK) useIssuesStore().setIssues(ISSUES)
      return
    }
    useIssuesStore().setIssues(adaptReport(report))
    const doc = await fetchDocument(taskId)
    if (doc) {
      const paper = adaptDocument(doc, report)
      useDocStore().setPaper(paper)
      useVersionStore().rebuildFromPaper(paper)
    }
  }

  function markError(message: string) {
    lastError.value = message
    taskState.value = 'error'
  }

  function startPolling(taskId: string, preferSse = ENABLE_SSE_PROGRESS) {
    const ui = useUiStore()
    const issues = useIssuesStore()
    stopPolling()
    currentTaskId.value = taskId
    issues.setBackendTask(taskId)
    taskState.value = retryAttempt.value > 0 ? 'retrying' : 'detecting'
    detectStage.value = 'PARSE'
    detectPct.value = Math.max(0, detectPct.value)
    lastError.value = ''
    const token = ++pollToken

    const poll = async () => {
      if (token !== pollToken) return
      try {
        const r = await getResult(taskId)
        if (token !== pollToken) return
        detectStage.value = r.stage
        detectPct.value = r.percent
        if (r.status === 'DONE') {
          await hydrateDone(taskId, r.report)
          taskState.value = 'done'
          retryAttempt.value = 0
          ui.toast(`检测完成，共发现 ${r.issueCount} 项问题`, 'success')
          return
        }
        if (r.status === 'ERROR') {
          markError(r.message || '检测失败')
          return
        }
        setTimeout(poll, POLL_INTERVAL)
      } catch (e) {
        if (token !== pollToken) return
        if (retryAttempt.value < MAX_PROGRESS_RETRIES) {
          retryAttempt.value += 1
          taskState.value = 'retrying'
          lastError.value = e instanceof Error ? e.message : '进度请求失败'
          setTimeout(poll, POLL_INTERVAL)
          return
        }
        markError(e instanceof Error ? e.message : '检测请求失败')
      }
    }

    if (preferSse) {
      progressStream = subscribeProgress(taskId, {
        onProgress(data) {
          if (token !== pollToken) return
          taskState.value = retryAttempt.value > 0 ? 'retrying' : 'detecting'
          detectStage.value = data.stage || detectStage.value
          detectPct.value = Math.max(detectPct.value, Number(data.percent ?? detectPct.value))
          if (data.message) lastError.value = data.message
        },
        async onDone() {
          if (token !== pollToken) return
          await poll()
        },
        onError(message) {
          if (token !== pollToken) return
          lastError.value = message
        },
        onFallback() {
          if (token !== pollToken) return
          retryAttempt.value += 1
          taskState.value = 'retrying'
          ui.toast('实时进度连接不可用，已切换为轮询模式')
          poll()
        },
      })
      return
    }

    poll()
  }

  async function startUpload(file?: File) {
    stopPolling()
    retryAttempt.value = 0
    lastError.value = ''
    currentTaskId.value = null
    useIssuesStore().setBackendTask(null)
    if (file) {
      currentFile.value = file
      fileName.value = file.name
      fileSize.value = file.size
    }
    taskState.value = 'uploading'
    uploadPct.value = 0
    try {
      const target = file ?? currentFile.value ?? (USE_MOCK ? new File([], fileName.value || 'demo.docx') : null)
      if (!target) {
        markError('请先选择论文文件')
        return
      }
      const { taskId } = await uploadAndCheck(target, ruleId.value, (p) => {
        uploadPct.value = p
      })
      startPolling(taskId)
    } catch (e) {
      markError(e instanceof Error ? e.message : '上传失败')
    }
  }

  async function restartWithRule(nextRuleId: string) {
    stopPolling()
    retryAttempt.value = 0
    lastError.value = ''
    ruleId.value = nextRuleId
    useIssuesStore().reset()
    useVersionStore().reset()

    if (currentTaskId.value) {
      taskState.value = 'detecting'
      detectStage.value = 'UPLOADING'
      detectPct.value = 0
      try {
        const { taskId } = await restartCheck(currentTaskId.value, nextRuleId)
        startPolling(taskId)
      } catch (e) {
        markError(e instanceof Error ? e.message : '重新检测失败')
      }
      return
    }

    await startUpload()
  }

  function retry() {
    if (currentTaskId.value) startPolling(currentTaskId.value, false)
    else startUpload()
  }

  function setState(s: TaskState) {
    stopPolling()
    if (s === 'uploading') {
      startUpload()
      return
    }
    taskState.value = s
    if (s === 'detecting' || s === 'retrying') {
      detectPct.value = 0
      detectStage.value = 'PARSE'
    }
    if (s === 'error') lastError.value = '演示错误状态'
  }

  function setStage(id: string) {
    const s = STAGES.find((x) => x.id === id)
    if (s) {
      detectStage.value = s.id
      detectPct.value = s.pct
    }
  }

  function setRule(id: string) {
    ruleId.value = id
  }

  async function loadRuleBases() {
    try {
      const list = await getRuleBases()
      if (list.length) {
        rules.value = list
        if (!list.find((r) => r.id === ruleId.value)) ruleId.value = list[0].id
      }
    } catch (e) {
      useUiStore().toast(e instanceof Error ? e.message : '规范列表加载失败', 'info')
    }
  }

  function reset() {
    stopPolling()
    taskState.value = 'idle'
    uploadPct.value = 0
    retryAttempt.value = 0
    lastError.value = ''
    currentTaskId.value = null
    currentFile.value = null
    useIssuesStore().reset()
    useDocStore().reset()
    useVersionStore().reset()
  }

  return {
    taskState,
    fileName,
    fileSize,
    fileSizeText,
    fileTypeLabel,
    uploadPct,
    detectStage,
    detectPct,
    lastError,
    retryAttempt,
    currentTaskId,
    currentFile,
    ruleId,
    rules,
    startUpload,
    restartWithRule,
    startPolling,
    retry,
    setState,
    setStage,
    setRule,
    loadRuleBases,
    reset,
  }
})

