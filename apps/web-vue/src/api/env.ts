// 运行时配置：开发态默认走本地 mock；接真实后端时设 VITE_USE_MOCK=false 与 VITE_API_BASE。
export const USE_MOCK =
  (import.meta.env.VITE_USE_MOCK ?? 'true').toString().toLowerCase() !== 'false'

export const API_BASE: string =
  import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export const AUTH_REQUIRED = !USE_MOCK

export const TOKEN_STORAGE_KEY = 'fpc_token'
export const UNAUTHORIZED_EVENT = 'fpc:unauthorized'
export const CHUNK_UPLOAD_THRESHOLD = Number(import.meta.env.VITE_CHUNK_UPLOAD_THRESHOLD ?? 10 * 1024 * 1024)
export const CHUNK_SIZE = Number(import.meta.env.VITE_CHUNK_SIZE ?? 2 * 1024 * 1024)
export const ENABLE_SSE_PROGRESS = (import.meta.env.VITE_ENABLE_SSE_PROGRESS ?? 'true').toString().toLowerCase() !== 'false'
export const MAX_PROGRESS_RETRIES = Number(import.meta.env.VITE_MAX_PROGRESS_RETRIES ?? 5)
