import type { Decision } from '../types'
import { http } from './checkApi'

export type BackendDecisionAction = Decision['action'] | 'pending'

export interface BackendDecisionPayload {
  issue_id: string
  action: BackendDecisionAction
  custom_content?: string | null
}

export function patchDecision(
  taskId: string,
  issueId: string,
  action: BackendDecisionAction,
  customContent?: string,
): Promise<BackendDecisionPayload> {
  return http.patch(`/v1/tasks/${encodeURIComponent(taskId)}/decisions/${encodeURIComponent(issueId)}`, {
    issue_id: issueId,
    action,
    custom_content: customContent ?? null,
  })
}
