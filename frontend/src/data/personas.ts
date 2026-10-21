import type { Role, User } from '@/types/domain'

/**
 * ⚠ Données de démonstration SYNTHÉTIQUES (aucune donnée réelle BMCI).
 * Un seul jeu de personas partagé par toute l'app (cf. manque G23 : cohérence inter-rôles).
 * E-mails d'affichage au format prenom.nom@bmci.local.
 */

/**
 * Comptes de démo seedés par le backend (`app/database/seed.py`). Les emails sont
 * publics (ce sont les comptes de démo synthétiques @bmci.local) ; le mot de passe
 * est injecté UNIQUEMENT à partir de la variable Vite `VITE_DEMO_PASSWORD`.
 *
 * - En DEV local : poser `VITE_DEMO_PASSWORD=…` dans `frontend/.env.local` (gitignored).
 *   Les écrans de démo (bouton « entrer en démo » / sélecteur Collab/Manager/HRBP)
 *   pré-remplissent alors email + MDP comme avant.
 * - En PROD / portfolio public (Vercel) : ne PAS définir la variable. Les écrans
 *   pré-remplissent uniquement l'email, le MDP reste vide — l'utilisateur doit
 *   le saisir manuellement. Objectif : ne jamais exposer de MDP dans le bundle JS.
 */
export const DEMO_EMAILS: Record<Role, string> = {
  collab: 'youssef.elamrani@bmci.local',
  manager: 'karim.naji@bmci.local',
  rh: 'nadia.alami@bmci.local',
}

/** MDP de démo pour `role`, lu depuis `VITE_DEMO_PASSWORD` (vide par défaut). */
export function demoPasswordFor(_role: Role): string {
  return (import.meta.env.VITE_DEMO_PASSWORD as string | undefined) ?? ''
}

export const PERSONAS: Record<Role, User> = {
  collab: {
    id: 'u-youssef',
    role: 'collab',
    name: 'Youssef El Amrani',
    firstName: 'Youssef',
    initials: 'YE',
    email: 'youssef.elamrani@bmci.local',
    title: 'Conseiller clientèle particuliers',
    entity: 'Retail Banking',
    roleLabel: 'Collaborateur',
  },
  manager: {
    id: 'u-karim',
    role: 'manager',
    name: 'Karim Naji',
    firstName: 'Karim',
    initials: 'KN',
    email: 'karim.naji@bmci.local',
    title: 'Directeur de Pôle Risques',
    entity: 'Direction des Risques',
    roleLabel: 'Manager',
  },
  rh: {
    id: 'u-nadia',
    role: 'rh',
    name: 'Nadia Alami',
    firstName: 'Nadia',
    initials: 'NA',
    email: 'nadia.alami@bmci.local',
    title: 'Responsable Développement RH',
    entity: 'Direction des Ressources Humaines',
    roleLabel: 'HRBP',
  },
}
