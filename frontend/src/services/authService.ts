import type { Role, User } from '@/types/domain'
import { PERSONAS } from '@/data/personas'

/**
 * Service d'authentification — MOCK-FIRST.
 * Simule un backend ; sera remplacé par des appels `/api/auth/*` (:5001) sans
 * toucher aux composants (même signature).
 */
export const authService = {
  async login(role: Role, _email?: string, _password?: string): Promise<User> {
    await delay(400) // simule la latence réseau
    return { ...PERSONAS[role] }
  },

  async logout(): Promise<void> {
    await delay(150)
  },
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}
