import axios from 'axios'
import type { Rule } from '../types'
import { ISSUES, RULES, STAGES } from '../data/paper'
import { API_BASE, TOKEN_STORAGE_KEY, UNAUTHORIZED_EVENT, USE_MOCK } from './env'
import type { BackendCheckReport } from './adapter'
import type { BackendDocumentView } from './docAdapter'

/**
 * 检测任务 API 客户端（方案 §4、§5；接入 fudan-pager-check 后端 mse-tyrion 分支）
 *
 * USE_MOCK=true（默认）：所有方法走本地模拟，无需后端即可演示。
 * 设置 VITE_USE_MOCK=false 即接真实后端 (/v1/rule_bases、/v1/check、/v1/tasks/{id}、/v1/result/{id})。
 * 请求自动从 localStorage 取 JWT 写入 Authorization 头；401 时清空并派发 fpc:unauthorized 事件。
 */

export const http = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
})

// 注入 JWT
http.interceptors.request.use((cfg) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) {
    cfg.headers = cfg.headers ?? {}
    ;(cfg.headers as Record<string, string>).Authorization = `Bearer ${token}`
  }
  return cfg
})

// 统一响应解包（方案 §4.1）+ 401 通知
http.interceptors.response.use(
  (res) => res.data?.data ?? res.data,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT))
    }
    const detail = err.response?.data
    return Promise.reject(new Error(detail?.message || err.message || '网络错误'))
  },
)

export type DetectStatus = 'DETECTING' | 'DONE' | 'ERROR'

export interface UploadResp {
  taskId: string
}

export interface ResultResp {
  status: DetectStatus
  stage: string
  percent: number
  issueCount: number
  message?: string
  /** DONE 时携带后端完整 CheckReport，便于任务层灌入 issuesStore */
  report?: BackendCheckReport
}

export type ProgressCb = (percent: number) => void

// ---------------- 真实后端分支（mse-tyrion） ----------------
async function realGetRuleBases(): Promise<Rule[]> {
  const arr = await http.get<unknown, Array<Record<string, unknown>>>('/v1/rule_bases')
  return (arr ?? []).map((x) => ({
    id: String(x.id),
    name: String(x.display_name ?? x.id),
    short: String(x.display_name ?? x.id),
    version: '',
    summary: x.summary as Rule['summary'],
  }))
}

async function realUploadAndCheck(
  file: File,
  ruleId: string,
  onProgress: ProgressCb,
): Promise<UploadResp> {
  const form = new FormData()
  form.append('file', file)
  form.append('rule_base_id', ruleId)
  const r = await http.post<unknown, Record<string, unknown>>('/v1/check', form, {
    onUploadProgress: (e) => onProgress(Math.round((e.loaded / (e.total || 1)) * 100)),
  })
  return { taskId: String(r.task_id ?? r.taskId) }
}

// 进度走 /v1/tasks/{id}（status + progress_percent + current_stage），DONE 后再取一次 /v1/result 拿 issue 数
async function realGetResult(taskId: string): Promise<ResultResp> {
  const t = await http.get<unknown, Record<string, unknown>>(`/v1/tasks/${taskId}`)
  const status = String(t.status ?? '').toLowerCase()
  if (status === 'failed') {
    return {
      status: 'ERROR',
      stage: 'ERROR',
      percent: 0,
      issueCount: 0,
      message: (t.error as string) || '检测失败',
    }
  }
  if (status === 'done') {
    let report: BackendCheckReport | undefined
    try {
      report = await http.get<unknown, BackendCheckReport>(`/v1/result/${taskId}`)
    } catch {
      // /v1/result 尚未就绪时继续轮询，避免 UI 进入“完成但空报告”的假完成态。
      return {
        status: 'DETECTING',
        stage: String(t.current_stage ?? 'DONE'),
        percent: 99,
        issueCount: 0,
        message: '检测结果整理中',
      }
    }
    return {
      status: 'DONE',
      stage: 'DONE',
      percent: 100,
      issueCount: report?.issues?.length ?? 0,
      report,
    }
  }
  return {
    status: 'DETECTING',
    stage: String(t.current_stage ?? 'PARSE'),
    percent: Number(t.progress_percent ?? 0),
    issueCount: 0,
  }
}

// ---------------- 本地模拟分支 ----------------
const mockTasks = new Map<string, number>()
const DETECT_MS = 4200

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms))
}

async function mockUploadAndCheck(
  _file: File,
  _ruleId: string,
  onProgress: ProgressCb,
): Promise<UploadResp> {
  for (let p = 0; p <= 100; p += 8) {
    onProgress(Math.min(100, p))
    await sleep(90)
  }
  onProgress(100)
  const taskId = `mock-${Date.now()}`
  mockTasks.set(taskId, Date.now())
  return { taskId }
}

function mockGetResult(taskId: string): ResultResp {
  const start = mockTasks.get(taskId)
  if (start === undefined) {
    return { status: 'ERROR', stage: 'ERROR', percent: 0, issueCount: 0, message: '任务不存在' }
  }
  const elapsed = Date.now() - start
  if (elapsed >= DETECT_MS) {
    return { status: 'DONE', stage: 'DONE', percent: 100, issueCount: ISSUES.length }
  }
  const phases = STAGES.filter((s) => s.id !== 'DONE')
  const idx = Math.min(phases.length - 1, Math.floor((elapsed / DETECT_MS) * phases.length))
  const s = phases[idx]
  return { status: 'DETECTING', stage: s.id, percent: s.pct, issueCount: 0 }
}

// ---------------- 对外统一接口 ----------------
export function getRuleBases(): Promise<Rule[]> {
  return USE_MOCK ? sleep(150).then(() => RULES) : realGetRuleBases()
}

export function uploadAndCheck(
  file: File,
  ruleId: string,
  onProgress: ProgressCb,
): Promise<UploadResp> {
  return USE_MOCK
    ? mockUploadAndCheck(file, ruleId, onProgress)
    : realUploadAndCheck(file, ruleId, onProgress)
}

export function getResult(taskId: string): Promise<ResultResp> {
  return USE_MOCK ? Promise.resolve(mockGetResult(taskId)) : realGetResult(taskId)
}

// 拉真后端的 DocumentView（论文结构 + 扁平 spans）；mock 模式返回 null
export async function fetchDocument(taskId: string): Promise<BackendDocumentView | null> {
  if (USE_MOCK) return null
  try {
    return await http.get<unknown, BackendDocumentView>(`/v1/result/${taskId}/document`)
  } catch {
    return null
  }
}
