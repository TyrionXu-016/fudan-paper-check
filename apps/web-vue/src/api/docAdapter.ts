import type { Paper, Paragraph, ParaNode, Section } from '../types'
import type { BackendCheckReport, BackendIssue } from './adapter'

// 后端 DocumentView（mse-tyrion: packages/schema/models.py）
export interface BackendSection {
  id: string
  kind: string
  title: string
  level: number
  start_line: number
  end_line: number
  parent_id?: string | null
}

export interface BackendSpan {
  id: string
  section_id: string
  block_id: string
  start_offset: number
  end_offset: number
  text: string
  line_start?: number | null
  line_end?: number | null
  page?: number | null
}

export interface BackendDocumentView {
  sections: BackendSection[]
  spans: BackendSpan[]
  paper_title?: string
}

// 把扁平的 sections + spans + issues 重建为前端 Paper（嵌套段落、内联 SpanNode）
export function adaptDocument(
  doc: BackendDocumentView,
  report: BackendCheckReport | undefined,
): Paper {
  // 1) issue 按 span_id 索引
  const issueBySpan = new Map<string, BackendIssue>()
  for (const i of report?.issues ?? []) {
    if (i.span_id) issueBySpan.set(i.span_id, i)
  }

  // 2) spans 按 section_id 分组、按 start_offset 排序
  const spansBySection: Record<string, BackendSpan[]> = {}
  for (const s of doc.spans ?? []) {
    ;(spansBySection[s.section_id] = spansBySection[s.section_id] || []).push(s)
  }
  for (const arr of Object.values(spansBySection)) {
    arr.sort((a, b) => (a.start_offset ?? 0) - (b.start_offset ?? 0))
  }

  // 3) 单 section 的 spans → Paragraph[]，同 block_id 拼成一段
  function buildParagraphs(sectionId: string): Paragraph[] {
    const spans = spansBySection[sectionId] || []
    if (!spans.length) return []
    const out: Paragraph[] = []
    let blkId = ''
    let cur: Paragraph = []
    for (const s of spans) {
      if (s.block_id !== blkId) {
        if (cur.length) out.push(cur)
        cur = []
        blkId = s.block_id
      }
      const issue = issueBySpan.get(s.id)
      if (issue) {
        cur.push({
          spanId: s.id,
          original: s.text,
          suggested: issue.suggested_text || s.text,
          issueId: issue.id || s.id,
        })
      } else {
        // 合并相邻纯文本，避免大量 string 节点
        const last = cur[cur.length - 1]
        if (typeof last === 'string') cur[cur.length - 1] = last + s.text
        else cur.push(s.text)
      }
    }
    if (cur.length) out.push(cur)
    return out
  }

  // 4) sections 按 start_line 排序
  const sorted = [...(doc.sections ?? [])].sort(
    (a, b) => (a.start_line ?? 0) - (b.start_line ?? 0),
  )

  // 5) 摘要 / 作者 / 正文章节拆分
  let abstract: Paragraph[] = []
  let author = ''
  const sections: Section[] = []

  for (let idx = 0; idx < sorted.length; idx++) {
    const sec = sorted[idx]
    const paragraphs = buildParagraphs(sec.id)
    const kind = (sec.kind || '').toLowerCase()
    const titleLower = sec.title?.toLowerCase() || ''

    // 第一个 level=1 的 section 通常是标题区：title 就是论文名，spans 是作者/署名行
    if (idx === 0 && sec.level === 1) {
      author = paragraphs
        .map((p) => p.map((n: ParaNode) => (typeof n === 'string' ? n : n.original)).join(''))
        .join(' · ')
      continue
    }
    // 摘要识别：kind=abstract 或 title 含"摘"或英文 abstract
    if (kind === 'abstract' || sec.title?.includes('摘') || titleLower.includes('abstract')) {
      abstract = paragraphs
      continue
    }
    sections.push({ heading: sec.title || sec.id, paragraphs })
  }

  return {
    title: doc.paper_title || sorted[0]?.title || '论文',
    author,
    abstract,
    sections,
  }
}
