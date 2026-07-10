import type { Paragraph } from '../types'
import { isSpanNode } from '../types'
import { useVersionStore } from '../stores/version'
import { useEditorStore } from '../stores/editor'
import { useDocStore } from '../stores/doc'

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function escapeXml(s: string): string {
  return escapeHtml(s).replace(/"/g, '&quot;').replace(/'/g, '&apos;')
}

function stripHtml(s: string): string {
  const el = document.createElement('div')
  el.innerHTML = s
  return el.textContent || ''
}

function resolveParagraph(p: Paragraph, current: (spanId: string) => string | undefined): string {
  return p
    .map((node) =>
      isSpanNode(node) ? current(node.spanId) ?? escapeHtml(node.original) : escapeHtml(node),
    )
    .join('')
}

interface ExportBlock {
  kind: 'title' | 'author' | 'heading' | 'paragraph' | 'label'
  text: string
}

function collectBlocks(): ExportBlock[] {
  const editor = useEditorStore()
  const paper = useDocStore().currentPaper
  if (editor.dirty) {
    const text = stripHtml(editor.docHtml)
    return [
      { kind: 'title', text: paper.title },
      ...(paper.author ? [{ kind: 'author' as const, text: paper.author }] : []),
      ...text
        .split(/\n{2,}|\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((text) => ({ kind: 'paragraph' as const, text })),
    ]
  }

  const version = useVersionStore()
  const current = (spanId: string) => version.current(spanId)
  const blocks: ExportBlock[] = [{ kind: 'title', text: paper.title }]
  if (paper.author) blocks.push({ kind: 'author', text: paper.author })
  if (paper.abstract.length) {
    blocks.push({ kind: 'label', text: '摘  要' })
    for (const p of paper.abstract) blocks.push({ kind: 'paragraph', text: stripHtml(resolveParagraph(p, current)) })
  }
  for (const sec of paper.sections) {
    blocks.push({ kind: 'heading', text: sec.heading })
    for (const p of sec.paragraphs) blocks.push({ kind: 'paragraph', text: stripHtml(resolveParagraph(p, current)) })
  }
  return blocks
}

function toArrayBuffer(bytes: Uint8Array): ArrayBuffer {
  const buffer = new ArrayBuffer(bytes.byteLength)
  new Uint8Array(buffer).set(bytes)
  return buffer
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

const crcTable = (() => {
  const table = new Uint32Array(256)
  for (let i = 0; i < 256; i += 1) {
    let c = i
    for (let k = 0; k < 8; k += 1) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    table[i] = c >>> 0
  }
  return table
})()

function crc32(bytes: Uint8Array): number {
  let c = 0xffffffff
  for (const b of bytes) c = crcTable[(c ^ b) & 0xff] ^ (c >>> 8)
  return (c ^ 0xffffffff) >>> 0
}

function u16(v: number): number[] {
  return [v & 0xff, (v >>> 8) & 0xff]
}

function u32(v: number): number[] {
  return [v & 0xff, (v >>> 8) & 0xff, (v >>> 16) & 0xff, (v >>> 24) & 0xff]
}

function concat(parts: Uint8Array[]): Uint8Array {
  const total = parts.reduce((sum, p) => sum + p.length, 0)
  const out = new Uint8Array(total)
  let offset = 0
  for (const part of parts) {
    out.set(part, offset)
    offset += part.length
  }
  return out
}

function makeZip(files: Array<{ path: string; content: string }>): Uint8Array {
  const enc = new TextEncoder()
  const locals: Uint8Array[] = []
  const centrals: Uint8Array[] = []
  let offset = 0

  for (const file of files) {
    const name = enc.encode(file.path)
    const data = enc.encode(file.content)
    const crc = crc32(data)
    const local = new Uint8Array([
      ...u32(0x04034b50), ...u16(20), ...u16(0x0800), ...u16(0), ...u16(0), ...u16(0),
      ...u32(crc), ...u32(data.length), ...u32(data.length), ...u16(name.length), ...u16(0),
      ...name, ...data,
    ])
    locals.push(local)

    centrals.push(new Uint8Array([
      ...u32(0x02014b50), ...u16(20), ...u16(20), ...u16(0x0800), ...u16(0), ...u16(0), ...u16(0),
      ...u32(crc), ...u32(data.length), ...u32(data.length), ...u16(name.length), ...u16(0), ...u16(0),
      ...u16(0), ...u16(0), ...u32(0), ...u32(offset), ...name,
    ]))
    offset += local.length
  }

  const central = concat(centrals)
  const end = new Uint8Array([
    ...u32(0x06054b50), ...u16(0), ...u16(0), ...u16(files.length), ...u16(files.length),
    ...u32(central.length), ...u32(offset), ...u16(0),
  ])
  return concat([...locals, central, end])
}

function docxParagraph(block: ExportBlock): string {
  const style = block.kind === 'title' ? 'Title' : block.kind === 'heading' ? 'Heading1' : 'Normal'
  const jc = block.kind === 'title' || block.kind === 'author' || block.kind === 'label' ? 'center' : 'both'
  const text = escapeXml(block.text)
  return `<w:p><w:pPr><w:pStyle w:val="${style}"/><w:jc w:val="${jc}"/></w:pPr><w:r><w:t xml:space="preserve">${text}</w:t></w:r></w:p>`
}

function buildDocx(): Uint8Array {
  const blocks = collectBlocks()
  const documentXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>${blocks.map(docxParagraph).join('')}
    <w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1800" w:bottom="1440" w:left="1800"/></w:sectPr>
  </w:body>
</w:document>`
  const stylesXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:eastAsia="宋体"/><w:sz w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:rPr><w:rFonts w:eastAsia="黑体"/><w:b/><w:sz w:val="32"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:rPr><w:rFonts w:eastAsia="黑体"/><w:b/><w:sz w:val="28"/></w:rPr></w:style>
</w:styles>`
  return makeZip([
    { path: '[Content_Types].xml', content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>` },
    { path: '_rels/.rels', content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>` },
    { path: 'word/_rels/document.xml.rels', content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>` },
    { path: 'word/document.xml', content: documentXml },
    { path: 'word/styles.xml', content: stylesXml },
  ])
}

function wrapCanvasText(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const lines: string[] = []
  let line = ''
  for (const ch of text) {
    const next = line + ch
    if (ctx.measureText(next).width > maxWidth && line) {
      lines.push(line)
      line = ch
    } else {
      line = next
    }
  }
  if (line) lines.push(line)
  return lines
}

async function renderPdfPages(): Promise<Uint8Array[]> {
  const blocks = collectBlocks()
  const pages: Uint8Array[] = []
  const canvas = document.createElement('canvas')
  canvas.width = 1240
  canvas.height = 1754
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('当前浏览器不支持 PDF 画布导出')
  const context = ctx

  const marginX = 130
  const maxWidth = canvas.width - marginX * 2
  let y = 140

  function newPage() {
    context.fillStyle = '#fff'
    context.fillRect(0, 0, canvas.width, canvas.height)
    context.fillStyle = '#111827'
    y = 140
  }
  async function flushPage() {
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92)
    const bin = atob(dataUrl.split(',')[1])
    const bytes = new Uint8Array(bin.length)
    for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i)
    pages.push(bytes)
  }

  newPage()
  for (const block of blocks) {
    const isTitle = block.kind === 'title'
    const isHeading = block.kind === 'heading'
    const isCentered = isTitle || block.kind === 'author' || block.kind === 'label'
    const fontSize = isTitle ? 34 : isHeading ? 25 : block.kind === 'author' ? 20 : 22
    const lineHeight = Math.round(fontSize * 1.75)
    context.font = `${isTitle || isHeading ? '700 ' : ''}${fontSize}px "Microsoft YaHei", SimSun, sans-serif`
    const lines = wrapCanvasText(context, block.text, maxWidth)
    const needed = lines.length * lineHeight + (isTitle || isHeading ? 20 : 8)
    if (y + needed > canvas.height - 130) {
      await flushPage()
      newPage()
    }
    for (const line of lines) {
      const x = isCentered ? (canvas.width - context.measureText(line).width) / 2 : marginX
      context.fillText(line, x, y)
      y += lineHeight
    }
    y += isTitle || isHeading ? 20 : 8
  }
  await flushPage()
  return pages
}

function ascii(s: string): Uint8Array {
  return new TextEncoder().encode(s)
}

function buildPdf(images: Uint8Array[]): Uint8Array {
  const parts: Uint8Array[] = []
  const offsets: number[] = [0]
  let offset = 0
  const add = (part: Uint8Array) => { parts.push(part); offset += part.length }
  const obj = (id: number, body: Uint8Array | string) => {
    offsets[id] = offset
    add(ascii(`${id} 0 obj\n`))
    add(typeof body === 'string' ? ascii(body) : body)
    add(ascii('\nendobj\n'))
  }

  add(ascii('%PDF-1.4\n'))
  const pageIds = images.map((_, i) => 3 + i * 3)
  obj(1, '<< /Type /Catalog /Pages 2 0 R >>')
  obj(2, `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(' ')}] /Count ${pageIds.length} >>`)

  images.forEach((img, i) => {
    const pageId = 3 + i * 3
    const imageId = pageId + 1
    const contentId = pageId + 2
    obj(pageId, `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /XObject << /Im${i} ${imageId} 0 R >> >> /Contents ${contentId} 0 R >>`)
    obj(imageId, concat([ascii(`<< /Type /XObject /Subtype /Image /Width 1240 /Height 1754 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${img.length} >>\nstream\n`), img, ascii('\nendstream')]))
    const stream = `q\n595 0 0 842 0 0 cm\n/Im${i} Do\nQ\n`
    obj(contentId, `<< /Length ${stream.length} >>\nstream\n${stream}endstream`)
  })

  const xrefOffset = offset
  const count = 2 + images.length * 3
  add(ascii(`xref\n0 ${count + 1}\n0000000000 65535 f \n`))
  for (let i = 1; i <= count; i += 1) add(ascii(`${String(offsets[i]).padStart(10, '0')} 00000 n \n`))
  add(ascii(`trailer\n<< /Size ${count + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`))
  return concat(parts)
}

export function exportWord() {
  const title = useDocStore().currentPaper.title || '论文'
  const docxBytes = buildDocx()
  const blob = new Blob([toArrayBuffer(docxBytes)], {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  })
  triggerDownload(blob, `${title}.docx`)
}

export async function exportPdf() {
  const title = useDocStore().currentPaper.title || '论文'
  const pages = await renderPdfPages()
  const pdfBytes = buildPdf(pages)
  const blob = new Blob([toArrayBuffer(pdfBytes)], { type: 'application/pdf' })
  triggerDownload(blob, `${title}.pdf`)
}

