<script setup lang="ts">
import { ref } from 'vue'
import AppIcon from '../AppIcon.vue'
import { useTaskStore } from '../../stores/task'
import { useUiStore } from '../../stores/ui'

const task = useTaskStore()
const ui = useUiStore()
const drag = ref(false)
const inputEl = ref<HTMLInputElement | null>(null)

const MAX_SIZE = 50 * 1024 * 1024 // 50MB（方案 §3.3）
// 与后端 CHECK_ALLOWED_SUFFIXES 对齐：.pdf .docx .md .markdown
const ACCEPT = /\.(docx|pdf|md|markdown)$/i

function validateAndStart(file: File | undefined | null) {
  if (!file) return
  if (!ACCEPT.test(file.name)) {
    ui.toast('仅支持 .docx / .pdf / .md 格式，请重新选择', 'info')
    return
  }
  if (file.size > MAX_SIZE) {
    ui.toast(`文件大小 ${(file.size / 1024 / 1024).toFixed(1)}MB 超过 50MB 上限`, 'info')
    return
  }
  task.startUpload(file)
}

function onDrop(e: DragEvent) {
  e.preventDefault()
  drag.value = false
  validateAndStart(e.dataTransfer?.files?.[0])
}

function onPick(e: Event) {
  const input = e.target as HTMLInputElement
  validateAndStart(input.files?.[0])
  input.value = '' // 允许重复选择同一文件
}

function openPicker() {
  inputEl.value?.click()
}
</script>

<template>
  <!-- idle: dropzone -->
  <div
    v-if="task.taskState === 'idle'"
    class="upload"
    :class="{ drag }"
    @dragover.prevent="drag = true"
    @dragleave="drag = false"
    @drop="onDrop"
    @click="openPicker"
  >
    <input
      ref="inputEl"
      type="file"
      accept=".docx,.pdf,.md,.markdown"
      style="display: none"
      @change="onPick"
    />
    <div class="upload-icon"><AppIcon name="upload" :size="22" /></div>
    <div class="upload-title">拖拽 / 点击上传论文</div>
    <div class="upload-hint">
      支持 <span class="kbd">.docx</span> <span class="kbd">.pdf</span>
      <span class="kbd">.md</span> · 最大 50MB · &gt;10MB 自动分片
    </div>
  </div>

  <!-- uploading -->
  <div v-else-if="task.taskState === 'uploading'" class="upload uploaded">
    <div class="file-icon"><AppIcon name="file" :size="20" /></div>
    <div class="file-meta">
      <div class="file-name">{{ task.fileName }}</div>
      <div class="file-info">
        正在上传 ·
        <span style="color: var(--teal-700); font-weight: 600">{{ Math.round(task.uploadPct) }}%</span>
        <span class="dot">·</span>分片 {{ Math.ceil(task.uploadPct / 10) }}/10
      </div>
      <div class="upload-progress"><div :style="{ width: task.uploadPct + '%' }" /></div>
    </div>
    <button class="icon-btn" title="取消" @click="task.reset()"><AppIcon name="x" :size="16" /></button>
  </div>

  <!-- detecting / done -->
  <div v-else class="upload uploaded">
    <div class="file-icon"><AppIcon name="file" :size="20" /></div>
    <div class="file-meta">
      <div class="file-name">{{ task.fileName }}</div>
      <div class="file-info">
        {{ task.fileSizeText }}<span class="dot">·</span>{{ task.fileTypeLabel }}
        <template v-if="task.taskState === 'detecting'">
          <span class="dot">·</span><span style="color: var(--teal-700)">检测中…</span>
        </template>
        <template v-else>
          <span class="dot">·</span><span style="color: var(--green-700)">检测完成</span>
        </template>
      </div>
    </div>
    <button class="icon-btn" title="重新上传" @click="task.reset()">
      <AppIcon name="reset" :size="15" />
    </button>
  </div>
</template>
