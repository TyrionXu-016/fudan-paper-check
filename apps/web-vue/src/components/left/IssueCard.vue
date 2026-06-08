<script setup lang="ts">
import { computed, ref } from 'vue'
import AppIcon from '../AppIcon.vue'
import type { Issue } from '../../types'
import { TYPE_META } from '../../data/paper'
import { useIssuesStore } from '../../stores/issues'

const props = defineProps<{ issue: Issue }>()
const issues = useIssuesStore()

const meta = computed(() => TYPE_META[props.issue.type])
const decision = computed(() => issues.decisions[props.issue.id])
const isAccepted = computed(() => decision.value?.action === 'accept')
const isRejected = computed(() => decision.value?.action === 'reject')
const isCustom = computed(() => decision.value?.action === 'custom')
const decided = computed(() => isAccepted.value || isRejected.value || isCustom.value)
const isActive = computed(() => issues.activeIssueId === props.issue.id)

const afterText = computed(() =>
  isCustom.value ? decision.value?.customContent ?? props.issue.after : props.issue.after,
)

const customMode = ref(false)
const customText = ref(decision.value?.customContent || props.issue.after)

function startCustom() {
  customText.value = decision.value?.customContent || props.issue.after
  customMode.value = true
}
function applyCustom() {
  issues.decide(props.issue.id, 'custom', customText.value)
  customMode.value = false
}

function focusIssue() {
  issues.setActive(props.issue.id)
  setTimeout(() => {
    const selector = props.issue.spanId
      ? `[data-span-id="${props.issue.spanId}"]`
      : `[data-doc-issue-id="${props.issue.id}"], [data-doc-issues]`
    const el = document.querySelector(selector)
    if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }, 50)
}
</script>

<template>
  <div
    class="issue"
    :class="{ active: isActive, accepted: isAccepted, rejected: isRejected, custom: isCustom }"
    @click="focusIssue"
  >
    <div class="issue-tag" :style="{ background: meta.color }">{{ meta.short }}</div>
    <div class="issue-loc">
      <span class="severity-dot" :class="`severity-${issue.severity}`" />
      {{ issue.location }}
    </div>
    <div style="font-size: 13.5px; font-weight: 500; margin-bottom: 8px; color: var(--ink-1)">
      {{ issue.summary }}
    </div>

    <div class="diff">
      <div class="diff-row before">
        <div class="diff-label">原文</div>
        <div class="diff-text" style="white-space: pre-line">{{ issue.before }}</div>
      </div>
      <div class="diff-row" :class="isCustom ? 'custom-row' : 'after'">
        <div class="diff-label">{{ isCustom ? '自定义' : '建议' }}</div>
        <div class="diff-text" style="white-space: pre-line">{{ afterText }}</div>
      </div>
    </div>

    <div class="issue-explain">
      <AppIcon name="sparkle" :size="13" />
      <span>{{ issue.explain }}</span>
    </div>

    <!-- custom edit mode -->
    <div v-if="customMode" class="custom-input" @click.stop>
      <textarea v-model="customText" autofocus />
      <div class="custom-input-actions">
        <button class="btn btn-primary" @click="applyCustom">
          <AppIcon name="check" :size="13" /> 应用自定义
        </button>
        <button class="btn" @click="customMode = false">取消</button>
      </div>
    </div>

    <!-- decided state -->
    <div
      v-else-if="decided"
      class="issue-state"
      :class="isAccepted ? 'accepted' : isRejected ? 'rejected' : 'custom'"
    >
      <template v-if="isAccepted"><AppIcon name="check" :size="13" /> 已接受 AI 建议</template>
      <template v-else-if="isRejected"><AppIcon name="x" :size="13" /> 已拒绝</template>
      <template v-else><AppIcon name="edit" :size="13" /> 自定义修改</template>
      <button class="undo-link" @click.stop="issues.undoIssue(issue.id)">撤销</button>
    </div>

    <!-- pending actions -->
    <div v-else class="issue-actions" @click.stop>
      <button class="btn btn-accept" title="接受 AI 建议 (A)" @click="issues.decide(issue.id, 'accept')">
        <AppIcon name="check" :size="14" /><span class="shortcut">A</span>
      </button>
      <button class="btn btn-reject" title="拒绝建议 (R)" @click="issues.decide(issue.id, 'reject')">
        <AppIcon name="x" :size="14" /><span class="shortcut">R</span>
      </button>
      <button class="btn btn-custom" title="自定义修改 (E)" @click="startCustom">
        <AppIcon name="edit" :size="14" /><span class="shortcut">E</span>
      </button>
    </div>
  </div>
</template>
