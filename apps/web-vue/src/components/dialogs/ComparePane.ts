import { Fragment, h, type FunctionalComponent, type VNode } from 'vue'
import type { Paragraph } from '../../types'
import { isSpanNode } from '../../types'
import { useIssuesStore } from '../../stores/issues'
import { useDocStore } from '../../stores/doc'
import { useVersionStore } from '../../stores/version'

interface Props {
  mode: 'original' | 'modified'
  focusIdx: number
}

// 对比弹窗单栏：原文 / 修改后，按当前差异序号高亮聚焦
const ComparePane: FunctionalComponent<Props> = (props) => {
  const issues = useIssuesStore()
  const version = useVersionStore()
  const paper = useDocStore().currentPaper
  let count = -1

  const renderNodes = (nodes: Paragraph): (string | VNode)[] =>
    nodes.map((n, i) => {
      if (!isSpanNode(n)) return n
      const d = n.issueId ? issues.decisions[n.issueId] : undefined
      const accepted = d?.action === 'accept'
      const custom = d?.action === 'custom'
      let text = n.original
      let cls = ''
      if (props.mode === 'modified') {
        if (accepted) {
          text = version.current(n.spanId) ?? n.suggested
          cls = 'hl hl-accepted'
        } else if (custom) {
          text = version.current(n.spanId) ?? d?.customContent ?? n.original
          cls = 'hl hl-custom'
        }
      }
      if (accepted || custom) {
        count++
        if (count === props.focusIdx) cls += ' focused'
      }
      if (!cls) return text
      // 自定义内容可能含格式标签，用 innerHTML 渲染
      return custom
        ? h('span', { key: i, class: cls, innerHTML: text })
        : h('span', { key: i, class: cls }, text)
    })

  const body: VNode[] = [
    h('h1', { style: { fontSize: '18px', textAlign: 'center', margin: '0 0 14px' } }, paper.title),
    ...paper.abstract.map((para, i) => h('p', { key: `a-${i}` }, renderNodes(para))),
  ]
  paper.sections.forEach((sec, si) => {
    body.push(
      h('h2', { key: `h-${si}`, style: { fontSize: '15px', fontWeight: 600, margin: '18px 0 8px' } }, sec.heading),
    )
    sec.paragraphs.forEach((para, pi) => {
      body.push(h('p', { key: `p-${si}-${pi}` }, renderNodes(para)))
    })
  })

  return h(Fragment, body)
}

ComparePane.props = ['mode', 'focusIdx']

export default ComparePane
