import { defineStore } from 'pinia'
import type { Role, User } from '@/types/domain'
import { authService } from '@/services/authService'

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
    user: loadUser() as User | null,
    loading: false,
  }),
  getters: {
    isAuthenticated: (s): boolean => s.user !== null,
    role: (s): Role | null => s.user?.role ?? null,
  },
  actions: {
    async login(role: Role, email?: string, password?: string) {
      this.loading = true
      try {
        this.user = await authService.login(role, email, password)
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
