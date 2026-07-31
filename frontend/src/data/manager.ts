import type { CollabProfile, RecoData, Offer, NotificationItem } from '@/types/domain'
import type { KpiCard } from '@/types/manager'

/** Profil du manager Jean-Marc Dupont (Directeur de Pôle Risques → Directeur Exécutif). */
export const MANAGER_PROFILE: CollabProfile = {
  progressionPct: 84,
  posteVise: 'Directeur Exécutif des Risques',
  horizon: 'Horizon 2 ans',
  description:
    "Directeur de Pôle Risques, j'anime une équipe de 8 collaborateurs et pilote la maîtrise du risque de crédit du portefeuille Corporate. Objectif : évoluer vers un rôle exécutif (COMEX).",
  aspirations: ['Direction exécutive des Risques', 'Influence COMEX', 'Vision stratégique Groupe'],
  zones: 'Casablanca · Paris',
  stations: [
    { period: '2012 · 2016', title: 'Analyste Risque Senior', desc: 'Scoring et modélisation.', state: 'past' },
    { period: '2016 · 2021', title: 'Manager Risques', desc: '5 collaborateurs.', state: 'past' },
    { period: '2021 · présent', title: 'Directeur de Pôle Risques', desc: '8 collaborateurs · portefeuille Corporate.', state: 'current' },
    { period: 'Objectif', title: 'Directeur Exécutif Risques', desc: 'Station visée · horizon 2028.', state: 'goal' },
  ],
  todos: [
    { icon: 'chat', title: 'Entretiens annuels', text: '2 entretiens en retard à programmer.', linkLabel: 'Programmer', to: 'manager.entretien' },
    { icon: 'route', title: "Souhaits d'évolution reçus", text: '3 souhaits de votre équipe à traiter.', linkLabel: 'Traiter', to: 'manager.souhaitsRecus' },
    { icon: 'brief', title: 'Postes à pourvoir', text: '3 postes ouverts · voir les profils recommandés.', linkLabel: 'Voir', to: 'manager.offres' },
  ],
  skills: [
    { label: 'Encadrement & leadership', pct: 82 },
    { label: 'Risque de crédit', pct: 92 },
    { label: 'Vision stratégique', pct: 64 },
    { label: 'Influence COMEX', pct: 58 },
    { label: 'Gestion de crise', pct: 66 },
  ],
  peerReviews: [
    { initials: 'NA', name: 'Nadia Alami', role: 'RH', text: 'Manager solide, développe bien ses talents. Prêt pour un rôle exécutif.', stars: 5 },
    { initials: 'SK', name: 'Sarah K.', role: 'Directrice', text: 'Excellente maîtrise du risque et sens du collectif.', stars: 5 },
  ],
}

/** Recommandations d'évolution du manager — vers le haut (COMEX). */
export const MANAGER_RECO: RecoData = {
  posteVise: 'Directeur Exécutif des Risques',
  pct: 62,
  skills: [
    { icon: 'route', title: 'Vision stratégique', desc: 'Appétit au risque et planification Groupe.', tag: 'SFIA · niveau 6' },
    { icon: 'spark', title: 'Influence COMEX', desc: 'Communication et arbitrages exécutifs.', tag: 'essentielle' },
    { icon: 'shield', title: 'Gestion de crise', desc: 'Continuité et résilience opérationnelle.', tag: 'essentielle', critical: true },
  ],
  passerelles: [
    { title: 'Chief Risk Officer (CRO) adjoint', pct: 74, label: 'Forte affinité', source: 'SFIA', tone: 'new' },
    { title: 'Directeur des Risques Régional', pct: 69, label: 'Bonne affinité', source: 'ESCO', tone: 'ai' },
    { title: 'Directeur Conformité & Risques', pct: 63, label: 'Affinité modérée', source: 'O*NET', tone: 'mut' },
  ],
  plan: "Pour viser Directeur Exécutif : (1) Vision stratégique · appétit au risque et planification Groupe ; (2) Influence COMEX · communication et arbitrages exécutifs ; (3) Gestion de crise · continuité et résilience.",
  confiance: 'clair',
}

