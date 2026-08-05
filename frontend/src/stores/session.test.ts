import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { ApiError } from '@/services/http'
import type { User } from '@/types/domain'

// authService mocké : on ne teste que la logique du store (pas le réseau).
vi.mock('@/services/authService', () => ({
  authService: { login: vi.fn(), me: vi.fn(), logout: vi.fn() },
}))
import { authService } from '@/services/authService'
import { useSessionStore } from './session'

const STORAGE_KEY = 'bmci.session'

const marc: User = {
  id: '3', role: 'collab', name: 'Youssef El Amrani', firstName: 'Youssef', initials: 'YE',
  email: 'youssef.elamrani@bnpparibas.com', title: 'Analyste Senior', entity: 'Risques',
  roleLabel: 'Collaborateur',
}

// localStorage en mémoire (env node : pas de DOM).
let mem: Record<string, string> = {}
const lsStub = {
  getItem: (k: string) => (k in mem ? mem[k] : null),
  setItem: (k: string, v: string) => { mem[k] = String(v) },
  removeItem: (k: string) => { delete mem[k] },
  clear: () => { mem = {} },
}

beforeEach(() => {
  mem = {}
  vi.stubGlobal('localStorage', lsStub)
  vi.mocked(authService.login).mockReset()
  vi.mocked(authService.me).mockReset()
  vi.mocked(authService.logout).mockReset().mockResolvedValue(undefined)
  setActivePinia(createPinia())
})

describe('session store — état & getters', () => {
  it('démarre non authentifié sans cache', () => {
    const s = useSessionStore()
    expect(s.user).toBeNull()
    expect(s.isAuthenticated).toBe(false)
    expect(s.role).toBeNull()
  })

  it('hydrate le cache local au démarrage', () => {
    mem[STORAGE_KEY] = JSON.stringify(marc)
    const s = useSessionStore()
    expect(s.user?.name).toBe('Youssef El Amrani')
    expect(s.isAuthenticated).toBe(true)
    expect(s.role).toBe('collab')
  })
})

describe('session store — login / logout', () => {
  it('login pose l’utilisateur et le persiste', async () => {
    vi.mocked(authService.login).mockResolvedValue(marc)
    const s = useSessionStore()
    await s.login('youssef.elamrani@bnpparibas.com', 'x')
    expect(s.user).toEqual(marc)
    expect(s.isAuthenticated).toBe(true)
    expect(JSON.parse(mem[STORAGE_KEY]).id).toBe('3')
  })

  it('logout révoque côté serveur puis vide user + cache', async () => {
    mem[STORAGE_KEY] = JSON.stringify(marc)
    const s = useSessionStore()
    await s.logout()
    expect(authService.logout).toHaveBeenCalledOnce()
    expect(s.user).toBeNull()
    expect(mem[STORAGE_KEY]).toBeUndefined()
  })
})

describe('session store — durcissement #4', () => {
  it('expire() purge localement SANS appel réseau', () => {
    mem[STORAGE_KEY] = JSON.stringify(marc)
    const s = useSessionStore()
    s.expire()
    expect(s.user).toBeNull()
    expect(mem[STORAGE_KEY]).toBeUndefined()
    expect(authService.logout).not.toHaveBeenCalled() // cookie déjà mort
  })

  it('hydrate() : cookie valide → pose l’utilisateur', async () => {
    vi.mocked(authService.me).mockResolvedValue(marc)
    const s = useSessionStore()
    await s.hydrate()
    expect(s.user).toEqual(marc)
    expect(s.hydrated).toBe(true)
  })

  it('hydrate() : 401 → purge le cache périmé', async () => {
    mem[STORAGE_KEY] = JSON.stringify(marc) // cache présent…
    vi.mocked(authService.me).mockRejectedValue(new ApiError(401, 'Non authentifié'))
    const s = useSessionStore()
    expect(s.user).not.toBeNull() // …chargé au départ
    await s.hydrate()
    expect(s.user).toBeNull() // purge sur 401
    expect(mem[STORAGE_KEY]).toBeUndefined()
    expect(s.hydrated).toBe(true)
  })

  it('hydrate() : erreur réseau (non-401) → garde le cache', async () => {
    mem[STORAGE_KEY] = JSON.stringify(marc)
    vi.mocked(authService.me).mockRejectedValue(new ApiError(503, 'Service indisponible'))
    const s = useSessionStore()
    await s.hydrate()
    expect(s.user?.name).toBe('Youssef El Amrani') // cache conservé le temps de la session
    expect(mem[STORAGE_KEY]).toBeDefined()
    expect(s.hydrated).toBe(true)
  })
})
