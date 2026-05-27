import axios from 'axios'
import type { Rule } from '../types'
import { ISSUES, RULES, STAGES } from '../data/paper'

/**
 * 检测任务 API 客户端（方案 §4、§5）
 *
 * 当前 USE_MOCK = true：所有方法走本地模拟，无需后端即可演示。
 * 接入真实后端时：把 USE_MOCK 改为 false，并在 .env 配置 VITE_API_BASE，
 * 后端只需实现 GET /rule_bases、POST /check、GET /result/{taskId} 三个接口、
 * 且响应遵循 §4.1 的 { code, message, data } 外壳即可，前端其余逻辑无需改动。
 */
const USE_MOCK = true

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '/api',
  timeout: 15000,
})

// 统一响应解包（方案 §4.1）：业务层只拿 data 字段
http.interceptors.response.use(
  (res) => res.data?.data ?? res.data,
  (err) => {
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
}

export type ProgressCb = (percent: number) => void

// ---------------- 真实后端分支 ----------------
async function realGetRuleBases(): Promise<Rule[]> {
  return http.get('/rule_bases')
}

async function realUploadAndCheck(
  file: File,
  ruleId: string,
  onProgress: ProgressCb,
): Promise<UploadResp> {
  const form = new FormData()
  form.append('file', file)
  form.append('rule_base_id', ruleId)
  return http.post('/check', form, {
    onUploadProgress: (e) => onProgress(Math.round((e.loaded / (e.total || 1)) * 100)),
  })
}

async function realGetResult(taskId: string): Promise<ResultResp> {
  return http.get(`/result/${taskId}`)
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
  // 模拟分片上传进度
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
  // 按时间映射到检测阶段（不含末尾 DONE）
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
