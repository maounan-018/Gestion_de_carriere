import type { RecoData } from '@/types/domain'

/** Recommandations de parcours — ancrées sur le poste visé (ESCO · O*NET · SFIA). */
export const RECO: RecoData = {
  posteVise: "Manager d'équipe Risques",
  pct: 68,
  skills: [
    {
      icon: 'team', title: "Diriger une équipe",
      desc: 'Animer, prioriser et faire monter en compétence une équipe de 5 à 8 analystes.',
      tag: 'ESCO', critical: true,
    },
    {
      icon: 'route', title: 'Conduite d\'entretien',
      desc: "Mener des entretiens d'évaluation et de développement structurés.",
      tag: 'ESCO',
    },
    {
      icon: 'shield', title: 'Pilotage du risque',
      desc: 'Superviser le coût du risque du portefeuille et les arbitrages associés.',
      tag: 'SFIA · niveau 5',
    },
  ],
  passerelles: [
    { title: "Manager d'équipe Risques", pct: 82, label: 'Forte affinité', source: 'ESCO', tone: 'new' },
    { title: 'Analyste Crédit Senior · Corporate', pct: 74, label: 'Bonne affinité', source: 'ESCO', tone: 'ai' },
    { title: 'Chef de Projet Lean Management', pct: 63, label: 'Affinité modérée', source: 'O*NET', tone: 'mut' },
  ],
  plan:
    "Pour viser Manager d'équipe Risques : (1) combler l'écart « Diriger une équipe » via le mentorat ; (2) développer la conduite d'entretien ; (3) monter sur le pilotage du coût du risque.",
}
