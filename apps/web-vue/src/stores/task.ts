import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { STAGES } from '../data/paper'
import { getResult, uploadAndCheck } from '../api/checkApi'
import { useUiStore } from './ui'

export type TaskState = 'idle' | 'uploading' | 'detecting' | 'done'

const POLL_INTERVAL = 600

function formatSize(bytes: number): string {
  if (!bytes) return '—'
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${bytes} B`
}

// taskStore —— 任务状态机：上传 → 检测 → 完成（方案 §3.2）
// 上传走 checkApi.uploadAndCheck，检测走 checkApi.getResult 定时轮询（方案中期目标：先用轮询顶着）
export const useTaskStore = defineStore('task', () => {
  // 原型默认进入 done 态，便于直接演示完整界面
  const taskState = ref<TaskState>('done')
  const fileName = ref('张明_基于深度学习的图像识别方法研究.docx')
  const fileSize = ref(1.8 * 1024 * 1024)
  const uploadPct = ref(0)
  const detectStage = ref('FORMAT_CHECK')
  const detectPct = ref(35)
  const ruleId = ref('fudan_university')

  const fileSizeText = computed(() => formatSize(fileSize.value))
  const fileTypeLabel = computed(() =>
    /\.pdf$/i.test(fileName.value) ? 'PDF 文档' : 'Word 文档',
  )

  // 轮询令牌：reset / 重新上传时使旧轮询失效
  let pollToken = 0

  function stopPolling() {
    pollToken++
  }

  // 定时轮询检测结果，直到 DONE / ERROR
  function startPolling(taskId: string) {
    const ui = useUiStore()
    taskState.value = 'detecting'
    detectStage.value = 'PARSE'
    detectPct.value = 0
    const token = ++pollToken

    const tick = async () => {
      if (token !== pollToken) return // 已被取消
      try {
        const r = await getResult(taskId)
        if (token !== pollToken) return
        detectStage.value = r.stage
        detectPct.value = r.percent
        if (r.status === 'DONE') {
          taskState.value = 'done'
          ui.toast(`检测完成，共发现 ${r.issueCount} 项问题`, 'success')
          return
        }
        if (r.status === 'ERROR') {
          ui.toast(r.message || '检测失败', 'info')
          taskState.value = 'idle'
          return
        }
        setTimeout(tick, POLL_INTERVAL)
      } catch (e) {
        if (token !== pollToken) return
        ui.toast(e instanceof Error ? e.message : '检测请求失败', 'info')
        taskState.value = 'idle'
      }
    }
    tick()
  }

  // 上传 + 检测主流程
  async function startUpload(file?: File) {
    const ui = useUiStore()
    stopPolling()
    if (file) {
      fileName.value = file.name
      fileSize.value = file.size
    }
    taskState.value = 'uploading'
    uploadPct.value = 0
    try {
      const target = file ?? new File([], fileName.value)
      const { taskId } = await uploadAndCheck(target, ruleId.value, (p) => {
        uploadPct.value = p
      })
      startPolling(taskId)
    } catch (e) {
      ui.toast(e instanceof Error ? e.message : '上传失败', 'info')
      taskState.value = 'idle'
    }
  }

  // 供 Tweaks 面板直接切换状态机演示
  function setState(s: TaskState) {
    stopPolling()
    if (s === 'uploading') {
      startUpload()
      return
    }
    taskState.value = s
    if (s === 'detecting') {
      detectPct.value = 0
      detectStage.value = 'PARSE'
    }
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

  function reset() {
    stopPolling()
    taskState.value = 'idle'
    uploadPct.value = 0
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
    ruleId,
    startUpload,
    startPolling,
    setState,
    setStage,
    setRule,
    reset,
  }
})
