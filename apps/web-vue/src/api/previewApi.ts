import { http } from './checkApi'

export interface BackendPreviewSpan {
  span_id: string
  section_id: string
  text: string
  highlight?: string | null
}

export interface BackendPreviewView {
  task_id: string
  paper_title: string
  spans: BackendPreviewSpan[]
  unresolved_count: number
}

export function getBackendPreview(taskId: string): Promise<BackendPreviewView> {
  return http.get(`/v1/tasks/${encodeURIComponent(taskId)}/preview`)
}
