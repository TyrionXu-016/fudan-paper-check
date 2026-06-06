<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from '../AppIcon.vue'
import { useIssuesStore } from '../../stores/issues'

const props = defineProps<{ issueId: string }>()
const issues = useIssuesStore()

const action = computed(() => issues.decisions[props.issueId]?.action)
const active = computed(() => issues.activeIssueId === props.issueId)
</script>

<template>
  <div
    v-if="action === 'reject'"
    style="margin: 4px 0 14px; padding: 6px 12px; font-size: 12px; color: var(--ink-5); font-family: var(--font-ui); font-style: italic; text-align: center; text-indent: 0"
  >
    — 段落逻辑建议已忽略 —
  </div>

  <p
    v-else-if="action === 'accept'"
    style="background: var(--green-50); box-shadow: inset 0 -2px 0 var(--green-500); border-radius: 3px; padding: 2px 6px; margin: 0 0 14px"
  >
    然而，单纯加深网络深度会带来梯度消失与退化问题。
  </p>

  <div
    v-else
    @click="issues.setActive(issueId)"
    style="margin: 4px 0 14px; padding: 10px 14px; font-size: 12.5px; background: var(--amber-50); border: 1px dashed var(--amber-500); border-radius: 7px; color: #92400e; font-family: var(--font-ui); text-indent: 0; cursor: pointer; display: flex; align-items: flex-start; gap: 8px"
    :style="active ? { borderStyle: 'solid', boxShadow: '0 0 0 3px rgba(245,158,11,0.18)' } : {}"
  >
    <AppIcon name="sparkle" :size="14" style="margin-top: 2px; flex: none" />
    <div>
      <div style="font-weight: 600; margin-bottom: 2px">建议插入过渡句</div>
      <div style="color: #b45309">然而，单纯加深网络深度会带来梯度消失与退化问题。</div>
    </div>
  </div>
</template>
