import fs from 'node:fs'
import path from 'node:path'
import zlib from 'node:zlib'

const dist = path.resolve('dist/assets')
const JS_GZIP_LIMIT = 180 * 1024
const CSS_GZIP_LIMIT = 60 * 1024

if (!fs.existsSync(dist)) {
  console.error('dist/assets not found. Run npm run build first.')
  process.exit(1)
}

let failed = false
for (const name of fs.readdirSync(dist)) {
  const file = path.join(dist, name)
  if (!/\.(js|css)$/.test(name)) continue
  const gzipSize = zlib.gzipSync(fs.readFileSync(file)).length
  const limit = name.endsWith('.js') ? JS_GZIP_LIMIT : CSS_GZIP_LIMIT
  const ok = gzipSize <= limit
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}: ${(gzipSize / 1024).toFixed(1)} KiB gzip`)
  if (!ok) failed = true
}

if (failed) process.exit(1)
