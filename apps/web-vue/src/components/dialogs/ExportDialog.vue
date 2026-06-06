<script setup lang="ts">
import { computed } from 'vue'
import ModalShell from './ModalShell.vue'
import AppIcon from '../AppIcon.vue'
import { useIssuesStore } from '../../stores/issues'
import { useUiStore } from '../../stores/ui'
import { exportPdf, exportWord } from '../../utils/export'

const issues = useIssuesStore()
const ui = useUiStore()

const format = computed(() => (ui.exportDialog === 'word' ? 'Word' : 'PDF'))
const pending = computed(() => issues.pendingCount)

function confirm() {
  const isWord = ui.exportDialog === 'word'
  ui.exportDialog = null
  if (isWord) exportWord()
  else exportPdf()
  ui.toast(`已导出 ${isWord ? 'Word' : 'PDF'}（应用全部修改）`, 'success')
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

    <template #footer>
      <button class="btn" @click="ui.exportDialog = null">取消</button>
      <button class="btn btn-primary" @click="confirm">
        <AppIcon name="download" :size="13" /> 确认导出
      </button>
    </template>
  </ModalShell>
</template>