/** Offres de mobilité du manager (niveau dirigeant). */
export const MANAGER_OFFERS: Offer[] = [
  {
    key: 'directeur-executif-risques',
    type: 'Poste', tone: 'mut', pct: 74, adq: 'Recommandé', ligne: 'Risque',
    title: 'Directeur Exécutif des Risques (COMEX)',
    sub: 'Direction exécutive de la filière Risques du Groupe.',
    meta: [{ icon: 'pin', label: 'Casablanca, Siège' }, { icon: 'brief', label: 'Mandat exécutif' }],
    managerInformed: false,
    ctx: 'Comité Exécutif · Filière Risques Groupe',
    missionTitle: 'Le mandat', tpill: null,
    mission: [
      "Membre du COMEX, vous portez l'appétit au risque du Groupe, arbitrez les expositions majeures et représentez la filière auprès du régulateur et du conseil.",
      'Vous fédérez les directeurs de pôle et pilotez la transformation de la fonction Risques.',
    ],
    skills: ['Vision stratégique', 'Influence COMEX', 'Gestion de crise', 'Leadership exécutif', 'Relation régulateur'],
    infos: [
      { icon: 'pin', label: 'Localisation · Casablanca, Siège' },
      { icon: 'brief', label: 'Mandat · exécutif (COMEX)' },
      { icon: 'cal', label: 'Ouverture · succession horizon 2027-2028' },
      { icon: 'user', label: 'Référent · Direction Générale' },
    ],
    noteIcon: 'shield', noteText: 'Candidature confidentielle : traitée directement par la Direction Générale.', noteOk: true,
    cta: "Manifester mon intérêt", ctaDetail: 'Manifester mon intérêt',
    fitTitle: '74 % de compatibilité',
    fitText: 'Vos écarts principaux : vision stratégique et influence COMEX — ciblés dans vos recommandations.',
  },
  {
    key: 'cro-adjoint',
    type: 'Poste', tone: 'mut', pct: 71, adq: 'Adapté', ligne: 'Risque',
    title: 'CRO Adjoint · Filière Risques',
    sub: 'Bras droit du Chief Risk Officer sur le pilotage transverse.',
    meta: [{ icon: 'pin', label: 'Casablanca' }, { icon: 'brief', label: 'CDI cadre dirigeant' }],
    managerInformed: false,
    ctx: 'Direction des Risques Groupe',
    missionTitle: 'Le poste', tpill: null,
    mission: [
      "Vous secondez le CRO sur la stratégie risque, la coordination des pôles et les instances de gouvernance.",
    ],
    skills: ['Pilotage transverse', 'Gouvernance', 'Vision stratégique', 'Reporting exécutif'],
    infos: [
      { icon: 'pin', label: 'Localisation · Casablanca, Siège' },
      { icon: 'brief', label: 'Contrat · cadre dirigeant' },
      { icon: 'cal', label: 'Prise de poste · T1 2027' },
      { icon: 'user', label: 'Référent · CRO Groupe' },
    ],
    noteIcon: 'shield', noteText: 'Candidature confidentielle.', noteOk: true,
    cta: 'Postuler', ctaDetail: 'Postuler à ce poste',
    fitTitle: '71 % de compatibilité',
    fitText: 'Une étape naturelle vers un mandat exécutif complet.',
  },
  {
    key: 'mission-transfo-risque',
    type: 'Mission transverse', tone: 'ai', pct: 80, adq: 'Très adapté', ligne: 'Risque',
    title: 'Sponsor · Transformation Data de la fonction Risques',
    sub: 'Piloter la feuille de route data & IA de la filière (20 % sur 9 mois).',
    meta: [{ icon: 'team', label: 'Cross-pôles' }, { icon: 'clock', label: '9 mois' }],
    managerInformed: false,
    ctx: 'Programme de transformation · Direction des Risques',
    missionTitle: 'La mission', tpill: '20 % de votre temps',
    mission: [
      'En tant que sponsor, vous portez la feuille de route data/IA de la fonction Risques : priorisation des cas d’usage, arbitrages et conduite du changement auprès des pôles.',
    ],
    skills: ['Sponsoring', 'Data & IA', 'Conduite du changement', 'Vision stratégique'],
    infos: [
      { icon: 'team', label: 'Format · sponsor cross-pôles' },
      { icon: 'clock', label: 'Durée · 9 mois, 20 % du temps' },
      { icon: 'cal', label: 'Démarrage · octobre 2026' },
      { icon: 'user', label: 'Sponsor exécutif · CRO' },
    ],
    noteIcon: 'bell', noteText: 'Mission de visibilité exécutive.', noteOk: false,
    cta: 'Me porter candidat', ctaDetail: 'Me porter candidat',
    fitTitle: 'Visibilité COMEX',
    fitText: 'Une exposition idéale pour préparer votre passage exécutif.',
  },
]

export const MANAGER_OFFER_LIGNES = ['Tout', 'Risque', 'Finance', 'Clientèle'] as const

/** Notifications du manager (destinations = routes manager, sans paramètre). */
export const MANAGER_NOTIFICATIONS: NotificationItem[] = [
  { id: 'mn1', icon: 'route', title: "Nouveau souhait d'évolution", text: 'Aya Bennani souhaite évoluer vers Manager d’équipe Risques.', time: 'Il y a 2 h', unread: true, to: 'manager.souhaitsRecus' },
  { id: 'mn2', icon: 'chat', title: 'Entretien en retard', text: 'Mehdi Chraibi n’a pas eu d’entretien depuis 15 mois.', time: 'Il y a 5 h', unread: true, to: 'manager.entretien' },
  { id: 'mn3', icon: 'spark', title: 'Haut potentiel détecté', text: 'Sofia Haddad (score 92) · apte au management de transition.', time: 'Hier', unread: true, to: 'manager.equipe' },
  { id: 'mn4', icon: 'brief', title: 'Poste à pourvoir', text: '3 candidats internes recommandés pour « Analyste Risque Senior ».', time: 'Il y a 2 j', unread: false, to: 'manager.offres' },
  { id: 'mn5', icon: 'award', title: 'Campagne d’évaluation', text: 'La campagne annuelle 2026 est ouverte pour votre équipe.', time: 'Il y a 3 j', unread: false, to: 'manager.equipe' },
]

/** KPI du tableau de bord manager. */
export const MANAGER_KPIS: KpiCard[] = [
  { icon: 'team', value: '8', label: 'Collaborateurs', to: 'manager.equipe' },
  { icon: 'chat', value: '2', label: 'Entretiens en retard', hint: 'à programmer', to: 'manager.entretien' },
  { icon: 'route', value: '3', label: "Souhaits à traiter", to: 'manager.souhaitsRecus' },
  { icon: 'brief', value: '3', label: 'Postes à pourvoir', to: 'manager.offres' },
]
