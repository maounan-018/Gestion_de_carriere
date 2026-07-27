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
  collab: { email: 'marc.bennani@bmci.local', password: 'Bmci-Demo-2026!' },
  manager: { email: 'jeanmarc.dupont@bmci.local', password: 'Bmci-Demo-2026!' },
  rh: { email: 'nadia.alami@bmci.local', password: 'Bmci-Demo-2026!' },
}
export const PERSONAS: Record<Role, User> = {
  collab: {
    id: 'u-marc',
    role: 'collab',
    name: 'Marc Bennani',
    firstName: 'Marc',
    initials: 'MB',
    email: 'marc.bennani@bnpparibas.com',
    title: 'Analyste Risque Senior',
    entity: 'Direction des Risques',
    roleLabel: 'Collaborateur',
  },
  manager: {
    id: 'u-jeanmarc',
    role: 'manager',
    name: 'Jean-Marc Dupont',
    firstName: 'Jean-Marc',
    initials: 'JM',
    email: 'jean-marc.dupont@bnpparibas.com',
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
    roleLabel: 'RH',
  },
}
