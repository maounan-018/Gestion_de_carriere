import type { Role, User } from '@/types/domain'
import { PERSONAS, DEMO_EMAILS } from '@/data/personas'
import { apiFetch, setCsrf, setToken } from './http'

/**
 * Service d'authentification — respecte la bascule `VITE_API_MODE` (comme apiService).
 * - LIVE (défaut) : `/api/auth/*`. Login e-mail/mot de passe → cookies HttpOnly +
 *   token CSRF. L'identité vient du backend ; les champs présentationnels (titre,
 *   entité, libellé, photo) sont fournis par le persona correspondant.
 * - MOCK : résout le persona de démo à partir de l'e-mail, **sans backend** (démo
 *   offline). Sans cette branche, se connecter exigeait le backend même en mock.
 */

const MODE: 'mock' | 'live' = import.meta.env.VITE_API_MODE === 'mock' ? 'mock' : 'live'
// Miroir de la clé de stores/session.ts — utilisé uniquement pour rejouer la
// session en mode mock (pas de cookie de session à revalider).
const SESSION_KEY = 'bmci.session'

interface BackendUser {
  id: number
  email: string
  name: string
  role: string // COLLAB | MANAGER | RH | ADMIN
  type?: string
  manager_id?: number | null
  departement_key?: string | null
}

interface LoginResponse {
  utilisateur: BackendUser
  csrf_token: string
  // Jeton de session pour l'auth Bearer cross-origin (ignoré en same-origin).
  token: string
}

function mapRole(role: string): Role {
  const r = role.toUpperCase()
  if (r === 'MANAGER') return 'manager'
  if (r === 'RH' || r === 'ADMIN') return 'rh'
  return 'collab'
}

function mapUser(u: BackendUser): User {
  const role = mapRole(u.role)
  const base = PERSONAS[role]
  const name = (u.name || base.name).trim()
  const parts = name.split(/\s+/)
  const initials = ((parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '')).toUpperCase() || base.initials
  return {
    ...base, // titre, entité, roleLabel, photo (présentation)
    id: String(u.id),
    role,
    name,
    email: u.email || base.email,
    firstName: parts[0] || base.firstName,
    initials,
  }
}

/** Résout le persona de démo à partir de l'e-mail (mode mock, sans backend). */
function personaByEmail(email: string): User | null {
  const e = email.trim().toLowerCase()
  const role = (Object.keys(DEMO_EMAILS) as Role[]).find(
    (r) => DEMO_EMAILS[r].toLowerCase() === e,
  )
  return role ? PERSONAS[role] : null
}

export const authService = {
  /** Connexion : pose les cookies (session + CSRF) et renvoie l'utilisateur. */
  async login(email: string, password: string): Promise<User> {
    if (MODE === 'mock') {
      const user = personaByEmail(email)
      if (!user) throw new Error('Identifiants de démonstration inconnus.')
      return user
    }
    const res = await apiFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    setCsrf(res.csrf_token)
    setToken(res.token) // cross-origin : mémorise le Bearer ; same-origin : no-op
    return mapUser(res.utilisateur)
  },

  /** Utilisateur courant depuis le cookie de session, ou null si non authentifié. */
  async me(): Promise<User | null> {
    if (MODE === 'mock') {
      try {
        const raw = localStorage.getItem(SESSION_KEY)
        return raw ? (JSON.parse(raw) as User) : null
      } catch {
        return null
      }
    }
    try {
      const u = await apiFetch<BackendUser>('/auth/me')
      return mapUser(u)
    } catch {
      return null
    }
  },

  /** Révoque la session côté serveur et oublie le token CSRF local. */
  async logout(): Promise<void> {
    if (MODE === 'mock') {
      setCsrf(null)
      setToken(null)
      return
    }
    try {
      await apiFetch('/auth/logout', { method: 'POST' })
    } catch {
      /* session déjà expirée : on nettoie quand même côté client */
    } finally {
      setCsrf(null)
      setToken(null)
    }
  },
}
