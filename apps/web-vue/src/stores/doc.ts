import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { Paper } from '../types'
import { PAPER } from '../data/paper'

// docStore —— 真后端返回的论文内容；paper === null 时所有消费者回落到静态 mock PAPER
export const useDocStore = defineStore('doc', () => {
  const paper = ref<Paper | null>(null)

  // 统一对外读：真后端有数据用真，否则用 mock
  const currentPaper = computed<Paper>(() => paper.value ?? PAPER)
  const isLive = computed(() => paper.value !== null)

  function setPaper(p: Paper | null) {
    paper.value = p
  }

  function reset() {
    paper.value = null
  }

  return { paper, currentPaper, isLive, setPaper, reset }
})
