<script setup lang="ts">
import { ref } from 'vue'
import AppIcon from '../AppIcon.vue'
import IssueCard from './IssueCard.vue'
import type { IssueTypeKey } from '../../types'
import { GROUP_ORDER, TYPE_META } from '../../data/paper'
import { useIssuesStore } from '../../stores/issues'

const issues = useIssuesStore()
const collapsed = ref<Partial<Record<IssueTypeKey, boolean>>>({})
function toggle(t: IssueTypeKey) {
  collapsed.value[t] = !collapsed.value[t]
}

function pendingOf(type: IssueTypeKey) {
  const items = issues.grouped[type] ?? []
  return items.filter((i) => !issues.decisions[i.id]).length
}
function doneOf(type: IssueTypeKey) {
  const items = issues.grouped[type] ?? []
  return items.length - pendingOf(type)
}

const availableTypes = GROUP_ORDER.filter((t) => issues.issues.some((i) => i.type === t))
</script>

<template>
  <div style="display: flex; flex-direction: column; flex: 1; min-height: 0">
    <div class="issues-toolbar">
      <div class="search">
        <AppIcon name="search" :size="14" />
        <input v-model="issues.searchQuery" placeholder="搜索问题..." />
      </div>
      <select v-model="issues.filterType" class="filter-select">
        <option value="ALL">全部类型</option>
        <option v-for="t in availableTypes" :key="t" :value="t">{{ TYPE_META[t].label }}</option>
      </select>
    </div>

    <div class="issues-scroll">
      <div
        v-if="issues.groupKeys.length === 0"
        style="padding: 32px 20px; text-align: center; color: var(--ink-4)"
      >
        <div style="font-size: 13px">没有匹配的问题</div>
      </div>

      <div v-for="type in issues.groupKeys" :key="type" class="group">
        <div class="group-head" @click="toggle(type)">
          <AppIcon name="chevR" :size="14" class="group-caret" :class="{ open: !collapsed[type] }" />
          <div class="group-icon" :style="{ background: TYPE_META[type].bg, color: TYPE_META[type].color }">
            <span style="font-size: 10px; font-weight: 700">{{ TYPE_META[type].short }}</span>
          </div>
          <div class="group-title">{{ TYPE_META[type].label }}</div>
          <div class="group-count">
            <span v-if="pendingOf(type) > 0" class="count-pill pending">{{ pendingOf(type) }} 待处理</span>
            <span v-if="doneOf(type) > 0" class="count-pill done">{{ doneOf(type) }} 已处理</span>
          </div>
        </div>

        <template v-if="!collapsed[type]">
          <IssueCard v-for="issue in issues.grouped[type]" :key="issue.id" :issue="issue" />
          <div v-if="pendingOf(type) > 0" class="group-batch">
            <button @click="issues.batchAccept(type)">
              <AppIcon name="check" :size="12" style="vertical-align: -1px; margin-right: 4px" />
              全部接受 ({{ pendingOf(type) }})
            </button>
            <button @click="issues.batchReject(type)">
              <AppIcon name="x" :size="12" style="vertical-align: -1px; margin-right: 4px" />
              全部拒绝
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
