import type { IconKey } from '@/types/domain'
import type { TeamSkill } from '@/types/manager'

/* ------------------------------------------------------ Personnes (annuaire) */
export interface RhPerson {
  id: string
  initials: string
  name: string
  role: string
  pole: string
  seniority: string
  ring: number
  evalScore: string
  lastRh: string // dernier entretien RH
  aspiration: string
  aspirationHorizon: string
  skills: TeamSkill[]
  strengths: string[]
  gaps: string[]
  riskDeparture?: boolean
  flag?: 'top' | 'watch' | null
}

/* ------------------------------------------------------------- Cartographie */
export type Criticite = 'critique' | 'modéré' | 'bénin'
export interface CartoPole {
  name: string
  levels: number[] // niveau 0-5 par famille (aligné sur CARTO_SKILLS)
  people: string[] // noms présents dans le pôle
  analyse: { text: string; criticite: Criticite; focus?: string }
}

/* ---------------------------------------------------------------------- KPI */
export interface RhKpi {
  icon: IconKey
  value: string
  label: string
  hint?: string
  to?: string
}

/* ------------------------------------------------------------------ Alertes */
export type AlertKind = 'retention' | 'potential' | 'succession'
export type AlertSeverity = 'crit' | 'warn' | 'info'
export interface RhAlert {
  id: string
  kind: AlertKind
  icon: IconKey
  severity: AlertSeverity
  title: string
  text: string
  cta: string
  to: string
}

/* -------------------------------------------------- Hauts potentiels / veille */
export interface HautPotentiel {
  personId: string
  score: number
  readiness: string // ex. « Prêt · 6-12 mois »
  target: string // rôle cible
}

export interface VeilleType {
  key: 'annuels' | 'rh'
  label: string
  desc: string
  done: number
  planned: number
  late: number
}
