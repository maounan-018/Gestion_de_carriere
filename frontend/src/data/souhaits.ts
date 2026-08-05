import type { Souhait } from '@/types/domain'

export const SOUHAITS: Souhait[] = [
  {
    title: "Manager d'équipe Risques",
    horizon: '12-18 mois',
    desc: "Encadrer une équipe d'analystes et développer une expertise réglementaire (Bâle III).",
    status: 'Transmise au manager',
    tone: 'new',
    pushed: true,
  },
  {
    title: 'Expert Data & Risque',
    horizon: '2 ans',
    desc: 'Expertise data appliquée au risque (modélisation avancée, Python).',
    status: 'Brouillon',
    tone: 'mut',
    pushed: false,
  },
]
