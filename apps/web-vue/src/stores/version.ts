import { defineStore } from 'pinia'
import { reactive } from 'vue'
import type { ModRecord, ModSource, Paper, Paragraph } from '../types'
import { isSpanNode } from '../types'
import { nowTs } from '../utils/time'
import { useDocStore } from './doc'

const MAX_HISTORY_PER_SPAN = 20

function buildFromPaper(paper: Paper): Record<string, ModRecord[]> {
  const v: Record<string, ModRecord[]> = {}
  const walk = (nodes: Paragraph) => {
    for (const n of nodes) {
      if (isSpanNode(n)) {
        v[n.spanId] = [
          { content: n.original, source: 'original', ts: '初始', note: '原始论文文本' },
        ]
      }
    }
  }
  paper.abstract.forEach(walk)
  paper.sections.forEach((s) => s.paragraphs.forEach(walk))
  return v
}

// versionStore —— 管理预览区每个 span 节点的修改版本链（方案 §4.4）
// 论文换了（真后端 setPaper 或 reset 回 mock）时调 rebuildFromPaper 重建版本链
export const useVersionStore = defineStore('version', () => {
  const versions = reactive<Record<string, ModRecord[]>>(
    buildFromPaper(useDocStore().currentPaper),
  )

  function push(spanId: string, content: string, source: ModSource, note: string) {
    const next = [...(versions[spanId] || []), { content, source, ts: nowTs(), note }]
    versions[spanId] =
      next.length <= MAX_HISTORY_PER_SPAN ? next : [next[0], ...next.slice(-(MAX_HISTORY_PER_SPAN - 1))]
  }

  function setHistory(spanId: string, arr: ModRecord[]) {
    versions[spanId] = arr
  }

  function applyRevert(spanId: string, idx: number) {
    const target = versions[spanId]?.[idx]
    if (!target) return
    push(spanId, target.content, 'revert', `回退至版本 ${idx}`)
  }

  function popLast(spanId: string) {
    if ((versions[spanId]?.length ?? 0) > 1) {
      versions[spanId] = versions[spanId].slice(0, -1)
    }
  }

  function current(spanId: string): string | undefined {
    const list = versions[spanId]
    return list?.[list.length - 1]?.content
  }

  function rebuildFromPaper(paper: Paper) {
    const init = buildFromPaper(paper)
    for (const k of Object.keys(versions)) delete versions[k]
    Object.assign(versions, init)
  }

  function reset() {
    rebuildFromPaper(useDocStore().currentPaper)
  }

  return { versions, push, setHistory, applyRevert, popLast, current, rebuildFromPaper, reset }
})
