<script setup lang="ts">
import { ref } from 'vue'
import ModalShell from './ModalShell.vue'
import AppIcon from '../AppIcon.vue'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const mode = ref<'login' | 'register'>('login')
const email = ref('')
const password = ref('')
const name = ref('')

async function submit() {
  try {
    if (mode.value === 'login') {
      await auth.doLogin(email.value.trim(), password.value)
    } else {
      await auth.doRegister(email.value.trim(), password.value, name.value.trim() || email.value)
    }
  } catch {
    /* error already in auth.error */
  }
}
</script>

<template>
  <ModalShell
    :title="mode === 'login' ? '登录' : '注册'"
    :subtitle="mode === 'login' ? '使用账号登录后再上传论文' : '创建新账号'"
    :width="420"
    :show-close="false"
  >
    <div style="display: flex; flex-direction: column; gap: 10px">
      <label v-if="mode === 'register'" class="auth-field">
        <span>姓名</span>
        <input v-model="name" type="text" placeholder="可选，默认取邮箱前缀" />
      </label>
      <label class="auth-field">
        <span>邮箱</span>
        <input v-model="email" type="email" required autocomplete="email" placeholder="you@example.com" />
      </label>
      <label class="auth-field">
        <span>密码</span>
        <input
          v-model="password"
          type="password"
          required
          autocomplete="current-password"
          placeholder="至少 8 位"
          @keyup.enter="submit"
        />
      </label>
      <div v-if="auth.error" style="color: #b91c1c; font-size: 12.5px">{{ auth.error }}</div>
    </div>

    <template #footer>
      <button
        class="btn"
        style="margin-right: auto; color: var(--ink-3)"
        @click="mode = mode === 'login' ? 'register' : 'login'"
      >
        {{ mode === 'login' ? '没有账号？注册 →' : '← 已有账号？登录' }}
      </button>
      <button class="btn btn-primary" :disabled="auth.submitting" @click="submit">
        <AppIcon v-if="!auth.submitting" name="check" :size="13" />
        {{ auth.submitting ? '提交中…' : mode === 'login' ? '登录' : '注册' }}
      </button>
    </template>
  </ModalShell>
</template>
