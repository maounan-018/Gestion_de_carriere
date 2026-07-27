import type { CollabProfile } from '@/types/domain'

/** Profil de carrière du collaborateur (persona Marc Bennani). */
export const COLLAB_PROFILE: CollabProfile = {
  progressionPct: 68,
  posteVise: "Manager d'équipe Risques",
  horizon: '12 à 18 mois',
  description:
    "Analyste Senior au Pôle Risques, référent du scoring IFRS 9. J'accompagne les chargés d'affaires sur l'analyse de contrepartie et je souhaite évoluer vers l'encadrement d'équipe.",
  aspirations: ['Management', 'Expertise', 'Mobilité géographique'],
  zones: 'Casablanca · Paris',
  stations: [
    { period: '2019 · 2021', title: 'Analyste Junior', desc: 'Graduate Program, portefeuille PME.', state: 'past' },
    { period: '2021 · 2023', title: 'Analyste', desc: 'Portefeuille Corporate.', state: 'past' },
    { period: '2023 · présent', title: 'Analyste Senior', desc: 'Référent scoring IFRS 9.', state: 'current' },
    { period: 'Objectif', title: "Manager d'équipe Risques", desc: 'Station visée · horizon 12-18 mois.', state: 'goal' },
  ],
  todos: [
    { icon: 'user', title: 'Complétez votre profil', text: 'Ajoutez vos aspirations pour affiner vos recommandations.', linkLabel: 'Compléter', to: 'collab.profil' },
    { icon: 'route', title: '2 recommandations à explorer', text: 'Des passerelles vers votre objectif Manager.', linkLabel: 'Voir les recommandations', to: 'collab.reco' },
    { icon: 'brief', title: 'Une offre correspond à 91 %', text: 'Analyste Crédit Senior · Corporate Banking.', linkLabel: 'Voir les offres', to: 'collab.offres' },
  ],
  skills: [
    { label: 'Analyse financière', pct: 88 },
    { label: 'Modélisation IFRS 9', pct: 82 },
    { label: 'Risque de contrepartie', pct: 78 },
    { label: 'Python · SQL', pct: 70 },
    { label: "Diriger une équipe", pct: 45 },
  ],
  peerReviews: [
    { initials: 'JM', name: 'Jean-Marc Dupont · Manager', role: 'Mars 2026', text: 'Analyste rigoureux, livrables fiables ; a pris en main le scoring corporate avec autonomie.', stars: 5 },
    { initials: 'YA', name: 'Yasmine Alaoui · Collègue', role: 'Fév. 2026', text: "Toujours disponible pour aider l'équipe sur les dossiers complexes.", stars: 5 },
    { initials: 'SC', name: 'Salma Cherkaoui · Collègue', role: 'Janv. 2026', text: 'Bonne pédagogie sur les sujets réglementaires.', stars: 4 },
  ],
}
