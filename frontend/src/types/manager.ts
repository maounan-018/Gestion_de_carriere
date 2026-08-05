import type { IconKey, OfferType, PillTone } from '@/types/domain'

/* ------------------------------------------------------------ Équipe */
export interface TeamSkill {
  label: string
  pct: number
}
export interface TeamEval {
  period: string
  score: string
  comment: string
  by: string
}
export interface TeamMember {
  id: string
  initials: string
  name: string
  role: string
  seniority: string
  ring: number // score global (%)
  evalScore: string // ex. « 4,8/5 »
  lastEntretien: string
  skills: TeamSkill[]
  strengths: string[]
  gaps: string[]
  aspiration: string
  aspirationHorizon: string
  evals: TeamEval[]
  flag?: 'top' | 'watch' | null // haut potentiel / à suivre
  cvFilename?: string | null // CV conservé du collaborateur (Lot 4) — null si aucun
}

/* --------------------------------------------- Postes vacants (équipe) */
export interface VacancyReco {
  memberId: string
  score: number
  label: string
  tone: PillTone
  why: string
}
export type VacancyStatus = 'brouillon' | 'validation' | 'ouvert' | 'clôturé'
export interface Vacancy {
  key: string
  title: string
  type: OfferType
  ligne: string
  sub: string
  openSince: string
  status: VacancyStatus
  recos: VacancyReco[]
}

/* ---------------------------------------------------- Souhaits reçus */
export type SouhaitRecuKind = 'mission' | 'carriere'
export type SouhaitRecuStatus = 'à traiter' | 'accordé' | 'transmis HRBP' | 'refusé'
export interface SouhaitRecu {
  id: string
  memberId: string
  memberName: string
  memberInitials: string
  title: string
  kind: SouhaitRecuKind
  horizon: string
  desc: string
  date: string
  status: SouhaitRecuStatus
}

/* -------------------------------------------------------- Dashboard KPI */
export interface KpiCard {
  icon: IconKey
  value: string
  label: string
  hint?: string
  to?: string
}
