import { defineStore } from 'pinia'
import type { Role, User } from '@/types/domain'
import { authService } from '@/services/authService'
import { ApiError } from '@/services/http'

const STORAGE_KEY = 'bmci.session'

function loadUser(): User | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as User) : null
  } catch {
    return null
  }
}

function persist(user: User | null) {
  try {
    if (user) localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    else localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* stockage indisponible — session en mémoire uniquement */
  }
}

export const useSessionStore = defineStore('session', {
  state: () => ({
    // Cache local pour un rendu immédiat ; la source de vérité reste le cookie
    // de session (revalidé par hydrate() au démarrage).
    user: loadUser() as User | null,
    loading: false,
    hydrated: false,
  }),
  getters: {
    isAuthenticated: (s): boolean => s.user !== null,
    role: (s): Role | null => s.user?.role ?? null,
  },
  actions: {
    /** Revalide la session au démarrage : le cookie décide, pas le cache local. */
    async hydrate() {
      try {
        const user = await authService.me()
        this.user = user
        persist(user)
      } catch (e) {
        // 401 = cookie absent/invalide → la session n'existe pas : purge le cache
        // périmé. Autre erreur (réseau) → on garde le cache le temps de la session.
        if (e instanceof ApiError && e.status === 401) {
          this.user = null
          persist(null)
        }
      } finally {
        this.hydrated = true
      }
    },
    /** Session invalidée côté serveur (401 en cours d'usage) : purge locale, sans
     *  appel réseau (le cookie est déjà mort). La redirection est gérée par l'appelant. */
    expire() {
      this.user = null
      persist(null)
    },
    /** Connexion par e-mail / mot de passe (auth locale backend). */
    async login(email: string, password: string) {
      this.loading = true
      try {
        this.user = await authService.login(email, password)
        persist(this.user)
        return this.user
      } finally {
        this.loading = false
      }
    },
    async logout() {
      await authService.logout()
      this.user = null
      persist(null)
    },
  },
})
