<script setup lang="ts">
import { computed } from 'vue'
import AppIcon from '../AppIcon.vue'
import { STAGES } from '../../data/paper'
import { useTaskStore } from '../../stores/task'

const task = useTaskStore()
const currIdx = computed(() => STAGES.findIndex((s) => s.id === task.detectStage))
const visibleStages = STAGES.filter((s) => s.id !== 'DONE')

function stateOf(i: number) {
  if (i < currIdx.value) return 'done'
  if (i === currIdx.value) return 'active'
  return 'pending'
}
</script>

<template>
  <div class="fsm-skeleton">
    <div style="font-weight: 600; font-size: 14px; color: var(--ink-2)">正在检测论文 …</div>
    <div style="font-size: 12px; color: var(--ink-4); margin-top: 6px">
      SSE 实时推送进度，断线后自动重连
    </div>
    <div class="fsm-stages">
      <div v-for="(s, i) in visibleStages" :key="s.id" class="fsm-stage" :class="stateOf(i)">
        <div class="stage-mini">
          <AppIcon v-if="stateOf(i) === 'done'" name="check" :size="10" />
        </div>
        <div>{{ s.label }}</div>
        <div v-if="stateOf(i) === 'active'" style="margin-left: auto; font-size: 11px; color: var(--teal-700)">
          进行中
        </div>
      </div>
    </div>
  </div>
</template>
