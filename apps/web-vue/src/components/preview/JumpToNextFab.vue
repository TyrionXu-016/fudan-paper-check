<script setup lang="ts">
import AppIcon from '../AppIcon.vue'
import { useIssuesStore } from '../../stores/issues'

const issues = useIssuesStore()

function jump() {
  const pending = issues.firstPending
  if (!pending) return
  issues.setActive(pending.id)
  setTimeout(() => {
    if (!pending.spanId) return
    const el = document.querySelector(`[data-span-id="${pending.spanId}"]`)
    if (el) el.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }, 50)
}
</script>

<template>
  <button v-if="issues.pendingCount > 0" class="jump-fab" @click="jump">
    <AppIcon name="arrowDown" :size="13" />
    <span>跳转下一处未处理 ({{ issues.pendingCount }})</span>
  </button>
</template>
