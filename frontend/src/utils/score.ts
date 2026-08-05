/**
 * Coloration des scores de maîtrise (%) — retour tuteur : « les scores ne
 * doivent pas tous être en verts ; du vert, de l'orange, du rouge selon le
 * pourcentage de maîtrise ». Charte respectée : vert, or/orange (warning),
 * rouge (danger) — jamais de noir.
 *
 * Seuils : ≥ 70 % maîtrisé (vert) · 40–69 % à consolider (orange) ·
 * < 40 % à développer (rouge).
 */
export type ScoreTone = 'green' | 'warn' | 'danger'

export function scoreTone(pct: number): ScoreTone {
  if (pct >= 70) return 'green'
  if (pct >= 40) return 'warn'
  return 'danger'
}

const TONE_TEXT: Record<ScoreTone, string> = {
  green: 'text-green-deep',
  warn: 'text-warning',
  danger: 'text-danger',
}
const TONE_BAR: Record<ScoreTone, string> = {
  green: 'bg-green',
  warn: 'bg-warning',
  danger: 'bg-danger',
}
const TONE_LABEL: Record<ScoreTone, string> = {
  green: 'Maîtrisé',
  warn: 'À consolider',
  danger: 'À développer',
}

/** Classe de couleur de texte pour un score en %. */
export const scoreText = (pct: number): string => TONE_TEXT[scoreTone(pct)]
/** Classe de couleur de barre/pastille pleine pour un score en %. */
export const scoreBar = (pct: number): string => TONE_BAR[scoreTone(pct)]
/** Intitulé du niveau de maîtrise correspondant. */
export const scoreLabel = (pct: number): string => TONE_LABEL[scoreTone(pct)]

/**
 * Tri STRICTEMENT décroissant par pourcentage (retour tuteur : « les
 * compétences en tête de liste = les plus forts pourcentages »). Copie non
 * mutante ; départage stable par libellé pour un ordre déterministe.
 */
export function byPctDesc<T extends { pct: number; label?: string; name?: string }>(
  items: readonly T[],
): T[] {
  return [...items].sort(
    (a, b) => b.pct - a.pct || (a.label ?? a.name ?? '').localeCompare(b.label ?? b.name ?? ''),
  )
}
