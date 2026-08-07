/**
 * http.ts — Client HTTP unique vers l'API backend.
 *
 * DEUX MODES, selon la variable de build `VITE_API_BASE` :
 *
 *  - SAME-ORIGIN (dév, `VITE_API_BASE` vide) : appels `/api/*` via le proxy Vite
 *    `/api → :5001`. Auth par cookies HttpOnly + CSRF double-submit (en-tête
 *    X-CSRF-Token = cookie non-HttpOnly `bmci_csrf`). Comportement historique.
 *
 *  - CROSS-ORIGIN (build déployé, ex. front Vercel → backend FastAPI en localhost
 *    chez l'utilisateur : `VITE_API_BASE=http://localhost:5001`). Les cookies
 *    cross-site ne s'appliquent pas → auth par en-tête `Authorization: Bearer`
 *    (jeton mémorisé au login, persisté en localStorage). Le CSRF ne s'applique pas
 *    (le jeton Bearer n'est jamais envoyé automatiquement par le navigateur).
 *
 * - Erreurs : lève `ApiError` (status + message issu de `detail` FastAPI).
 */

// Origine du backend (sans slash final). Vide en dév → chemins relatifs (proxy Vite).
const ORIGIN = (import.meta.env.VITE_API_BASE ?? '').replace(/\/$/, '')
/** Base des appels API : '/api' en dév (proxy) ou 'http://host:port/api' déployé. */
export const API_BASE = `${ORIGIN}/api`
/** Vrai si front et backend sont sur des origines différentes (auth Bearer). */
export const IS_CROSS_ORIGIN = ORIGIN !== ''

const CSRF_COOKIE = 'bmci_csrf'
const TOKEN_KEY = 'bmci_token'
const SAFE = new Set(['GET', 'HEAD', 'OPTIONS'])
// Endpoints d'auth : un 401 y est normal (probe /me non connecté, logout expiré)
// et ne doit PAS déclencher la redirection globale (sinon boucle).
const AUTH_PATH = /^\/auth\//

let csrfToken: string | null = null
// Jeton de session pour l'auth Bearer (cross-origin uniquement). Persisté en
// localStorage pour survivre au rechargement — il n'y a pas de cookie cross-site
// à rejouer. En same-origin, il reste null (on s'appuie sur le cookie HttpOnly).
let bearer: string | null = IS_CROSS_ORIGIN ? localStorage.getItem(TOKEN_KEY) : null

/** Mémorise le token CSRF renvoyé par /auth/login (et re-lu du cookie au reload). */
export function setCsrf(token: string | null): void {
  csrfToken = token
}

/** Mémorise (ou efface) le jeton de session Bearer — cross-origin uniquement. */
export function setToken(token: string | null): void {
  bearer = IS_CROSS_ORIGIN ? token : null
  if (!IS_CROSS_ORIGIN) return
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

/** Jeton de session Bearer courant (null en same-origin). */
export function getToken(): string | null {
  return bearer
}

// Intercepteur 401 : session expirée en cours d'usage → l'app décide (déconnexion
// + retour connexion). Enregistré par main.ts pour éviter un import circulaire.
let onUnauthorized: ((path: string) => void) | null = null
export function setUnauthorizedHandler(cb: ((path: string) => void) | null): void {
  onUnauthorized = cb
}

function readCsrfCookie(): string | null {
  const m = document.cookie.match(new RegExp('(?:^|;\\s*)' + CSRF_COOKIE + '=([^;]+)'))
  return m ? decodeURIComponent(m[1]) : null
}

/** Token CSRF courant (mémoire au login, sinon relu du cookie). Pour les appels
 *  qui ne passent pas par `apiFetch` (ex. flux SSE lu via `fetch` + reader). */
export function getCsrf(): string | null {
  return csrfToken ?? readCsrfCookie()
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

// Mode d'envoi des cookies : inclus en same-origin (auth par cookie), omis en
// cross-origin (auth par Bearer, aucun cookie à transmettre).
const CREDENTIALS: RequestCredentials = IS_CROSS_ORIGIN ? 'omit' : 'include'

/** Ajoute l'auth (Bearer si cross-origin) et le CSRF (si same-origin, méthode mutante). */
function authHeaders(method: string, base: Record<string, string>): Record<string, string> {
  const headers = { ...base }
  if (bearer) headers['Authorization'] = `Bearer ${bearer}`
  if (!IS_CROSS_ORIGIN && !SAFE.has(method)) {
    const csrf = getCsrf()
    if (csrf) headers['X-CSRF-Token'] = csrf
  }
  return headers
}

export async function apiFetch<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const method = (opts.method ?? 'GET').toUpperCase()
  let headers: Record<string, string> = { Accept: 'application/json', ...(opts.headers ?? {}) }

  if (!SAFE.has(method)) headers['Content-Type'] = 'application/json'
  headers = authHeaders(method, headers)

  const res = await fetch(API_BASE + path, {
    method,
    credentials: CREDENTIALS,
    headers,
    body: opts.body !== undefined ? JSON.stringify(opts.body) : undefined,
  })

  if (res.status === 204) return undefined as T
  const text = await res.text()
  const data: unknown = text ? JSON.parse(text) : undefined

  if (!res.ok) {
    // Session expirée en cours d'usage (hors endpoints d'auth) → notifie l'app.
    if (res.status === 401 && !AUTH_PATH.test(path)) onUnauthorized?.(path)
    const detail =
      data && typeof data === 'object' && 'detail' in data ? (data as { detail: unknown }).detail : data
    const message = typeof detail === 'string' ? detail : `Erreur ${res.status}`
    throw new ApiError(res.status, message, data)
  }
  return data as T
}

/** Upload multipart (FormData). Ne fixe PAS Content-Type (le navigateur pose la
 *  boundary). Auth (Bearer/CSRF) + credentials comme `apiFetch`. */
export async function apiUpload<T>(path: string, form: FormData): Promise<T> {
  const headers = authHeaders('POST', { Accept: 'application/json' })
  const res = await fetch(API_BASE + path, { method: 'POST', credentials: CREDENTIALS, headers, body: form })
  if (res.status === 204) return undefined as T
  const text = await res.text()
  const data: unknown = text ? JSON.parse(text) : undefined
  if (!res.ok) {
    if (res.status === 401 && !AUTH_PATH.test(path)) onUnauthorized?.(path)
    const detail =
      data && typeof data === 'object' && 'detail' in data ? (data as { detail: unknown }).detail : data
    throw new ApiError(res.status, typeof detail === 'string' ? detail : `Erreur ${res.status}`, data)
  }
  return data as T
}

/** GET authentifié renvoyant un Blob (ex. PDF de CV). En cross-origin l'auth passe
 *  par Bearer et une `<iframe>`/`<a>` ne peut pas porter d'en-tête : on télécharge
 *  donc les octets ici, puis l'appelant crée un object URL (même-origine, sans
 *  contrainte de framing). Fonctionne aussi en same-origin (auth par cookie). */
export async function apiBlob(path: string): Promise<Blob> {
  const headers = authHeaders('GET', {})
  const res = await fetch(API_BASE + path, { credentials: CREDENTIALS, headers })
  if (!res.ok) {
    if (res.status === 401 && !AUTH_PATH.test(path)) onUnauthorized?.(path)
    let message = `Erreur ${res.status}`
    try {
      const data = await res.json()
      if (data && typeof data.detail === 'string') message = data.detail
    } catch {
      /* réponse non-JSON : on garde le message générique */
    }
    throw new ApiError(res.status, message)
  }
  return res.blob()
}
