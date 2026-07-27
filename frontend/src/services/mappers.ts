/**
 * mappers.ts — Adaptateurs schémas backend → types front.
 *
 * Le backend renvoie des schémas NATIFS (français, sans présentation). Le front a
 * ses propres types (icônes, tons, libellés). Ces mappers font la traduction, en
 * un seul endroit, pour que les schémas back ne « fuient » jamais dans les vues.
 */

import type { IconKey, NotificationItem, Formation, Role } from '@/types/domain'

/* ------------------------------------------------------------------ Backend */
export interface NotificationOut {
  id: number
  type: string
  titre: string
  texte: string | null
  to_route: string | null
  lu: boolean
  created_at: string
}

export interface FormationOut {
  id: number
  titre: string
  provider: string | null
  duree: string | null
  niveau: string | null
  domaine: string | null
  tags: string[]
  skill_cible: string | null
  synthetique: boolean
}

/* -------------------------------------------------------------------- Utils */
/** Temps relatif court en français (« à l'instant », « il y a 3 h », « il y a 2 j »). */
export function relativeTime(iso: string): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ''
  const s = Math.max(0, Math.floor((Date.now() - then) / 1000))
  if (s < 60) return "à l'instant"
  const m = Math.floor(s / 60)
  if (m < 60) return `il y a ${m} min`
  const h = Math.floor(m / 60)
  if (h < 24) return `il y a ${h} h`
  const j = Math.floor(h / 24)
  if (j < 7) return `il y a ${j} j`
  const sem = Math.floor(j / 7)
  return `il y a ${sem} sem`
}

const NOTIF_ICONS: Record<string, IconKey> = {
  offre: 'brief',
  entretien: 'chat',
  souhait: 'route',
  action: 'bolt',
  info: 'bell',
}

// Résolution `to_route` (clé backend/maquette) → NOM de route Vue Router valide,
// par rôle. Toute clé inconnue retombe sur le tableau de bord du rôle (jamais de
// nom invalide, qui casserait le <RouterLink :to="{ name }">).
const NOTIF_ROUTE: Record<Role, Record<string, string>> = {
  collab: {
    offres: 'collab.offres', souhaitSuivi: 'collab.souhaits', entretien: 'collab.entretien',
    reco: 'collab.reco', formation: 'collab.formation', profil: 'collab.profil',
    recherche: 'collab.recherche', coach: 'collab.coach', mesCandidatures: 'collab.mesCandidatures',
  },
  manager: {
    souhaitsRecus: 'manager.souhaitsRecus', entretien: 'manager.entretien', offres: 'manager.offres',
    equipe: 'manager.equipe', reco: 'manager.reco', coach: 'manager.coach',
  },
  rh: {
    rhOffres: 'rh.offres', offres: 'rh.offres', cartographie: 'rh.cartographie',
    hautsPotentiels: 'rh.hautsPotentiels', veille: 'rh.entretiens', alertes: 'rh.alertes',
    annuaire: 'rh.annuaire', souhaitsRecus: 'rh.annuaire',
  },
}

function notifRoute(role: Role, key: string | null): string {
  return (key && NOTIF_ROUTE[role]?.[key]) || `${role}.dashboard`
}

/* ----------------------------------------------------------------- Mappers */
export function mapNotification(n: NotificationOut, role: Role): NotificationItem {
  return {
    id: String(n.id),
    icon: NOTIF_ICONS[n.type] ?? 'bell',
    title: n.titre,
    text: n.texte ?? '',
    time: relativeTime(n.created_at),
    unread: !n.lu,
    to: notifRoute(role, n.to_route),
  }
}

export function mapFormation(f: FormationOut): Formation {
  return {
    id: String(f.id),
    title: f.titre,
    provider: f.provider ?? '',
    duration: f.duree ?? '',
    level: f.niveau ?? '',
    status: 'recommended', // le backend n'a pas de suivi par collaborateur (LMS)
    progress: 0,
    tags: f.tags ?? [],
    reason: f.skill_cible ? `Compétence visée : ${f.skill_cible}` : undefined,
  }
}
