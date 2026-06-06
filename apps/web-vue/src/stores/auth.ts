import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as api from '../api/authApi'
import type { AuthUser } from '../api/authApi'
import { TOKEN_STORAGE_KEY, UNAUTHORIZED_EVENT } from '../api/env'

// authStore —— JWT 登录态：登录/注册/登出 + 持久化 token + 监听 401 自动登出
export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const token = ref<string | null>(localStorage.getItem(TOKEN_STORAGE_KEY))
  const submitting = ref(false)
  const error = ref('')

  const isAuthed = computed(() => !!token.value)

  function setToken(t: string | null) {
    token.value = t
    if (t) localStorage.setItem(TOKEN_STORAGE_KEY, t)
    else localStorage.removeItem(TOKEN_STORAGE_KEY)
  }

  async function doLogin(email: string, password: string) {
    submitting.value = true
    error.value = ''
    try {
      const res = await api.login(email, password)
      setToken(res.access_token)
      user.value = res.user
    } catch (e) {
      error.value = e instanceof Error ? e.message : '登录失败'
      throw e
    } finally {
      submitting.value = false
    }
  }

  async function doRegister(email: string, password: string, name: string) {
    submitting.value = true
    error.value = ''
    try {
      const res = await api.register(email, password, name)
      setToken(res.access_token)
      user.value = res.user
    } catch (e) {
      error.value = e instanceof Error ? e.message : '注册失败'
      throw e
    } finally {
      submitting.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      user.value = await api.me()
    } catch {
      setToken(null)
      user.value = null
    }
  }

  function logout() {
    setToken(null)
    user.value = null
  }

  // 后端返回 401 时（任意请求触发）自动登出
  window.addEventListener(UNAUTHORIZED_EVENT, () => {
    token.value = null
    user.value = null
  })

  return { user, token, submitting, error, isAuthed, doLogin, doRegister, fetchMe, logout }
})
