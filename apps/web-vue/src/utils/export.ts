import type { Paragraph } from '../types'
import { isSpanNode } from '../types'
import { PAPER } from '../data/paper'
import { useVersionStore } from '../stores/version'
import { useEditorStore } from '../stores/editor'

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

// 把一个段落（字符串 + span 节点混合）解析为应用了所有决策后的终稿 HTML。
// 纯文本片段转义；span 内容（可能含手动编辑的 <b>/<i>/<u> 格式）按原样注入。
function resolveParagraph(p: Paragraph, current: (spanId: string) => string | undefined): string {
  return p
    .map((node) =>
      isSpanNode(node) ? current(node.spanId) ?? escapeHtml(node.original) : escapeHtml(node),
    )
    .join('')
}

// 文档编辑器有改动时，导出其内容 + 页面设置（行距/页边距/页眉页脚/字体）
function buildFromEditor(forPrint: boolean): string {
  const editor = useEditorStore()
  const s = editor.settings
  const style = `
    body { font-family: ${s.fontFamily}; font-size: ${s.fontSize}px; line-height: ${s.lineHeight};
           color: #1a1a1a; max-width: 760px; margin: 0 auto; padding: ${forPrint ? '0' : '48px'}; }
    h1 { font-size: 22px; text-align: center; margin: 0 0 6px; }
    h2 { font-size: 16px; margin: 22px 0 10px; }
    .author { text-align: center; color: #555; font-size: 13px; margin: 0 0 24px; }
    .label { text-align: center; letter-spacing: 4px; margin: 18px 0 8px; }
    p { margin: 0 0 12px; }
    .doc-header { text-align: center; color: #888; font-size: 12px; border-bottom: 1px solid #ddd; padding-bottom: 6px; margin-bottom: 16px; }
    .doc-footer { text-align: center; color: #888; font-size: 12px; border-top: 1px solid #ddd; padding-top: 6px; margin-top: 16px; }
    @page { margin: ${s.marginV}cm ${s.marginH}cm; }
  `
  const header = s.headerText ? `<div class="doc-header">${escapeHtml(s.headerText)}</div>` : ''
  const footer = s.footerText ? `<div class="doc-footer">${escapeHtml(s.footerText)}</div>` : ''
  return `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8" />
<title>${escapeHtml(PAPER.title)}</title><style>${style}</style></head>
<body>${header}${editor.docHtml}${footer}</body></html>`
}

// 组装终稿 HTML（Word 与 PDF 共用）
function buildDocumentHtml(forPrint: boolean): string {
  if (useEditorStore().dirty) return buildFromEditor(forPrint)

  const version = useVersionStore()
  const current = (spanId: string) => version.current(spanId)

  const paras: string[] = []
  paras.push(`<h1>${escapeHtml(PAPER.title)}</h1>`)
  paras.push(`<p class="author">${escapeHtml(PAPER.author)}</p>`)
  paras.push(`<p class="label">摘　要</p>`)
  for (const p of PAPER.abstract) {
    paras.push(`<p class="body">${escapeHtml(resolveParagraph(p, current))}</p>`)
  }
  for (const sec of PAPER.sections) {
    paras.push(`<h2>${escapeHtml(sec.heading)}</h2>`)
    for (const p of sec.paragraphs) {
      paras.push(`<p class="body">${escapeHtml(resolveParagraph(p, current))}</p>`)
    }
  }

  const style = `
    body { font-family: "SimSun", "宋体", serif; color: #1a1a1a; line-height: 1.8;
           max-width: 760px; margin: 0 auto; padding: ${forPrint ? '0' : '48px'}; }
    h1 { font-family: "SimHei", "黑体", sans-serif; font-size: 22px; text-align: center; margin: 0 0 6px; }
    h2 { font-family: "SimHei", "黑体", sans-serif; font-size: 16px; margin: 22px 0 10px; }
    .author { text-align: center; color: #555; font-size: 13px; margin: 0 0 24px; }
    .label { font-family: "SimHei", "黑体", sans-serif; text-align: center; letter-spacing: 4px; margin: 18px 0 8px; }
    .body { font-size: 15px; text-indent: 2em; margin: 0 0 12px; }
    @page { margin: 2.54cm 3.17cm; }
  `

  return `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8" />
<title>${escapeHtml(PAPER.title)}</title><style>${style}</style></head>
<body>${paras.join('\n')}</body></html>`
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

// 导出 Word：生成 .doc（HTML 内核，Word/WPS 可直接打开，中文无乱码）
export function exportWord() {
  const html = buildDocumentHtml(false)
  const blob = new Blob(['﻿', html], { type: 'application/msword;charset=utf-8' })
  triggerDownload(blob, `${PAPER.title}.doc`)
}

// 导出 PDF：打开格式化打印窗口，由浏览器“打印 / 另存为 PDF”输出（中文矢量、可选中）
export function exportPdf() {
  const html = buildDocumentHtml(true)
  const win = window.open('', '_blank', 'width=900,height=1000')
  if (!win) {
    // 弹窗被拦截时降级为 Blob 下载 HTML
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    triggerDownload(blob, `${PAPER.title}.html`)
    return
  }
  win.document.open()
  win.document.write(html)
  win.document.close()
  win.focus()
  setTimeout(() => win.print(), 300)
}
