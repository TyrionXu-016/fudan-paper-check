import { onMounted, onUnmounted } from 'vue'
import { useIssuesStore } from '../stores/issues'
import { useUiStore } from '../stores/ui'
import { useEditorStore } from '../stores/editor'

// 全局键盘快捷键（方案 §3.8）：A/R/E、↑↓ 导航、Ctrl+Z/Ctrl+Shift+Z、? 帮助、Esc
export function useShortcut() {
  const issues = useIssuesStore()
  const ui = useUiStore()
  const editor = useEditorStore()

  const onKey = (e: KeyboardEvent) => {
    const t = e.target as HTMLElement
    const inField =
      !!t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)

    // 文档编辑器模式：撤销/重做（含文本+排版+页面设置）与退出
    if (ui.editMode) {
      const key = e.key.toLowerCase()
      if (key === 'z' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        if (e.shiftKey) editor.redo()
        else editor.undo()
        return
      }
      if (key === 'y' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault()
        editor.redo()
        return
      }
      if (e.key === 'Escape') {
        if (inField && t.blur) t.blur()
        ui.editMode = false
        return
      }
      return // 其余按键交给可编辑区正常输入
    }

    if (inField) {
      if (e.key === 'Escape') t.blur()
      return
    }

    if (e.key === 'Escape') {
      if (ui.anyModalOpen()) ui.closeAllModals()
      return
    }
    if (e.key === '?') {
      ui.showShortcuts = true
      return
    }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      issues.navigate(e.key === 'ArrowDown' ? 'down' : 'up')
      return
    }

    const k = e.key.toLowerCase()
    if ((e.ctrlKey || e.metaKey) && k === 'f') {
      e.preventDefault()
      ;(document.querySelector('.search input') as HTMLInputElement | null)?.focus()
      return
    }
    if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '=')) {
      e.preventDefault()
      ui.setZoom(ui.zoom + 10)
      return
    }
    if ((e.ctrlKey || e.metaKey) && e.key === '-') {
      e.preventDefault()
      ui.setZoom(ui.zoom - 10)
      return
    }
    if ((e.ctrlKey || e.metaKey) && k === 's') {
      e.preventDefault()
      ui.exportDialog = 'word'
      return
    }
    if (k === 'z' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      if (e.shiftKey) issues.redo()
      else issues.undo()
      return
    }
    if (k === 'y' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault()
      issues.redo()
      return
    }

    const active = issues.activeIssueId
    const activeIssue = active ? issues.issues.find((i) => i.id === active) : null
    if ((e.ctrlKey || e.metaKey) && k === 'a' && activeIssue) {
      e.preventDefault()
      issues.batchAccept(activeIssue.type)
      return
    }
    if ((e.ctrlKey || e.metaKey) && k === 'r' && activeIssue) {
      e.preventDefault()
      issues.batchReject(activeIssue.type)
      return
    }
    if (!active) return
    if (k === 'a' && !e.ctrlKey && !e.metaKey) {
      e.preventDefault()
      issues.decide(active, 'accept')
    } else if (k === 'r' && !e.ctrlKey && !e.metaKey) {
      e.preventDefault()
      issues.decide(active, 'reject')
    } else if (k === 'e' && !e.ctrlKey && !e.metaKey) {
      e.preventDefault()
      const issue = issues.issues.find((i) => i.id === active)
      if (issue) issues.decide(active, 'custom', issue.after)
    }
  }

  onMounted(() => window.addEventListener('keydown', onKey))
  onUnmounted(() => window.removeEventListener('keydown', onKey))
}
