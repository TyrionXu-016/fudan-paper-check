import type { Decision } from '../types'
import { API_BASE, TOKEN_STORAGE_KEY } from './env'

export type ExportFormat = 'docx' | 'pdf' | 'md'

interface BackendDecision {
  issue_id: string
  action: Decision['action']
  custom_content?: string | null
}

interface ExportResponse {
  unresolved_count: number
  filename: string
  format: ExportFormat
}

function authHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra)
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  return headers
}

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(new URL(path, API_BASE), init)
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    throw new Error(body?.message || res.statusText || '导出请求失败')
  }
  return (body?.data ?? body) as T
}

function toBackendDecisions(decisions: Record<string, Decision>): BackendDecision[] {
  return Object.entries(decisions).map(([issueId, decision]) => ({
    issue_id: issueId,
    action: decision.action,
    custom_content: decision.customContent ?? null,
  }))
}

function filenameFromDisposition(value: string | null): string | null {
  if (!value) return null
  const utf8 = value.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8?.[1]) return decodeURIComponent(utf8[1])
  const ascii = value.match(/filename="?([^"]+)"?/i)
  return ascii?.[1] ?? null
}

function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export async function exportFromBackend(
  taskId: string,
  format: ExportFormat,
  decisions: Record<string, Decision>,
): Promise<ExportResponse> {
  const created = await requestJson<ExportResponse>(`/v1/tasks/${encodeURIComponent(taskId)}/export`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({
      format,
      decisions: toBackendDecisions(decisions),
    }),
  })

  const res = await fetch(new URL(`/v1/tasks/${encodeURIComponent(taskId)}/export/${format}`, API_BASE), {
    headers: authHeaders(),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.message || res.statusText || '导出文件下载失败')
  }

  const blob = await res.blob()
  const filename = filenameFromDisposition(res.headers.get('content-disposition')) || created.filename
  triggerDownload(blob, filename)
  return created
}
