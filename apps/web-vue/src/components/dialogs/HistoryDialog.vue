<script setup lang="ts">
import { computed } from 'vue'
import ModalShell from './ModalShell.vue'
import type { ModRecord } from '../../types'
import { useUiStore } from '../../stores/ui'
import { useVersionStore } from '../../stores/version'

const ui = useUiStore()
const version = useVersionStore()

const spanId = computed(() => ui.historyDialog?.spanId ?? '')
const history = computed<ModRecord[]>(() => version.versions[spanId.value] ?? [])
const currentText = computed(() => history.value[history.value.length - 1]?.content)

function badgeLabel(v: ModRecord, isCurrent: boolean) {
  if (isCurrent) return '当前'
  if (v.source === 'ai') return 'AI 建议'
  if (v.source === 'custom') return '用户编辑'
  if (v.source === 'manual') return '手动编辑'
  if (v.source === 'original') return '原始文本'
  return '历史回退'
}
// 版本内容可能含格式标签，时间轴去标签纯文本展示
function plainText(s: string) {
  return s.replace(/<[^>]+>/g, '')
}
function badgeClass(v: ModRecord, current: boolean) {
  if (current) return 'current'
  return v.source === 'manual' ? 'custom' : v.source
}
function isCurrent(v: ModRecord, idx: number) {
  return v.content === currentText.value && idx === history.value.length - 1
}

function apply(idx: number) {
  version.applyRevert(spanId.value, idx)
  ui.toast(`已应用版本 ${idx}`, 'info')
  ui.historyDialog = null
}
</script>

<template>
  <ModalShell
    title="修改历史"
    :subtitle="`Span #${spanId} · 共 ${history.length} 个版本`"
    :width="580"
    @close="ui.historyDialog = null"
  >
    <div class="timeline">
      <div
        v-for="(v, idx) in history"
        :key="idx"
        class="tl-item"
        :class="badgeClass(v, isCurrent(v, idx))"
      >
        <div class="tl-meta">
          <span class="tl-badge" :class="badgeClass(v, isCurrent(v, idx))">
            {{ badgeLabel(v, isCurrent(v, idx)) }}
          </span>
          <span>版本 {{ idx }}</span>
          <span v-if="v.ts" style="margin-left: auto">{{ v.ts }}</span>
        </div>
        <div class="tl-text">{{ plainText(v.content) }}</div>
        <div class="tl-note">
          <span>{{ v.note || ' ' }}</span>
          <button v-if="!isCurrent(v, idx)" class="tl-apply" @click="apply(idx)">
            应用此版本 →
          </button>
        </div>
      </div>
    </div>

    <template #footer>
      <button class="btn" @click="ui.historyDialog = null">关闭</button>
    </template>
  </ModalShell>
</template>
