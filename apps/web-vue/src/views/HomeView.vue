<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppIcon from '../components/AppIcon.vue'
import UploadCard from '../components/left/UploadCard.vue'
import RuleSelector from '../components/left/RuleSelector.vue'
import IssueList from '../components/left/IssueList.vue'
import DetectingPlaceholder from '../components/left/DetectingPlaceholder.vue'
import PreviewToolbar from '../components/preview/PreviewToolbar.vue'
import PaperPreview from '../components/preview/PaperPreview.vue'
import JumpToNextFab from '../components/preview/JumpToNextFab.vue'
import HistoryDialog from '../components/dialogs/HistoryDialog.vue'
import RulePreviewDialog from '../components/dialogs/RulePreviewDialog.vue'
import CompareDialog from '../components/dialogs/CompareDialog.vue'
import ShortcutHelpDialog from '../components/dialogs/ShortcutHelpDialog.vue'
import ExportDialog from '../components/dialogs/ExportDialog.vue'
import LoginModal from '../components/dialogs/LoginModal.vue'
import ModalShell from '../components/dialogs/ModalShell.vue'
import { RULES, STAGES } from '../data/paper'
import { useTaskStore } from '../stores/task'
import { useIssuesStore } from '../stores/issues'
import { useVersionStore } from '../stores/version'
import { useUiStore } from '../stores/ui'
import { useEditorStore } from '../stores/editor'
import { useAuthStore } from '../stores/auth'
import { AUTH_REQUIRED } from '../api/env'
import { useShortcut } from '../composables/useShortcut'

const task = useTaskStore()
const issues = useIssuesStore()
const version = useVersionStore()
const ui = useUiStore()
const editor = useEditorStore()
const auth = useAuthStore()

// 真实后端模式下，若已有 token 则拉取当前用户信息（失败会自动登出），并拉真实规范列表
onMounted(() => {
  if (AUTH_REQUIRED) {
    if (auth.token) auth.fetchMe()
    task.loadRuleBases()
  }
})

useShortcut()

const showTweaks = ref(false)
const stageLabel = computed(
  () => STAGES.find((s) => s.id === task.detectStage)?.label || '检测中',
)

const acceptPct = computed(() => (issues.acceptedCount / issues.totalIssues) * 100)
const customPct = computed(() => (issues.customCount / issues.totalIssues) * 100)
const rejectPct = computed(() => (issues.rejectedCount / issues.totalIssues) * 100)

function doReset() {
  task.reset()
  issues.reset()
  version.reset()
  editor.reset()
  ui.showResetConfirm = false
  ui.toast('已重置全部修改')
}

const TWEAK_STATES = [
  { v: 'idle', l: '空闲' },
  { v: 'uploading', l: '上传' },
  { v: 'detecting', l: '检测' },
  { v: 'done', l: '完成' },
] as const
</script>

