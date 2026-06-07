import type { Issue, IssueTypeKey, Severity } from '../types'

// 后端 Issue 形状（mse-tyrion: packages/schema/models.py）
export interface BackendIssue {
  id?: string
  issue_type?: string | null
  original_text?: string
  suggested_text?: string
  span_id?: string | null
  code?: string
  category?: string
  severity?: string
  section?: string | null
  line?: number | null
  page?: number | null
  page_line?: string | null
}

export interface BackendCheckReport {
  job_id?: string
  paper_title?: string
  summary?: { errors: number; warnings: number; infos: number }
  issues?: BackendIssue[]
}

// 后端 IssueType → 前端 IssueTypeKey
const TYPE_MAP: Record<string, IssueTypeKey> = {
  format: 'FORMAT',
  typo: 'TYPO',
  grammar: 'GRAMMAR',
  polish: 'POLISH',
  logic_contradiction: 'LOGIC',
  paragraph_logic: 'PARA_LOGIC',
  sentence_split: 'SPLIT',
  reference: 'FORMAT',
  llm: 'POLISH',
}

const CATEGORY_FALLBACK: Record<string, IssueTypeKey> = {
  structure: 'FORMAT',
  format: 'FORMAT',
  consistency: 'GRAMMAR',
  reference: 'FORMAT',
}

const SEVERITY_MAP: Record<string, Severity> = {
  error: 'high',
  warning: 'med',
  info: 'low',
}

const truncate = (s: string, n = 20): string => (s && s.length > n ? `${s.slice(0, n)}…` : s || '')

function buildLocation(i: BackendIssue): string {
  const parts: string[] = []
  if (i.section) parts.push(i.section)
  if (i.page_line) parts.push(i.page_line)
  else if (i.line != null) parts.push(`第 ${i.line} 行`)
  else if (i.page != null) parts.push(`第 ${i.page} 页`)
  return parts.length ? parts.join(' · ') : '全文'
}

function buildSummary(i: BackendIssue): string {
  if (i.original_text && i.suggested_text) {
    return `「${truncate(i.original_text)}」→「${truncate(i.suggested_text)}」`
  }
  if (i.original_text) return truncate(i.original_text, 40)
  if (i.suggested_text) return `建议：${truncate(i.suggested_text, 40)}`
  return i.code || '问题项'
}

export function adaptIssue(i: BackendIssue, idx: number): Issue {
  const typeKey =
    (i.issue_type && TYPE_MAP[i.issue_type.toLowerCase()]) ||
    (i.category && CATEGORY_FALLBACK[i.category.toLowerCase()]) ||
    'FORMAT'

  return {
    id: i.id || `be-${idx}`,
    type: typeKey,
    severity: SEVERITY_MAP[(i.severity || 'info').toLowerCase()] || 'low',
    location: buildLocation(i),
    summary: buildSummary(i),
    before: i.original_text || '',
    after: i.suggested_text || '',
    explain: i.code ? `规则：${i.code}` : '后端检测项',
    spanId: i.span_id ?? null,
    docLevel: !i.span_id,
  }
}

export function adaptReport(report: BackendCheckReport): Issue[] {
  return (report.issues || []).map(adaptIssue)
}
