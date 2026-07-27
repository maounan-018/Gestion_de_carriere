import type { Role, User } from '@/types/domain'
import { PERSONAS } from '@/data/personas'
import { apiFetch, setCsrf } from './http'

/**
 * Service d'authentification — API réelle (/api/auth/*).
 * Login par e-mail/mot de passe → cookies HttpOnly + token CSRF. L'identité
 * (id/nom/e-mail/rôle) vient du backend ; les champs présentationnels
 * (titre, entité, libellé, photo) sont fournis par le persona correspondant,
 * pour garder l'UI riche sans dupliquer ces données côté backend.
 */

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

export const authService = {
  /** Connexion locale : pose les cookies (session + CSRF) et renvoie l'utilisateur. */
  async login(email: string, password: string): Promise<User> {
    const res = await apiFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    setCsrf(res.csrf_token)
    return mapUser(res.utilisateur)
  },

  /** Utilisateur courant depuis le cookie de session, ou null si non authentifié. */
  async me(): Promise<User | null> {
    try {
      const u = await apiFetch<BackendUser>('/auth/me')
      return mapUser(u)
    } catch {
      return null
    }
  },

  /** Révoque la session côté serveur et oublie le token CSRF local. */
  async logout(): Promise<void> {
    try {
      await apiFetch('/auth/logout', { method: 'POST' })
    } catch {
      /* session déjà expirée : on nettoie quand même côté client */
    } finally {
      setCsrf(null)
    }
  },
}
