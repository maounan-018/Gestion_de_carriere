/**
 * Accents des KPI cards — retour tuteur : « le blanc et le vert sont les
 * couleurs principales mais on pourrait avoir d'autres couleurs pour les KPI
 * cards ». Variété maîtrisée dans la charte (vert, teal, or, bleu) — jamais de
 * noir ni de sombre. Couleur de la pastille d'icône, cyclée par position pour
 * un rendu stable et lisible.
 */
const KPI_ACCENTS = [
  'bg-green-soft text-green-deep',
  'bg-teal-soft text-teal',
  'bg-gold-soft text-gold',
  'bg-sky-soft text-sky',
] as const

export const kpiAccent = (i: number): string => KPI_ACCENTS[i % KPI_ACCENTS.length]
