<script setup lang="ts">
import { computed } from 'vue'
import ModalShell from './ModalShell.vue'
import AppIcon from '../AppIcon.vue'
import { useTaskStore } from '../../stores/task'
import { useUiStore } from '../../stores/ui'

const task = useTaskStore()
const ui = useUiStore()

const rule = computed(() => task.rules.find((r) => r.id === task.ruleId) ?? task.rules[0])
const cats = computed(() => rule.value?.summary ?? {})
const catCount = computed(() => Object.keys(cats.value).length)

const catStyle: Record<string, { icon: string; color: string; bg: string }> = {
  格式规范: { icon: 'book', color: 'var(--teal-700)', bg: 'var(--teal-50)' },
  错别字: { icon: 'warning', color: '#b91c1c', bg: '#fee2e2' },
  语病检查: { icon: 'warning', color: '#b45309', bg: '#fef3c7' },
  学术润色: { icon: 'sparkle', color: '#7c3aed', bg: '#ede9fe' },
  参考文献: { icon: 'file', color: '#0284c7', bg: '#e0f2fe' },
  逻辑检查: { icon: 'info', color: '#0f766e', bg: 'var(--teal-50)' },
}
const catLabel: Record<string, string> = {
  format: '格式规范',
  typo: '错别字',
  grammar: '语病检查',
  polish: '学术润色',
  reference: '参考文献',
  logic: '逻辑检查',
}
function labelFor(cat: string) {
  return catLabel[cat] ?? cat
}
function styleFor(cat: string) {
  return catStyle[labelFor(cat)] ?? { icon: 'info', color: 'var(--ink-3)', bg: 'var(--bg-sunken)' }
}
</script>

<template>
  <ModalShell
    :title="rule?.name ?? '检测规范'"
    :subtitle="`${rule?.version || '当前版本'} · 共 ${catCount} 项检测维度`"
    :width="620"
    @close="ui.showRulePreview = false"
  >
    <div v-for="(items, cat) in cats" :key="cat" class="rule-cat">
      <div class="rule-cat-title">
        <span class="icon" :style="{ background: styleFor(cat).bg, color: styleFor(cat).color }">
          <AppIcon :name="styleFor(cat).icon" :size="13" />
        </span>
        {{ labelFor(cat) }}
        <span style="font-size: 11px; color: var(--ink-4); font-weight: 400">· {{ items.length }} 项</span>
      </div>
      <ul class="rule-list">
        <li v-for="(s, i) in items" :key="i">{{ s }}</li>
      </ul>
    </div>

    <template #footer>
      <button class="btn btn-primary" @click="ui.showRulePreview = false">使用此规范</button>
    </template>
  </ModalShell>
</template>
