import type { Candidature } from '@/types/domain'

export const CANDIDATURES: Candidature[] = [
  { icon: 'spark', title: 'Ambassadeur Digital · Retail Banking', type: 'Mission transverse', date: '12 juillet 2026', status: 'Envoyée', tone: 'new' },
  { icon: 'brief', title: 'Analyste Crédit Senior · Corporate Banking', type: 'Poste', date: '28 juin 2026', status: 'En revue', tone: 'warn' },
  { icon: 'bolt', title: 'Task Force · IA Générative & Compliance', type: 'Projet', date: '15 juin 2026', status: 'Entretien planifié', tone: 'ai' },
  { icon: 'clock', title: 'Relecture Expertise · Rapport ESG 2026', type: 'Mission transverse', date: '2 mai 2026', status: 'Refusée', tone: 'hot' },
]
