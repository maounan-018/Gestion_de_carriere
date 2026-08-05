import type { Role, User } from '@/types/domain'

/**
 * ⚠ Données de démonstration SYNTHÉTIQUES (aucune donnée réelle BMCI).
 * Un seul jeu de personas partagé par toute l'app (cf. manque G23 : cohérence inter-rôles).
 * E-mails d'affichage au format prenom.nom@bnpparibas.com.
 */

/**
 * Identifiants de connexion de démo — mappés sur les comptes SEEDÉS du backend
 * (`app/database/seed.py`, e-mails @bmci.local, mot de passe SEED_DEMO_PASSWORD).
 * ⚠ Démo/local uniquement. Le rôle réel est déterminé par le backend au login.
 */
export const DEMO_CREDENTIALS: Record<Role, { email: string; password: string }> = {
  collab: { email: 'youssef.elamrani@bmci.local', password: 'Bmci-Demo-2026!' },
  manager: { email: 'karim.naji@bmci.local', password: 'Bmci-Demo-2026!' },
  rh: { email: 'nadia.alami@bmci.local', password: 'Bmci-Demo-2026!' },
}
export const PERSONAS: Record<Role, User> = {
  collab: {
    id: 'u-youssef',
    role: 'collab',
    name: 'Youssef El Amrani',
    firstName: 'Youssef',
    initials: 'YE',
    email: 'youssef.elamrani@bnpparibas.com',
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
    email: 'karim.naji@bnpparibas.com',
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
    email: 'nadia.alami@bnpparibas.com',
    title: 'Responsable Développement RH',
    entity: 'Direction des Ressources Humaines',
    roleLabel: 'HRBP',
  },
}
