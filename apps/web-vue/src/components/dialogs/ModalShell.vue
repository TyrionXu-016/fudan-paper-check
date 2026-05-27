<script setup lang="ts">
import { computed, useSlots } from 'vue'
import AppIcon from '../AppIcon.vue'

const props = withDefaults(
  defineProps<{ title: string; subtitle?: string; width?: number | string }>(),
  { width: 560 },
)
const emit = defineEmits<{ (e: 'close'): void }>()
const slots = useSlots()

const widthStyle = computed(() =>
  typeof props.width === 'number' ? `${props.width}px` : props.width,
)
</script>

<template>
  <div class="modal-backdrop" @click="emit('close')">
    <div class="modal" :style="{ width: widthStyle }" @click.stop>
      <div class="modal-head">
        <div>
          <div class="title">{{ title }}</div>
          <div v-if="subtitle" class="subtitle">{{ subtitle }}</div>
        </div>
        <button class="icon-btn close" @click="emit('close')"><AppIcon name="x" :size="16" /></button>
      </div>
      <div class="modal-body"><slot /></div>
      <div v-if="slots.footer" class="modal-foot"><slot name="footer" /></div>
    </div>
  </div>
</template>
