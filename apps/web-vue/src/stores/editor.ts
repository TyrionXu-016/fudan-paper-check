import { defineStore } from 'pinia'
import { computed, reactive, ref } from 'vue'
import { isSpanNode, type Paragraph } from '../types'
import { useVersionStore } from './version'
import { useDocStore } from './doc'

// 页面级排版设置（方案终期：行间距 / 页眉页脚 / 页边距 / 字体字号）
export interface DocSettings {
  marginV: number // 上下页边距 cm
  marginH: number // 左右页边距 cm
  fontFamily: string
  fontSize: number // px
  lineHeight: number
  headerText: string
  footerText: string
}

interface Snapshot {
  html: string
  settings: DocSettings
}

export const DEFAULT_SETTINGS: DocSettings = {
  marginV: 2.54,
  marginH: 3.17,
  fontFamily: '"Songti SC", "SimSun", serif',
  fontSize: 15,
  lineHeight: 1.8,
  headerText: '',
  footerText: '',
}

const MAX_SNAPSHOTS = 30

// editorStore —— 整篇文档编辑器：可编辑正文 HTML + 页面设置 + 快照式撤销/重做（全程留痕）
export const useEditorStore = defineStore('editor', () => {
  const docHtml = ref('')
  const settings = reactive<DocSettings>({ ...DEFAULT_SETTINGS })
  const dirty = ref(false)

  const snapshots = ref<Snapshot[]>([])
  const pointer = ref(-1)

  // 从论文（真后端或 mock）+ 已有决策构建初始可编辑 HTML
  function buildHtmlFromPaper(): string {
    const version = useVersionStore()
    const paper = useDocStore().currentPaper
    const resolve = (p: Paragraph) =>
      p
        .map((n) =>
          isSpanNode(n) ? (n.issueId ? version.current(n.spanId) ?? n.original : n.original) : n,
        )
        .join('')

    const parts: string[] = []
    parts.push(`<h1>${paper.title}</h1>`)
    if (paper.author) parts.push(`<p class="author">${paper.author}</p>`)
    if (paper.abstract.length) {
      parts.push(`<p class="label">摘　要</p>`)
      paper.abstract.forEach((p) => parts.push(`<p>${resolve(p)}</p>`))
    }
    paper.sections.forEach((s) => {
      parts.push(`<h2>${s.heading}</h2>`)
      s.paragraphs.forEach((p) => parts.push(`<p>${resolve(p)}</p>`))
    })
    return parts.join('')
  }

  function takeSnapshot(): Snapshot {
    return { html: docHtml.value, settings: { ...settings } }
  }

  function pushSnapshot() {
    // 丢弃 redo 分支
    snapshots.value = snapshots.value.slice(0, pointer.value + 1)
    snapshots.value.push(takeSnapshot())
    if (snapshots.value.length > MAX_SNAPSHOTS) snapshots.value.shift()
    pointer.value = snapshots.value.length - 1
  }

  // 进入编辑器：未编辑过则用当前决策结果重建；初始化快照基线
  function enter() {
    if (!dirty.value) {
      docHtml.value = buildHtmlFromPaper()
      snapshots.value = [takeSnapshot()]
      pointer.value = 0
    } else if (snapshots.value.length === 0) {
      snapshots.value = [takeSnapshot()]
      pointer.value = 0
    }
  }

  // 正文输入（已在组件层防抖）
  function commitHtml(html: string) {
    if (html === docHtml.value) return
    docHtml.value = html
    dirty.value = true
    pushSnapshot()
  }

  // 修改页面设置
  function setSetting<K extends keyof DocSettings>(key: K, value: DocSettings[K]) {
    if (settings[key] === value) return
    settings[key] = value
    dirty.value = true
    pushSnapshot()
  }

  function applySnapshot(s: Snapshot) {
    docHtml.value = s.html
    Object.assign(settings, s.settings)
  }

  function undo() {
    if (pointer.value > 0) {
      pointer.value--
      applySnapshot(snapshots.value[pointer.value])
    }
  }

  function redo() {
    if (pointer.value < snapshots.value.length - 1) {
      pointer.value++
      applySnapshot(snapshots.value[pointer.value])
    }
  }

  const canUndo = computed(() => pointer.value > 0)
  const canRedo = computed(() => pointer.value < snapshots.value.length - 1)
  const undoDepth = computed(() => pointer.value)

  function reset() {
    docHtml.value = ''
    dirty.value = false
    snapshots.value = []
    pointer.value = -1
    Object.assign(settings, DEFAULT_SETTINGS)
  }

  return {
    docHtml,
    settings,
    dirty,
    snapshots,
    pointer,
    buildHtmlFromPaper,
    enter,
    commitHtml,
    setSetting,
    undo,
    redo,
    canUndo,
    canRedo,
    undoDepth,
    reset,
  }
})
