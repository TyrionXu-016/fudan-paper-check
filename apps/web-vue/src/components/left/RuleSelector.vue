<script setup lang="ts">
import { computed, ref } from 'vue'
import AppIcon from '../AppIcon.vue'
import { useTaskStore } from '../../stores/task'
import { useIssuesStore } from '../../stores/issues'
import { useUiStore } from '../../stores/ui'

const task = useTaskStore()
const issues = useIssuesStore()
const ui = useUiStore()

const open = ref(false)
const rule = computed(() => task.rules.find((r) => r.id === task.ruleId) ?? task.rules[0])

function choose(id: string) {
  open.value = false
  if (id === task.ruleId) return
  if (task.taskState === 'done' || issues.decidedCount > 0) {
    ui.pendingRuleId = id
    ui.showRuleSwitchConfirm = true
    return
  }
  task.setRule(id)
}
</script>

<template>
  <div class="rule">
    <div style="position: relative">
      <div class="rule-select" @click="open = !open">
        <div class="rule-icon"><AppIcon name="book" :size="14" /></div>
        <div class="rule-name">{{ rule?.name ?? '暂无规范' }}</div>
        <span style="font-size: 11px; color: var(--ink-4)">{{ rule?.version }}</span>
        <AppIcon name="chevD" :size="14" class="chev" />
      </div>
      <div
        v-if="open"
        style="
          position: absolute; top: 100%; left: 0; right: 0; margin-top: 4px;
          background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
          box-shadow: var(--shadow-lg); z-index: 40; overflow: hidden;
        "
      >
        <div
          v-for="r in task.rules"
          :key="r.id"
          @click="choose(r.id)"
          style="display: flex; align-items: center; gap: 10px; padding: 10px 12px; cursor: pointer; border-bottom: 1px solid var(--border)"
          :style="{ background: r.id === task.ruleId ? 'var(--teal-50)' : 'transparent' }"
        >
          <div
            style="width: 24px; height: 24px; border-radius: 5px; background: var(--bg-sunken); color: var(--ink-3); display: grid; place-items: center; font-size: 11px; font-weight: 600"
          >
            {{ r.short.slice(0, 2) }}
          </div>
          <div style="flex: 1">
            <div style="font-size: 13px; font-weight: 500">{{ r.name }}</div>
            <div style="font-size: 11px; color: var(--ink-4)">{{ r.version }}</div>
          </div>
          <AppIcon v-if="r.id === task.ruleId" name="check" :size="14" style="color: var(--teal-600)" />
        </div>
      </div>
    </div>
    <button class="rule-preview-link" @click="ui.showRulePreview = true">
      <AppIcon name="info" :size="12" /> 预览此规范要求
    </button>
  </div>
</template>

