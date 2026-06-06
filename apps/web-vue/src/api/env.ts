// 运行时配置：开发态默认走本地 mock；接真实后端时设 VITE_USE_MOCK=false 与 VITE_API_BASE。
export const USE_MOCK =
  (import.meta.env.VITE_USE_MOCK ?? 'true').toString().toLowerCase() !== 'false'

export const API_BASE: string =
  import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

export const AUTH_REQUIRED = !USE_MOCK

export const TOKEN_STORAGE_KEY = 'fpc_token'
export const UNAUTHORIZED_EVENT = 'fpc:unauthorized'
