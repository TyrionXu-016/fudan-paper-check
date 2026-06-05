import { http } from './checkApi'

export interface AuthUser {
  id: string
  email: string
  name: string
  role?: string
}

export interface TokenResp {
  access_token: string
  token_type?: string
  user: AuthUser
}

export function login(email: string, password: string): Promise<TokenResp> {
  return http.post('/v1/auth/login', { email, password })
}

export function register(email: string, password: string, name: string): Promise<TokenResp> {
  return http.post('/v1/auth/register', { email, password, name })
}

export function me(): Promise<AuthUser> {
  return http.get('/v1/auth/me')
}
