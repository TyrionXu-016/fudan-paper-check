import { API_BASE, CHUNK_SIZE, TOKEN_STORAGE_KEY } from './env'

export interface ChunkUploadResult {
  taskId: string
}

export type ChunkProgress = (percent: number) => void

async function requestJson(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers)
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (!(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  const res = await fetch(new URL(path, API_BASE), { ...init, headers })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  const body = await res.json()
  return body?.data ?? body
}

export async function uploadInChunks(
  file: File,
  ruleId: string,
  onProgress: ChunkProgress,
): Promise<ChunkUploadResult> {
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE)
  const init = await requestJson('/v1/check/chunks/init', {
    method: 'POST',
    body: JSON.stringify({
      filename: file.name,
      size: file.size,
      chunks: totalChunks,
      rule_base_id: ruleId,
    }),
  })
  const uploadId = String(init.upload_id ?? init.uploadId ?? '')
  if (!uploadId) throw new Error('分片上传初始化失败')

  for (let index = 0; index < totalChunks; index += 1) {
    const start = index * CHUNK_SIZE
    const chunk = file.slice(start, Math.min(file.size, start + CHUNK_SIZE))
    const form = new FormData()
    form.append('upload_id', uploadId)
    form.append('index', String(index))
    form.append('total', String(totalChunks))
    form.append('chunk', chunk, `${file.name}.part${index}`)
    await requestJson('/v1/check/chunks/upload', { method: 'POST', body: form })
    onProgress(Math.round(((index + 1) / totalChunks) * 95))
  }

  const done = await requestJson('/v1/check/chunks/complete', {
    method: 'POST',
    body: JSON.stringify({ upload_id: uploadId }),
  })
  onProgress(100)
  return { taskId: String(done.task_id ?? done.taskId) }
}
