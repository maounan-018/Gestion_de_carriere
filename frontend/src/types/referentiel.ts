/**
 * types/referentiel.ts — Formes ÉDITABLES des référentiels (gabarit + cartographie).
 * Miroir des schémas backend GabaritResponse / CartographieDoc (champs à plat).
 */

export type GabaritKind = 'metadata' | 'freetext' | 'skill_list' | 'languages' | 'kpi'

export interface GabaritSection {
  key: string
  label: string
  kind: GabaritKind
  categorie?: string | null
  aide?: string | null
}

export interface GabaritDoc {
  version?: number | null
  sections: GabaritSection[]
}

export interface CartoDept {
  key: string
  nom: string
  pole?: string | null
  metiers: string[]
}

export interface CartoDoc {
  version?: number | null
  departements: CartoDept[]
}

/** Fiche de poste générée par IA (miroir de FicheGeneree — contenu synthétique). */
export interface FicheGeneree {
  metier: string
  departement: string
  synthetique: boolean
  sections: Record<string, string>
  competences_reference: string[]
}
