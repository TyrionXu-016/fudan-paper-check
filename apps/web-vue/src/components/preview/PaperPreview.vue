<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import ParaContent from './ParaContent'
import ParagraphLogicHint from './ParagraphLogicHint.vue'
import EditorToolbar from './EditorToolbar.vue'
import { useUiStore } from '../../stores/ui'
import { useEditorStore } from '../../stores/editor'
import { useDocStore } from '../../stores/doc'
import { useIssuesStore } from '../../stores/issues'
import type { Issue } from '../../types'

const ui = useUiStore()
const editor = useEditorStore()
const doc = useDocStore()
const issues = useIssuesStore()
// 真后端加载后 doc.currentPaper 是真实论文，否则回落到 mock PAPER
const paper = computed(() => doc.currentPaper)
const docIssues = computed(() => issues.issues.filter((issue) => issue.docLevel))
const topDocIssues = computed(() => docIssues.value.filter((issue) => docIssuePlacement(issue) === 'top'))
const abstractDocIssues = computed(() =>
  docIssues.value.filter((issue) => docIssuePlacement(issue) === 'abstract'),
)
const referenceDocIssues = computed(() =>
  docIssues.value.filter((issue) => docIssuePlacement(issue) === 'references'),
)
const referenceSectionIndex = computed(() =>
  paper.value.sections.findIndex((sec) => isReferenceHeading(sec.heading)),
)

const bodyEl = ref<HTMLElement | null>(null)

// 预览态：仅缩放
const scaleStyle = computed(() => ({ transform: `scale(${ui.zoom / 100})` }))

// 编辑态：缩放 + 页边距 + 字体/字号/行距
const paperStyle = computed(() => ({
  transform: `scale(${ui.zoom / 100})`,
  padding: `${editor.settings.marginV}cm ${editor.settings.marginH}cm`,
  fontFamily: editor.settings.fontFamily,
  fontSize: `${editor.settings.fontSize}px`,
  lineHeight: String(editor.settings.lineHeight),
}))

function syncBodyFromStore() {
  if (bodyEl.value && bodyEl.value.innerHTML !== editor.docHtml) {
    bodyEl.value.innerHTML = editor.docHtml
  }
}

let debounce: ReturnType<typeof setTimeout> | null = null
function onInput() {
  if (debounce) clearTimeout(debounce)
  debounce = setTimeout(() => {
    if (bodyEl.value) editor.commitHtml(bodyEl.value.innerHTML)
  }, 450)
}

function docIssueClass(issue: Issue) {
  const action = issues.decisions[issue.id]?.action
  return {
    active: issues.activeIssueId === issue.id,
    accepted: action === 'accept',
    rejected: action === 'reject',
    custom: action === 'custom',
  }
}

function docIssuePlacement(issue: Issue): 'top' | 'abstract' | 'references' {
  const text = `${issue.location} ${issue.summary} ${issue.explain}`.toLowerCase()
  if (/(参考文献|references|reference)/i.test(text)) return 'references'
  if (/(摘要|abstract)/i.test(text)) return 'abstract'
  return 'top'
}

function isReferenceHeading(heading: string) {
  return /(参考文献|references|reference)/i.test(heading)
}

// 进入编辑器：构建/恢复内容并写入 DOM
watch(
  () => ui.editMode,
  (on) => {
    if (on) {
      editor.enter()
      nextTick(syncBodyFromStore)
    }
  },
)

// 撤销/重做或外部变更时，把 store 内容写回 DOM
watch(
  () => editor.docHtml,
  () => {
    if (ui.editMode) nextTick(syncBodyFromStore)
  },
)

onMounted(() => {
  if (ui.editMode) {
    editor.enter()
    nextTick(syncBodyFromStore)
  }
})
</script>

