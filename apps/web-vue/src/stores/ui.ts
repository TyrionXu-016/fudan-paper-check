import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ToastKind = 'info' | 'success'
export interface Toast {
  id: number
  msg: string
  kind: ToastKind
}

export interface HistoryTarget {
  spanId: string
  issueId: string | null
}

export const useUiStore = defineStore('ui', () => {
  const toasts = ref<Toast[]>([])
  function toast(msg: string, kind: ToastKind = 'info') {
    const id = Date.now() + Math.random()
    toasts.value = [...toasts.value, { id, msg, kind }]
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, 2400)
  }

  // preview controls
  const zoom = ref(100)
  const editMode = ref(false)
  function setZoom(z: number) {
    zoom.value = Math.max(50, Math.min(200, z))
  }

  // modals
  const historyDialog = ref<HistoryTarget | null>(null)
  const showRulePreview = ref(false)
  const showCompare = ref(false)
  const showShortcuts = ref(false)
  const exportDialog = ref<'word' | 'pdf' | null>(null)
  const showResetConfirm = ref(false)
  const showRuleSwitchConfirm = ref(false)
  const pendingRuleId = ref<string | null>(null)

  function closeAllModals() {
    historyDialog.value = null
    showRulePreview.value = false
    showCompare.value = false
    showShortcuts.value = false
    exportDialog.value = null
    showResetConfirm.value = false
    showRuleSwitchConfirm.value = false
    pendingRuleId.value = null
  }

  const anyModalOpen = () =>
    !!historyDialog.value ||
    showRulePreview.value ||
    showCompare.value ||
    showShortcuts.value ||
    !!exportDialog.value ||
    showResetConfirm.value ||
    showRuleSwitchConfirm.value

  return {
    toasts,
    toast,
    zoom,
    editMode,
    setZoom,
    historyDialog,
    showRulePreview,
    showCompare,
    showShortcuts,
    exportDialog,
    showResetConfirm,
    showRuleSwitchConfirm,
    pendingRuleId,
    closeAllModals,
    anyModalOpen,
  }
})