<template>
  <div class="app">
    <!-- ============ TOP BAR ============ -->
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">论</div>
        <span class="brand-name">论文纠错 Agent</span>
        <span class="brand-tag">v0.9 · Beta</span>
      </div>
      <div class="topbar-progress">
        <div v-if="task.taskState === 'idle'" class="detect-pill idle">
          <span class="stage-dot" /><span>等待上传论文</span>
        </div>
        <div v-else-if="task.taskState === 'uploading'" class="detect-pill">
          <span class="stage-dot" /><span>上传中 · 分片传输</span>
          <div class="stage-bar"><div class="stage-fill" :style="{ width: task.uploadPct + '%' }" /></div>
          <span class="stage-pct">{{ Math.round(task.uploadPct) }}%</span>
        </div>
        <div v-else-if="task.taskState === 'detecting'" class="detect-pill">
          <span class="stage-dot" /><span>{{ stageLabel }}</span>
          <div class="stage-bar"><div class="stage-fill" :style="{ width: task.detectPct + '%' }" /></div>
          <span class="stage-pct">{{ task.detectPct }}%</span>
        </div>
        <div v-else class="detect-pill done">
          <span class="stage-dot" /><span>检测完成 · 共 {{ issues.totalIssues }} 项问题</span>
        </div>
      </div>
      <div class="topbar-actions">
        <div v-if="AUTH_REQUIRED && auth.isAuthed" class="auth-chip">
          <AppIcon name="check" :size="12" />
          <span>{{ auth.user?.name || auth.user?.email || '已登录' }}</span>
          <button class="auth-link" title="退出登录" @click="auth.logout()">退出</button>
        </div>
        <button class="icon-btn has-badge" title="通知" @click="ui.toast('暂无新通知')">
          <AppIcon name="info" :size="16" /><span class="badge" />
        </button>
        <button class="icon-btn" title="键盘快捷键" @click="ui.showShortcuts = true">
          <AppIcon name="help" :size="16" />
        </button>
        <button class="icon-btn" title="设置 / 演示控制" @click="showTweaks = !showTweaks">
          <AppIcon name="settings" :size="16" />
        </button>
      </div>
    </header>

    <!-- ============ MAIN SPLIT ============ -->
    <div class="split">
      <aside class="left-panel">
        <div class="section">
          <div class="section-head">
            <div class="section-title">论文文件</div>
            <button
              v-if="task.taskState === 'done'"
              style="font-size: 11px; color: var(--ink-4); background: none; border: none; cursor: pointer"
              @click="task.reset()"
            >
              重新上传
            </button>
          </div>
          <UploadCard />
        </div>

        <div class="section">
          <div class="section-head">
            <div class="section-title">检测规范</div>
            <span style="font-size: 11px; color: var(--ink-4)">{{ RULES.length }} 个可选</span>
          </div>
          <RuleSelector />
        </div>

        <IssueList v-if="task.taskState === 'done'" />
        <DetectingPlaceholder v-else-if="task.taskState === 'detecting'" />
        <div v-else style="padding: 40px 24px; text-align: center; color: var(--ink-4); font-size: 13px">
          {{ task.taskState === 'idle' ? '上传论文后将在此显示检测出的问题列表' : '上传完成后将自动开始检测…' }}
        </div>
      </aside>

      <main class="right-panel">
        <template v-if="task.taskState === 'done' || task.taskState === 'detecting'">
          <PreviewToolbar />
          <PaperPreview />
          <JumpToNextFab />
        </template>
        <div v-else style="flex: 1; display: grid; place-items: center; color: var(--ink-4)">
          <div style="text-align: center; max-width: 360px">
            <div
              style="width: 72px; height: 72px; border-radius: 18px; margin: 0 auto 18px; background: var(--bg-sunken); border: 1px solid var(--border); display: grid; place-items: center; color: var(--ink-5)"
            >
              <AppIcon name="file" :size="28" />
            </div>
            <div style="font-size: 16px; font-weight: 500; color: var(--ink-2); margin-bottom: 6px">
              尚未上传论文
            </div>
            <div style="font-size: 13px">上传 .docx 或 .pdf 文件后，论文将在此处实时渲染。</div>
          </div>
        </div>
      </main>
    </div>

    <!-- ============ BOTTOM BAR ============ -->
    <footer class="bottombar">
      <div class="progress-summary">
        <span class="nums">
          <span class="done">{{ issues.decidedCount }}</span>
          <span class="sep">/</span>{{ issues.totalIssues }}
        </span>
        <span style="color: var(--ink-4); font-size: 12px">已处理</span>
        <div class="progress-track">
          <div class="seg accepted" :style="{ width: acceptPct + '%' }" />
          <div class="seg custom" :style="{ left: acceptPct + '%', width: customPct + '%' }" />
          <div class="seg rejected" :style="{ left: acceptPct + customPct + '%', width: rejectPct + '%' }" />
        </div>
      </div>

      <div class="undo-counter" title="可撤销步数">
        <AppIcon name="undo" :size="12" /> 可撤销
        <strong>{{ ui.editMode ? editor.undoDepth : issues.undoStack.length }}</strong> 步
        <kbd>⌘Z</kbd>
      </div>

      <div class="spacer" />

      <button class="btn btn-ghost" @click="ui.showResetConfirm = true">
        <AppIcon name="reset" :size="13" /> 重置所有修改
      </button>
      <button class="btn" @click="ui.showCompare = true">
        <AppIcon name="compare" :size="13" /> 对比原始论文
      </button>
      <button class="btn" @click="ui.exportDialog = 'pdf'">
        <AppIcon name="download" :size="13" /> 导出 PDF
      </button>
      <button class="btn btn-primary" @click="ui.exportDialog = 'word'">
        <AppIcon name="download" :size="13" /> 导出 Word
      </button>
    </footer>

    <!-- ============ MODALS ============ -->
    <HistoryDialog v-if="ui.historyDialog" />
    <RulePreviewDialog v-if="ui.showRulePreview" />
    <CompareDialog v-if="ui.showCompare" />
    <ShortcutHelpDialog v-if="ui.showShortcuts" />
    <ExportDialog v-if="ui.exportDialog" />
    <LoginModal v-if="AUTH_REQUIRED && !auth.isAuthed" />
    <ModalShell
      v-if="ui.showResetConfirm"
      title="重置所有修改？"
      :width="420"
      @close="ui.showResetConfirm = false"
    >
      <div style="font-size: 13.5px; line-height: 1.7; color: var(--ink-3)">
        将清空所有 <strong>{{ issues.decidedCount }}</strong> 项决策、版本历史与撤销栈。此操作不可撤销。
      </div>
      <template #footer>
        <button class="btn" @click="ui.showResetConfirm = false">取消</button>
        <button class="btn" style="color: #b91c1c; border-color: #fecaca" @click="doReset">确认重置</button>
      </template>
    </ModalShell>

    <!-- ============ TOASTS ============ -->
    <div class="toasts">
      <div v-for="t in ui.toasts" :key="t.id" class="toast" :class="t.kind">
        <AppIcon v-if="t.kind === 'success'" name="check" :size="14" />
        {{ t.msg }}
      </div>
    </div>

    <!-- ============ TWEAKS (演示控制) ============ -->
    <div v-if="showTweaks" class="tweaks">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px">
        <div class="tweaks-title">演示控制</div>
        <button class="icon-btn" style="width: 22px; height: 22px" @click="showTweaks = false">
          <AppIcon name="x" :size="12" />
        </button>
      </div>
      <div class="tweaks-row">
        <label>任务状态机</label>
        <div class="seg">
          <button
            v-for="o in TWEAK_STATES"
            :key="o.v"
            :class="{ on: task.taskState === o.v }"
            @click="task.setState(o.v)"
          >
            {{ o.l }}
          </button>
        </div>
      </div>
      <div class="tweaks-row">
        <label>检测进度阶段</label>
        <select class="filter-select" :value="task.detectStage" @change="task.setStage(($event.target as HTMLSelectElement).value)">
          <option v-for="s in STAGES" :key="s.id" :value="s.id">{{ s.label }} ({{ s.pct }}%)</option>
        </select>
      </div>
      <div
        style="font-size: 11px; color: var(--ink-4); margin-top: 12px; line-height: 1.5; border-top: 1px solid var(--border); padding-top: 10px"
      >
        重点演示：第 2 章布局 + 第 3 章模块（FSM / 上传 / 规范 / 列表 / 决策 / 预览 / 历史 / 快捷键 / 对比）
      </div>
    </div>
  </div>
</template>
