import { defineStore } from 'pinia'
import { reactive } from 'vue'
import type { ModRecord, ModSource, Paragraph } from '../types'
import { isSpanNode } from '../types'
import { PAPER } from '../data/paper'
import { nowTs } from '../utils/time'

function buildInitial(): Record<string, ModRecord[]> {
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
  PAPER.abstract.forEach(walk)
  PAPER.sections.forEach((s) => s.paragraphs.forEach(walk))
  return v
}

// versionStore —— 管理预览区每个 span 节点的修改版本链（方案 §4.4）
export const useVersionStore = defineStore('version', () => {
  const versions = reactive<Record<string, ModRecord[]>>(buildInitial())

  function push(spanId: string, content: string, source: ModSource, note: string) {
    versions[spanId] = [...(versions[spanId] || []), { content, source, ts: nowTs(), note }]
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

  function reset() {
    const init = buildInitial()
    for (const k of Object.keys(versions)) delete versions[k]
    Object.assign(versions, init)
  }

  return { versions, push, setHistory, applyRevert, popLast, current, reset }
})
