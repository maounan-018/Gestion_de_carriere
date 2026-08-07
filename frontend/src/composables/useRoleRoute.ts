import { useSessionStore } from '@/stores/session'

/**
 * Écrans PARTAGÉS entre rôles (ex. Recommandations, Passerelles) : construit le
 * nom de route préfixé par le rôle courant → `roleRoute('passerelles')` donne
 * `collab.passerelles`, `manager.passerelles`, etc. Évite de coder « collab. » en dur.
 */
export function roleRoute(name: string): string {
  const role = useSessionStore().role || 'collab'
  return `${role}.${name}`
}
