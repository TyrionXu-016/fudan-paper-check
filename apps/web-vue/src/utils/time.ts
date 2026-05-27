export function nowTs(): string {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  return `2025-06-01 ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}
