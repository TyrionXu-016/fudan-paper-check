export type IssueTypeKey =
  | 'FORMAT'
  | 'TYPO'
  | 'GRAMMAR'
  | 'POLISH'
  | 'SPLIT'
  | 'PARA_LOGIC'
  | 'LOGIC'

export type Severity = 'high' | 'med' | 'low'

export type DecisionAction = 'accept' | 'reject' | 'custom'

export interface Issue {
  id: string
  type: IssueTypeKey
  severity: Severity
  location: string
  summary: string
  before: string
  after: string
  explain: string
  spanId: string | null
  docLevel?: boolean
}

// 预览区段落节点：纯字符串，或一个可交互的可编辑 span
export interface SpanNode {
  spanId: string
  original: string
  suggested: string
  issueId: string | null
}
export type ParaNode = string | SpanNode
export type Paragraph = ParaNode[]

export interface ParagraphLogic {
  issueId: string
  position: string
}
export interface Section {
  heading: string
  paragraphs: Paragraph[]
  paragraphLogic?: ParagraphLogic
}
export interface Paper {
  title: string
  author: string
  abstract: Paragraph[]
  sections: Section[]
}

export type RuleSummary = Record<string, string[]>
export interface Rule {
  id: string
  name: string
  short: string
  version: string
  summary?: RuleSummary
}

export interface TypeMeta {
  label: string
  color: string
  bg: string
  short: string
}

export interface Stage {
  id: string
  label: string
  pct: number
}

export interface Decision {
  action: DecisionAction
  customContent?: string
}

export type ModSource = 'original' | 'ai' | 'custom' | 'revert' | 'manual'
export interface ModRecord {
  content: string
  source: ModSource
  ts: string
  note: string
}

export function isSpanNode(n: ParaNode): n is SpanNode {
  return typeof n === 'object' && n !== null
}
