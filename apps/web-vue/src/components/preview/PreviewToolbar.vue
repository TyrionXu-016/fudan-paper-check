<script setup lang="ts">
import AppIcon from '../AppIcon.vue'
import { useUiStore } from '../../stores/ui'

const ui = useUiStore()
</script>

<template>
  <div class="preview-toolbar">
    <div class="toolbar-group">
      <button :class="{ on: !ui.editMode }" @click="ui.editMode = false">预览</button>
      <button :class="{ on: ui.editMode }" @click="ui.editMode = true">
        <AppIcon name="edit" :size="12" /> 手动编辑
      </button>
    </div>

    <div class="toolbar-group">
      <button title="缩小" @click="ui.setZoom(ui.zoom - 10)"><AppIcon name="zoomOut" :size="13" /></button>
      <span class="zoom-display">{{ ui.zoom }}%</span>
      <button title="放大" @click="ui.setZoom(ui.zoom + 10)"><AppIcon name="zoomIn" :size="13" /></button>
      <button style="font-size: 11px" @click="ui.setZoom(100)">适合</button>
    </div>

    <div class="legend">
      <span class="swatch"><span class="dot amber" /> 待处理</span>
      <span class="swatch"><span class="dot green" /> 已接受</span>
      <span class="swatch"><span class="dot blue" /> 自定义</span>
    </div>
  </div>
</template>
