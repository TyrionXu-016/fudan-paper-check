<script setup lang="ts">
import ModalShell from './ModalShell.vue'
import { useUiStore } from '../../stores/ui'

const ui = useUiStore()

const SHORTCUTS: { k: string[]; label: string }[] = [
  { k: ['A'], label: '接受当前问题' },
  { k: ['R'], label: '拒绝当前问题' },
  { k: ['E'], label: '自定义修改' },
  { k: ['↑'], label: '上一个问题' },
  { k: ['↓'], label: '下一个问题' },
  { k: ['Ctrl', 'Z'], label: '撤销 (最近 20 步)' },
  { k: ['Ctrl', 'Shift', 'Z'], label: '重做' },
  { k: ['Ctrl', 'Y'], label: '重做' },
  { k: ['Ctrl', 'A'], label: '全部接受当前分类' },
  { k: ['Ctrl', 'R'], label: '全部拒绝当前分类' },
  { k: ['Ctrl', 'F'], label: '聚焦搜索框' },
  { k: ['Ctrl', '+'], label: '放大预览' },
  { k: ['Ctrl', '-'], label: '缩小预览' },
  { k: ['Ctrl', 'S'], label: '导出 Word' },
  { k: ['?'], label: '打开本面板' },
  { k: ['Esc'], label: '关闭对话框 / 取消编辑' },
]
</script>

<template>
  <ModalShell title="键盘快捷键" subtitle="高效处理大量问题" :width="620" @close="ui.showShortcuts = false">
    <div class="shortcut-grid">
      <div v-for="(s, i) in SHORTCUTS" :key="i" class="shortcut-row">
        <div>{{ s.label }}</div>
        <div class="shortcut-keys">
          <template v-for="(kk, ki) in s.k" :key="ki">
            <kbd>{{ kk }}</kbd>
            <span v-if="ki < s.k.length - 1" style="color: var(--ink-5); font-size: 11px; padding: 0 2px">+</span>
          </template>
        </div>
      </div>
    </div>
    <template #footer>
      <button class="btn" @click="ui.showShortcuts = false">知道了</button>
    </template>
  </ModalShell>
</template>
