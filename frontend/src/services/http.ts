/**
 * http.ts — Client HTTP unique vers l'API backend (:5001 via le proxy Vite /api).
 *
 * - Same-origin (le proxy Vite forwarde /api → :5001) : cookies HttpOnly gérés
 *   par le navigateur. `credentials: 'include'` par sécurité.
 * - CSRF double-submit : sur les méthodes mutantes, on envoie l'en-tête
 *   X-CSRF-Token (valeur = cookie non-HttpOnly `bmci_csrf`, posé au login).
 * - Erreurs : lève `ApiError` (status + message issu de `detail` FastAPI).
 */

const BASE = '/api'
const CSRF_COOKIE = 'bmci_csrf'
const SAFE = new Set(['GET', 'HEAD', 'OPTIONS'])

let csrfToken: string | null = null

/** Mémorise le token CSRF renvoyé par /auth/login (et re-lu du cookie au reload). */
export function setCsrf(token: string | null): void {
  csrfToken = token
}

function readCsrfCookie(): string | null {
  const m = document.cookie.match(new RegExp('(?:^|;\\s*)' + CSRF_COOKIE + '=([^;]+)'))
  return m ? decodeURIComponent(m[1]) : null
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface RequestOptions {
  method?: string
  body?: unknown
  headers?: Record<string, string>
}

export async function apiFetch<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const method = (opts.method ?? 'GET').toUpperCase()
  const headers: Record<string, string> = { Accept: 'application/json', ...(opts.headers ?? {}) }

  if (!SAFE.has(method)) {
    headers['Content-Type'] = 'application/json'
    const csrf = csrfToken ?? readCsrfCookie()
    if (csrf) headers['X-CSRF-Token'] = csrf
  }

  const res = await fetch(BASE + path, {
    method,
    credentials: 'include',
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  })

  if (res.status === 204) return undefined as T
  const text = await res.text()
  const data: unknown = text ? JSON.parse(text) : undefined

  if (!res.ok) {
    const detail =
      data && typeof data === 'object' && 'detail' in data ? (data as { detail: unknown }).detail : data
    const message = typeof detail === 'string' ? detail : `Erreur ${res.status}`
    throw new ApiError(res.status, message, data)
  }
  return data as T
}
