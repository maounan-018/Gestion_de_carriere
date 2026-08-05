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
  cvFilename?: string | null // CV conservé du collaborateur (Lot 4) — null si aucun
}

/* ------------------------------------------------------------- Cartographie */
export type Criticite = 'critique' | 'modéré' | 'bénin'
export interface CartoPole {
  name: string // libellé du département
  pole?: string // pôle macro de rattachement (regroupement de la heatmap, comme en live)
  levels: number[] // niveau 0-5 par famille (aligné sur CARTO_SKILLS)
  people: string[] // noms présents dans le pôle
  analyse?: { text: string; criticite: Criticite; focus?: string }
}

/* Cartographie DATA-DRIVEN (matrice flexible N pôles × M familles). Les colonnes
 * `familles` et les lignes viennent du backend — aucune taxonomie figée côté front. */
export interface CartoLigne {
  departementKey: string
  label: string
  pole?: string | null // pôle macro de rattachement (regroupement de la heatmap)
  effectif: number
  niveauMoyen: number | null
  niveaux: (number | null)[] // aligné sur `familles` (une cellule par colonne)
  people: string[]
}
export interface CartoMatrix {
  familles: string[] // colonnes (libellés de familles, déjà humanisés)
  lignes: CartoLigne[]
}

/** Synthèse RH consolidée (effectifs par pôle, pipeline candidatures, tensions). */
export interface SyntheseRh {
  effectif: number
  parPole: { pole: string; effectif: number }[]
  candidaturesParStatut: { statut: string; nombre: number }[]
  famillesEnTension: number
}

export type TensionLevel = 'faible' | 'moyenne' | 'forte'
/** Vue par FAMILLE : offre interne détenue vs demande des offres ouvertes → tension. */
export interface FamilleTension {
  famille: string // libellé humanisé
  detenues: number
  profilsCouverts: number
  niveauMoyen: number | null
  demande: number
  tension: TensionLevel
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

/* --------------------------------------------------- Fiches de poste (lecture) */
/** Item de liste pour le sélecteur « Publier une offre ». */
export interface FicheListItem {
  id: number
  intitule_poste: string
  departement_key: string
  perimetre_bmci: string
  famille_metier: string | null
}
export interface FicheCompetenceLite {
  libelle: string
  categorie: string | null
}
/** Détail d'une fiche de poste (affiché quand une fiche est choisie). */
export interface FicheDetail extends FicheListItem {
  mission: string | null
  activites_principales: string | null
  langues: string | null
  indicateurs_performances: string | null
  competences: FicheCompetenceLite[]
}

/* --------------------------------------------- Entretiens : cas à traiter (RH) */
/** Cas concret : entretien en retard / à planifier, avec collaborateur, manager
 *  responsable et ancienneté du dernier entretien réalisé (mois ; null = jamais). */
export interface EntretienCas {
  profilId: number
  nom: string
  prenom: string | null
  posteActuel: string | null
  departementKey: string | null
  type: 'annuel' | 'rh'
  statut: 'en_retard' | 'planifie'
  datePrevue: string | null
  moisDepuisDernier: number | null
  managerNom: string | null
}
