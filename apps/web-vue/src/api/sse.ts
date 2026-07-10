import { API_BASE, MAX_PROGRESS_RETRIES, TOKEN_STORAGE_KEY } from './env'

export type ProgressStatus = 'DETECTING' | 'DONE' | 'ERROR'

export interface ProgressEventData {
  status?: ProgressStatus
  stage?: string
  percent?: number
  message?: string
  issueCount?: number
}

export interface ProgressStream {
  close: () => void
}

export interface ProgressHandlers {
  onProgress: (data: ProgressEventData) => void
  onDone?: (data: ProgressEventData) => void
  onError?: (message: string) => void
  onFallback?: () => void
}

const retryDelay = (attempt: number) => Math.min(4000, 1000 * 2 ** attempt)

function progressUrl(taskId: string): string {
  const url = new URL(`/v1/detect/progress/${encodeURIComponent(taskId)}`, API_BASE)
  const token = localStorage.getItem(TOKEN_STORAGE_KEY)
  if (token) url.searchParams.set('token', token)
  return url.toString()
}

export function subscribeProgress(taskId: string, handlers: ProgressHandlers): ProgressStream {
  let closed = false
  let retry = 0
  let source: EventSource | null = null
  let retryTimer: ReturnType<typeof setTimeout> | null = null

  const cleanup = () => {
    source?.close()
    source = null
    if (retryTimer) clearTimeout(retryTimer)
    retryTimer = null
  }

  const open = () => {
    if (closed) return
    cleanup()
    source = new EventSource(progressUrl(taskId))

    const handle = (event: MessageEvent) => {
      retry = 0
      let data: ProgressEventData = {}
      try {
        data = JSON.parse(event.data) as ProgressEventData
      } catch {
        data = { message: event.data }
      }
      handlers.onProgress(data)
      if (data.status === 'DONE' || data.stage === 'DONE') {
        handlers.onDone?.(data)
        cleanup()
      }
      if (data.status === 'ERROR' || data.stage === 'ERROR') {
        handlers.onError?.(data.message || '检测失败')
        cleanup()
      }
    }

    source.addEventListener('progress', handle)
    source.addEventListener('done', handle)
    source.addEventListener('error', () => {
      source?.close()
      if (closed) return
      if (retry >= MAX_PROGRESS_RETRIES) {
        handlers.onFallback?.()
        cleanup()
        return
      }
      handlers.onError?.(`实时进度连接中断，正在第 ${retry + 1} 次重连`)
      retryTimer = setTimeout(open, retryDelay(retry))
      retry += 1
    })
  }

  open()

  return {
    close() {
      closed = true
      cleanup()
    },
  }
}

