<script setup lang="ts">
import { computed, ref } from 'vue'
import ModalShell from './ModalShell.vue'
import AppIcon from '../AppIcon.vue'
import { useIssuesStore } from '../../stores/issues'
import { useTaskStore } from '../../stores/task'
import { useUiStore } from '../../stores/ui'
import { useEditorStore } from '../../stores/editor'
import { USE_MOCK } from '../../api/env'
import { exportFromBackend, type ExportFormat } from '../../api/exportApi'
import { getBackendPreview } from '../../api/previewApi'
import { exportPdf, exportWord } from '../../utils/export'

const issues = useIssuesStore()
const task = useTaskStore()
const ui = useUiStore()
const editor = useEditorStore()

const format = computed(() => (ui.exportDialog === 'word' ? 'Word' : 'PDF'))
const pending = computed(() => issues.pendingCount)
const exporting = ref(false)

async function confirm() {
  if (exporting.value) return
  exporting.value = true
  const isWord = ui.exportDialog === 'word'
  const backendFormat: ExportFormat = isWord ? 'docx' : 'pdf'
  try {
    if (!USE_MOCK && task.currentTaskId && !editor.dirty) {
      await exportFromBackend(task.currentTaskId, backendFormat, issues.decisions)
      getBackendPreview(task.currentTaskId)
        .then((preview) => {
          if (preview.unresolved_count !== pending.value) {
            ui.toast(`后端预览显示仍有 ${preview.unresolved_count} 项未处理`, 'info')
          }
        })
        .catch(() => undefined)
    } else if (isWord) {
      exportWord()
    } else {
      await exportPdf()
    }
    ui.exportDialog = null
    ui.toast(`已导出${isWord ? 'Word' : 'PDF'}（应用全部修改）`, 'success')
  } catch (e) {
    ui.toast(e instanceof Error ? e.message : '导出失败')
  } finally {
    exporting.value = false
  }
}
</script>

<template>
  <ModalShell :title="`导出 ${format}`" @close="ui.exportDialog = null">
    <div v-if="pending > 0" style="display: flex; gap: 12px; align-items: flex-start">
      <div
        style="width: 32px; height: 32px; border-radius: 8px; background: var(--amber-50); color: var(--amber-500); display: grid; place-items: center; flex: none"
      >
        <AppIcon name="warning" :size="16" />
      </div>
      <div>
        <div style="font-weight: 500; margin-bottom: 4px">
          还有 <span style="color: var(--amber-500); font-weight: 700">{{ pending }}</span> 项问题未处理
        </div>
        <div style="font-size: 12.5px; color: var(--ink-4); line-height: 1.6">
          未处理的问题将以原文形式保留在导出文档中。确认继续导出，或点击取消返回继续处理。
        </div>
      </div>
    </div>
    <div v-else style="display: flex; gap: 12px; align-items: flex-start">
      <div
        style="width: 32px; height: 32px; border-radius: 8px; background: var(--green-50); color: var(--green-700); display: grid; place-items: center; flex: none"
      >
        <AppIcon name="check" :size="16" />
      </div>
      <div>
        <div style="font-weight: 500">全部 {{ issues.totalIssues }} 项问题已处理</div>
        <div style="font-size: 12.5px; color: var(--ink-4)">将导出包含所有修改的最终版本。</div>
      </div>
    </div>

    <div
      v-if="editor.dirty"
      style="margin-top: 14px; padding: 10px 12px; border-radius: 8px; background: var(--teal-50); color: var(--teal-800); font-size: 12.5px; line-height: 1.6"
    >
      已检测到整篇手动编辑内容，本次将使用本地导出以保留当前预览中的修改。
    </div>

    <template #footer>
      <button class="btn" @click="ui.exportDialog = null">取消</button>
      <button class="btn btn-primary" :disabled="exporting" @click="confirm">
        <AppIcon name="download" :size="13" /> {{ exporting ? '导出中...' : '确认导出' }}
      </button>
    </template>
  </ModalShell>
</template>
