import { h, type FunctionalComponent, type VNode } from 'vue'
import type { Paragraph } from '../../types'
import { isSpanNode } from '../../types'
import { useIssuesStore } from '../../stores/issues'
import { useUiStore } from '../../stores/ui'

// 渲染单个段落的内联内容：纯文本片段 + 可交互高亮 span。
// 用函数式组件以精确控制内联节点，避免模板空白把中文撑开。
const ParaContent: FunctionalComponent<{ para: Paragraph }> = (props) => {
  const issues = useIssuesStore()
  const ui = useUiStore()
  const editable = ui.editMode

  const out: (string | VNode)[] = props.para.map((node, i) => {
    if (!isSpanNode(node)) return node
    const { spanId, original, suggested, issueId } = node
    if (!issueId) return original

    const decision = issues.decisions[issueId]
    let text = original
    let cls = 'hl hl-pending'
    let asHtml = false // custom/manual 内容可能含格式标签，用 innerHTML 渲染
    if (decision?.action === 'accept') {
      text = suggested
      cls = 'hl hl-accepted'
    } else if (decision?.action === 'custom') {
      text = decision.customContent ?? original
      cls = 'hl hl-custom'
      asHtml = true
    } else if (decision?.action === 'reject') {
      text = original
      cls = 'hl hl-rejected'
    }
    if (issues.activeIssueId === issueId) cls += ' focused'
    if (editable) cls += ' editable'

    const props_: Record<string, unknown> = {
      key: i,
      class: cls,
      'data-span-id': spanId,
      contenteditable: editable ? 'true' : 'false',
      onClick: (e: MouseEvent) => {
        e.stopPropagation()
        if (editable) return // 编辑态下点击仅定位光标
        if (decision?.action === 'accept' || decision?.action === 'custom') {
          ui.historyDialog = { spanId, issueId }
        } else {
          issues.setActive(issueId)
        }
      },
    }
    if (editable) {
      props_.onBlur = (e: FocusEvent) => {
        const el = e.target as HTMLElement
        issues.applyManualEdit(spanId, el.innerHTML)
      }
    }
    if (asHtml) props_.innerHTML = text

    return h('span', props_, asHtml ? undefined : text)
  })

  return out as unknown as VNode
}

ParaContent.props = ['para']

export default ParaContent
