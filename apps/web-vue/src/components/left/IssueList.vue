<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import AppIcon from '../AppIcon.vue'
import IssueCard from './IssueCard.vue'
import type { Issue, IssueTypeKey } from '../../types'
import { GROUP_ORDER, TYPE_META } from '../../data/paper'
import { useIssuesStore } from '../../stores/issues'

const issues = useIssuesStore()
const collapsed = ref<Partial<Record<IssueTypeKey, boolean>>>({})
const scrollTop = ref(0)
const viewportHeight = ref(620)

const HEADER_H = 48
const ISSUE_H = 238
const BATCH_H = 48
const OVERSCAN = 6
const VIRTUAL_THRESHOLD = 200

const measuredHeights = reactive<Record<string, number>>({})
const observers = new Map<string, ResizeObserver>()

type Row =
  | { key: string; kind: 'header'; type: IssueTypeKey; h: number }
  | { key: string; kind: 'issue'; type: IssueTypeKey; issue: Issue; h: number }
  | { key: string; kind: 'batch'; type: IssueTypeKey; h: number }

function toggle(t: IssueTypeKey) {
  collapsed.value[t] = !collapsed.value[t]
}

function estimateHeight(kind: Row['kind']) {
  if (kind === 'header') return HEADER_H
  if (kind === 'batch') return BATCH_H
  return ISSUE_H
}

function rowHeight(row: Pick<Row, 'key' | 'kind'>) {
  return measuredHeights[row.key] ?? estimateHeight(row.kind)
}

function setRowEl(key: string, el: Element | null) {
  observers.get(key)?.disconnect()
  observers.delete(key)
  if (!(el instanceof HTMLElement)) return

  const measure = () => {
    measuredHeights[key] = el.offsetHeight
  }
  measure()
  const observer = new ResizeObserver(measure)
  observer.observe(el)
  observers.set(key, observer)
}

onBeforeUnmount(() => {
  for (const observer of observers.values()) observer.disconnect()
  observers.clear()
})

function pendingOf(type: IssueTypeKey) {
  const items = issues.grouped[type] ?? []
  return items.filter((i) => !issues.decisions[i.id]).length
}
function doneOf(type: IssueTypeKey) {
  const items = issues.grouped[type] ?? []
  return items.length - pendingOf(type)
}

const availableTypes = computed(() => GROUP_ORDER.filter((t) => issues.issues.some((i) => i.type === t)))

const rows = computed<Row[]>(() => {
  const next: Row[] = []
  for (const type of issues.groupKeys) {
    next.push({ key: `h-${type}`, kind: 'header', type, h: HEADER_H })
    if (!collapsed.value[type]) {
      for (const issue of issues.grouped[type] ?? []) {
        next.push({ key: issue.id, kind: 'issue', type, issue, h: ISSUE_H })
      }
      if (pendingOf(type) > 0) next.push({ key: `b-${type}`, kind: 'batch', type, h: BATCH_H })
    }
  }
  return next
})

const useVirtual = computed(() => issues.filtered.length > VIRTUAL_THRESHOLD)
const totalHeight = computed(() => rows.value.reduce((sum, row) => sum + rowHeight(row), 0))

const visible = computed(() => {
  if (!useVirtual.value) return { start: 0, end: rows.value.length, top: 0, bottom: 0 }
  let y = 0
  let start = 0
  const upper = Math.max(0, scrollTop.value - OVERSCAN * ISSUE_H)
  while (start < rows.value.length && y + rowHeight(rows.value[start]) < upper) {
    y += rowHeight(rows.value[start])
    start += 1
  }
  let end = start
  let height = y
  const lower = scrollTop.value + viewportHeight.value + OVERSCAN * ISSUE_H
  while (end < rows.value.length && height < lower) {
    height += rowHeight(rows.value[end])
    end += 1
  }
  return { start, end, top: y, bottom: Math.max(0, totalHeight.value - height) }
})

const visibleRows = computed(() => rows.value.slice(visible.value.start, visible.value.end))

function onScroll(e: Event) {
  const el = e.currentTarget as HTMLElement
  scrollTop.value = el.scrollTop
  viewportHeight.value = el.clientHeight
}
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

    <div class="issues-scroll" @scroll="onScroll">
      <div
        v-if="issues.groupKeys.length === 0"
        style="padding: 32px 20px; text-align: center; color: var(--ink-4)"
      >
        <div style="font-size: 13px">没有匹配的问题</div>
      </div>

      <div v-else :style="useVirtual ? { height: `${totalHeight}px`, position: 'relative' } : undefined">
        <div :style="useVirtual ? { transform: `translateY(${visible.top}px)` } : undefined">
          <template v-for="row in visibleRows" :key="row.key">
            <div :ref="(el) => setRowEl(row.key, el as Element | null)">
              <div v-if="row.kind === 'header'" class="group-head" @click="toggle(row.type)">
                <AppIcon name="chevR" :size="14" class="group-caret" :class="{ open: !collapsed[row.type] }" />
                <div class="group-icon" :style="{ background: TYPE_META[row.type].bg, color: TYPE_META[row.type].color }">
                  <span style="font-size: 10px; font-weight: 700">{{ TYPE_META[row.type].short }}</span>
                </div>
                <div class="group-title">{{ TYPE_META[row.type].label }}</div>
                <div class="group-count">
                  <span v-if="pendingOf(row.type) > 0" class="count-pill pending">{{ pendingOf(row.type) }} 待处理</span>
                  <span v-if="doneOf(row.type) > 0" class="count-pill done">{{ doneOf(row.type) }} 已处理</span>
                </div>
              </div>

              <IssueCard v-else-if="row.kind === 'issue'" :issue="row.issue" />

              <div v-else class="group-batch">
                <button @click="issues.batchAccept(row.type)">
                  <AppIcon name="check" :size="12" style="vertical-align: -1px; margin-right: 4px" />
                  全部接受 ({{ pendingOf(row.type) }})
                </button>
                <button @click="issues.batchReject(row.type)">
                  <AppIcon name="x" :size="12" style="vertical-align: -1px; margin-right: 4px" />
                  全部拒绝
                </button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>