<template>
  <EditorToolbar v-if="ui.editMode" />

  <div class="preview-scroll">
    <!-- 编辑态：整篇可编辑文档 -->
    <div v-if="ui.editMode" class="paper doc-editing" :style="paperStyle">
      <div v-if="editor.settings.headerText" class="doc-header" contenteditable="false">
        {{ editor.settings.headerText }}
      </div>
      <div ref="bodyEl" class="doc-body" contenteditable="true" @input="onInput" @blur="onInput" />
      <div v-if="editor.settings.footerText" class="doc-footer" contenteditable="false">
        {{ editor.settings.footerText }}
      </div>
    </div>

    <!-- 预览态：按句高亮 + 纠错联动 -->
    <div v-else class="paper" :style="scaleStyle">
      <h1>{{ paper.title }}</h1>
      <div class="author">{{ paper.author }}</div>

      <div
        v-if="topDocIssues.length"
        class="doc-issue-anchor"
        data-doc-issues
        data-doc-issue-placement="top"
      >
        <div class="doc-issue-title">全文检查点</div>
        <button
          v-for="issue in topDocIssues"
          :key="issue.id"
          class="doc-issue-marker"
          :class="docIssueClass(issue)"
          :data-doc-issue-id="issue.id"
          @click="issues.setActive(issue.id)"
        >
          <span class="doc-issue-loc">{{ issue.location }}</span>
          <span class="doc-issue-summary">{{ issue.summary }}</span>
        </button>
      </div>

      <div
        v-if="abstractDocIssues.length"
        class="doc-issue-anchor doc-issue-anchor-abstract"
        data-doc-issues
        data-doc-issue-placement="abstract"
      >
        <div class="doc-issue-title">摘要位置</div>
        <button
          v-for="issue in abstractDocIssues"
          :key="issue.id"
          class="doc-issue-marker"
          :class="docIssueClass(issue)"
          :data-doc-issue-id="issue.id"
          @click="issues.setActive(issue.id)"
        >
          <span class="doc-issue-loc">{{ issue.location }}</span>
          <span class="doc-issue-summary">{{ issue.summary }}</span>
        </button>
      </div>

      <template v-if="paper.abstract.length">
        <div class="abstract-label">摘 要</div>
        <p v-for="(para, i) in paper.abstract" :key="`a-${i}`"><ParaContent :para="para" /></p>
      </template>

      <template v-for="(sec, si) in paper.sections" :key="`sec-${si}`">
        <div
          v-if="si === referenceSectionIndex && referenceDocIssues.length"
          class="doc-issue-anchor doc-issue-anchor-references"
          data-doc-issues
          data-doc-issue-placement="references"
        >
          <div class="doc-issue-title">参考文献位置</div>
          <button
            v-for="issue in referenceDocIssues"
            :key="issue.id"
            class="doc-issue-marker"
            :class="docIssueClass(issue)"
            :data-doc-issue-id="issue.id"
            @click="issues.setActive(issue.id)"
          >
            <span class="doc-issue-loc">{{ issue.location }}</span>
            <span class="doc-issue-summary">{{ issue.summary }}</span>
          </button>
        </div>
        <h2>{{ sec.heading }}</h2>
        <template v-for="(para, pi) in sec.paragraphs" :key="`s-${si}-${pi}`">
          <p><ParaContent :para="para" /></p>
          <ParagraphLogicHint
            v-if="sec.paragraphLogic && sec.paragraphLogic.position === `between-${pi + 1}-${pi + 2}`"
            :issue-id="sec.paragraphLogic.issueId"
          />
        </template>
      </template>

      <div
        v-if="referenceSectionIndex < 0 && referenceDocIssues.length"
        class="doc-issue-anchor doc-issue-anchor-references"
        data-doc-issues
        data-doc-issue-placement="references"
      >
        <div class="doc-issue-title">参考文献位置</div>
        <button
          v-for="issue in referenceDocIssues"
          :key="issue.id"
          class="doc-issue-marker"
          :class="docIssueClass(issue)"
          :data-doc-issue-id="issue.id"
          @click="issues.setActive(issue.id)"
        >
          <span class="doc-issue-loc">{{ issue.location }}</span>
          <span class="doc-issue-summary">{{ issue.summary }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
