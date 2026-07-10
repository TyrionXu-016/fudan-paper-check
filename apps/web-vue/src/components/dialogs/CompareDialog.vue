<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import AppIcon from '../AppIcon.vue'
import ComparePane from './ComparePane'
import { isSpanNode } from '../../types'
import type { Paragraph } from '../../types'
import { useIssuesStore } from '../../stores/issues'
import { useUiStore } from '../../stores/ui'
import { useDocStore } from '../../stores/doc'

const issues = useIssuesStore()
const ui = useUiStore()
const doc = useDocStore()
const diffIdx = ref(0)
const originalPane = ref<HTMLElement | null>(null)
const modifiedPane = ref<HTMLElement | null>(null)

const total = computed(() => {
  let n = 0
  const walk = (nodes: Paragraph) => {
    for (const node of nodes) {
      if (isSpanNode(node) && node.issueId) {
        const d = issues.decisions[node.issueId]
        if (d?.action === 'accept' || d?.action === 'custom') n++
      }
    }
  }
  const paper = doc.currentPaper
  paper.abstract.forEach(walk)
  paper.sections.forEach((s) => s.paragraphs.forEach(walk))
  return n
})

function scrollFocusedIntoView() {
  nextTick(() => {
    for (const pane of [originalPane.value, modifiedPane.value]) {
      const target = pane?.querySelector('.focused')
      target?.scrollIntoView({ block: 'center', behavior: 'smooth' })
    }
  })
}

watch(diffIdx, scrollFocusedIntoView)
</script>

<template>
  <div class="modal-backdrop" @click="ui.showCompare = false">
    <div class="modal" style="width: 85vw; height: 80vh" @click.stop>
      <div class="modal-head">
        <div>
          <div class="title">对比原始论文</div>
          <div class="subtitle">左：原文 · 右：修改后 · 检测到 {{ total }} 处差异</div>
        </div>
        <button class="icon-btn close" @click="ui.showCompare = false">
          <AppIcon name="x" :size="16" />
        </button>
      </div>

      <div class="diff-nav">
        <div style="font-weight: 500">
          第 <span style="color: var(--teal-700)">{{ Math.min(diffIdx + 1, total) || 0 }}</span> / {{ total }} 处修改
        </div>
        <div style="margin-left: auto; display: flex; gap: 6px">
          <button class="btn" @click="diffIdx = Math.max(0, diffIdx - 1)">
            <AppIcon name="chevL" :size="12" /> 上一处
          </button>
          <button class="btn" @click="diffIdx = Math.min(total - 1, diffIdx + 1)">
            下一处 <AppIcon name="chevR" :size="12" />
          </button>
        </div>
      </div>

      <div class="compare-body">
        <div class="compare-pane">
          <div class="compare-pane-head">原始论文</div>
          <div ref="originalPane" class="compare-pane-body"><ComparePane mode="original" :focus-idx="diffIdx" /></div>
        </div>
        <div class="compare-pane">
          <div class="compare-pane-head">修改后论文</div>
          <div ref="modifiedPane" class="compare-pane-body"><ComparePane mode="modified" :focus-idx="diffIdx" /></div>
        </div>
      </div>
    </div>
  </div>
</template>
