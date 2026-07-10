<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import ParaContent from './ParaContent'
import ParagraphLogicHint from './ParagraphLogicHint.vue'
import EditorToolbar from './EditorToolbar.vue'
import { useUiStore } from '../../stores/ui'
import { useEditorStore } from '../../stores/editor'
import { useDocStore } from '../../stores/doc'
import { useIssuesStore } from '../../stores/issues'

const ui = useUiStore()
const editor = useEditorStore()
const doc = useDocStore()
const issues = useIssuesStore()
// 真后端加载后 doc.currentPaper 是真实论文，否则回落到 mock PAPER
const paper = computed(() => doc.currentPaper)

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
function commitNow() {
  if (!bodyEl.value) return
  if (debounce) {
    clearTimeout(debounce)
    debounce = null
  }
  editor.commitHtml(bodyEl.value.innerHTML)
}

function syncSpanEditsFromDom() {
  if (!bodyEl.value) return
  const edits = Array.from(bodyEl.value.querySelectorAll<HTMLElement>('[data-span-id]'))
    .map((el) => ({
      spanId: el.dataset.spanId || '',
      html: el.innerHTML,
    }))
    .filter((edit) => edit.spanId)
  issues.applyManualEdits(edits)
}

function onInput() {
  if (debounce) clearTimeout(debounce)
  debounce = setTimeout(() => {
    if (bodyEl.value) editor.commitHtml(bodyEl.value.innerHTML)
  }, 450)
}

// 进入编辑器：构建/恢复内容并写入 DOM
watch(
  () => ui.editMode,
  (on, wasOn) => {
    if (on) {
      editor.enter()
      nextTick(syncBodyFromStore)
    } else if (wasOn) {
      commitNow()
      syncSpanEditsFromDom()
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

      <template v-if="paper.abstract.length">
        <div class="abstract-label">摘 要</div>
        <p v-for="(para, i) in paper.abstract" :key="`a-${i}`"><ParaContent :para="para" /></p>
      </template>

      <template v-for="(sec, si) in paper.sections" :key="`sec-${si}`">
        <h2>{{ sec.heading }}</h2>
        <template v-for="(para, pi) in sec.paragraphs" :key="`s-${si}-${pi}`">
          <p><ParaContent :para="para" /></p>
          <ParagraphLogicHint
            v-if="sec.paragraphLogic && sec.paragraphLogic.position === `between-${pi + 1}-${pi + 2}`"
            :issue-id="sec.paragraphLogic.issueId"
          />
        </template>
      </template>
    </div>
  </div>
</template>
