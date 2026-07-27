import type { NotificationItem } from '@/types/domain'

export const NOTIFICATIONS: NotificationItem[] = [
  { id: 'n1', icon: 'award', title: 'Nouvelle évaluation reçue', text: "Jean-Marc Dupont a finalisé votre évaluation annuelle 2025 · appréciation « Dépasse les attentes ».", time: 'Il y a 2 h', unread: true, to: 'collab.profil' },
  { id: 'n2', icon: 'brief', title: 'Candidature passée en revue', text: "Votre candidature au poste « Analyste Crédit Senior » est en cours d'examen par la Direction des Risques.", time: 'Il y a 5 h', unread: true, to: 'collab.mesCandidatures' },
  { id: 'n3', icon: 'spark', title: 'Nouvelles recommandations', text: '2 nouvelles opportunités correspondent à votre objectif Manager.', time: 'Hier', unread: true, to: 'collab.reco' },
  { id: 'n4', icon: 'book', title: 'Formation assignée', text: "Votre manager vous a assigné la formation « IFRS 9 avancé ».", time: 'Il y a 2 j', unread: false, to: 'collab.formation' },
  { id: 'n5', icon: 'cal', title: 'Entretien annuel à préparer', text: 'Votre entretien annuel approche : complétez votre bilan pour le préparer.', time: 'Il y a 3 j', unread: false, to: 'collab.entretien' },
]
