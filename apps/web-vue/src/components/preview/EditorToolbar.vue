<script setup lang="ts">
import { ref } from 'vue'
import AppIcon from '../AppIcon.vue'
import { useEditorStore } from '../../stores/editor'

const editor = useEditorStore()
const showPageSetup = ref(false)

const FONTS = [
  { label: '宋体', value: '"Songti SC", "SimSun", serif' },
  { label: '黑体', value: '"Heiti SC", "SimHei", sans-serif' },
  { label: '楷体', value: '"Kaiti SC", "KaiTi", serif' },
  { label: '仿宋', value: '"FangSong", "STFangsong", serif' },
  { label: 'Times', value: '"Times New Roman", Times, serif' },
]
const SIZES = [12, 13, 14, 15, 16, 18, 20, 22, 26]
const LINE_HEIGHTS = [
  { label: '1.0', value: 1 },
  { label: '1.15', value: 1.15 },
  { label: '1.5', value: 1.5 },
  { label: '1.75', value: 1.75 },
  { label: '2.0', value: 2 },
]

// 选区内联格式（execCommand 触发正文 input → 组件层提交快照）
function exec(cmd: string, val?: string) {
  document.execCommand('styleWithCSS', false, 'true')
  document.execCommand(cmd, false, val ?? '')
}

function onFont(e: Event) {
  editor.setSetting('fontFamily', (e.target as HTMLSelectElement).value)
}
function onSize(e: Event) {
  editor.setSetting('fontSize', Number((e.target as HTMLSelectElement).value))
}
function onLine(e: Event) {
  editor.setSetting('lineHeight', Number((e.target as HTMLSelectElement).value))
}
</script>

<template>
  <div class="editor-toolbar">
    <!-- 正文字体 / 字号 / 行距（页面级默认） -->
    <div class="et-group">
      <select class="et-select" :value="editor.settings.fontFamily" title="正文字体" @change="onFont">
        <option v-for="f in FONTS" :key="f.value" :value="f.value">{{ f.label }}</option>
      </select>
      <select class="et-select narrow" :value="editor.settings.fontSize" title="正文字号" @change="onSize">
        <option v-for="s in SIZES" :key="s" :value="s">{{ s }}px</option>
      </select>
      <select class="et-select narrow" :value="editor.settings.lineHeight" title="行间距" @change="onLine">
        <option v-for="l in LINE_HEIGHTS" :key="l.value" :value="l.value">⇕ {{ l.label }}</option>
      </select>
    </div>

    <!-- 选区内联格式 -->
    <div class="et-group">
      <button title="加粗" @mousedown.prevent @click="exec('bold')"><b>B</b></button>
      <button title="斜体" @mousedown.prevent @click="exec('italic')"><i>I</i></button>
      <button title="下划线" @mousedown.prevent @click="exec('underline')"><u>U</u></button>
    </div>
    <div class="et-group">
      <button title="左对齐" @mousedown.prevent @click="exec('justifyLeft')">⬅</button>
      <button title="居中" @mousedown.prevent @click="exec('justifyCenter')">⬌</button>
      <button title="右对齐" @mousedown.prevent @click="exec('justifyRight')">➡</button>
    </div>
    <div class="et-group">
      <button title="减少缩进" @mousedown.prevent @click="exec('outdent')">⇤</button>
      <button title="增加缩进" @mousedown.prevent @click="exec('indent')">⇥</button>
    </div>

    <!-- 页面设置（页边距 / 页眉 / 页脚） -->
    <div class="et-group" style="position: relative">
      <button :class="{ on: showPageSetup }" @click="showPageSetup = !showPageSetup">
        <AppIcon name="settings" :size="13" /> 页面设置
      </button>
      <div v-if="showPageSetup" class="page-setup">
        <div class="ps-row">
          <label>上下页边距</label>
          <input
            type="number" step="0.1" min="0" max="6"
            :value="editor.settings.marginV"
            @input="editor.setSetting('marginV', Number(($event.target as HTMLInputElement).value))"
          />
          <span>cm</span>
        </div>
        <div class="ps-row">
          <label>左右页边距</label>
          <input
            type="number" step="0.1" min="0" max="6"
            :value="editor.settings.marginH"
            @input="editor.setSetting('marginH', Number(($event.target as HTMLInputElement).value))"
          />
          <span>cm</span>
        </div>
        <div class="ps-row">
          <label>页眉文字</label>
          <input
            type="text" placeholder="（空 = 不显示）"
            :value="editor.settings.headerText"
            @input="editor.setSetting('headerText', ($event.target as HTMLInputElement).value)"
          />
        </div>
        <div class="ps-row">
          <label>页脚文字</label>
          <input
            type="text" placeholder="（空 = 不显示）"
            :value="editor.settings.footerText"
            @input="editor.setSetting('footerText', ($event.target as HTMLInputElement).value)"
          />
        </div>
      </div>
    </div>

    <!-- 撤销 / 重做（全程留痕：文本 + 排版 + 页面设置） -->
    <div class="et-group" style="margin-left: auto">
      <button title="撤销 (⌘Z)" :disabled="!editor.canUndo" @click="editor.undo()">
        <AppIcon name="undo" :size="13" />
      </button>
      <button title="重做 (⌘⇧Z)" :disabled="!editor.canRedo" @click="editor.redo()">
        <AppIcon name="undo" :size="13" style="transform: scaleX(-1)" />
      </button>
      <span class="et-depth">{{ editor.undoDepth }} 步</span>
    </div>
  </div>
</template>
