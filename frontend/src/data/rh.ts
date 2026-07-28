import type { CollabProfile, NotificationItem } from '@/types/domain'
import type { RhPerson, CartoPole, RhKpi, RhAlert, HautPotentiel, VeilleType } from '@/types/rh'

/**
 * Données RH (Nadia Alami) — fixtures synthétiques.
 * Jeu de personnes partagé avec l'espace manager (manque G23) + élargi aux autres pôles.
 */
export const RH_PEOPLE: RhPerson[] = [
  { id: 'aya', initials: 'AB', name: 'Aya Bennani', role: "Chargée d'Affaires Senior", pole: 'Risques', seniority: '6 ans', ring: 88, evalScore: '4,8/5', lastRh: '14 mois', aspiration: "Manager d'équipe Risques", aspirationHorizon: '12 mois', skills: [{ label: 'Analyse crédit', pct: 90 }, { label: 'Négociation', pct: 88 }, { label: 'Réglementaire', pct: 78 }], strengths: ['Rigueur', 'Sens du client'], gaps: ['Diriger une équipe'], flag: 'top' },
  { id: 'karim', initials: 'KI', name: 'Karim Idrissi', role: 'Analyste Risque', pole: 'Risques', seniority: '4 ans', ring: 82, evalScore: '4,3/5', lastRh: '8 mois', aspiration: 'Expert Modélisation', aspirationHorizon: '18 mois', skills: [{ label: 'IFRS 9', pct: 84 }, { label: 'Data / Python', pct: 80 }], strengths: ['Modélisation'], gaps: ['Communication'], flag: null },
  { id: 'sofia', initials: 'SH', name: 'Sofia Haddad', role: 'Analyste Middle Office', pole: 'Corporate', seniority: '5 ans', ring: 92, evalScore: '4,6/5', lastRh: '5 mois', aspiration: 'Management de transition', aspirationHorizon: '6·12 mois', skills: [{ label: 'Middle office', pct: 90 }, { label: 'Conformité', pct: 84 }], strengths: ['Excellence opérationnelle', 'Leadership'], gaps: ['Exposition stratégique'], flag: 'top' },
  { id: 'youssef', initials: 'YA', name: 'Youssef Amrani', role: 'Contrôleur de Gestion', pole: 'Finance', seniority: '3 ans', ring: 74, evalScore: '3,9/5', lastRh: '10 mois', aspiration: 'Contrôleur Senior', aspirationHorizon: '18 mois', skills: [{ label: 'Analyse financière', pct: 82 }, { label: 'Reporting', pct: 80 }], strengths: ['Reporting'], gaps: ['Business partnering'], flag: null },
  { id: 'leila', initials: 'LF', name: 'Leïla Fassi', role: 'Chargée de Conformité', pole: 'Conformité', seniority: '7 ans', ring: 86, evalScore: '4,5/5', lastRh: '6 mois', aspiration: 'Responsable Conformité', aspirationHorizon: '12 mois', skills: [{ label: 'Conformité', pct: 92 }, { label: 'KYC/LCB-FT', pct: 88 }], strengths: ['Expertise réglementaire'], gaps: ['Outils data'], flag: 'top' },
  { id: 'mehdi', initials: 'MC', name: 'Mehdi Chraibi', role: 'Trésorier Adjoint', pole: 'Finance', seniority: '2 ans', ring: 63, evalScore: '3,4/5', lastRh: '18 mois', aspiration: 'À clarifier', aspirationHorizon: '—', skills: [{ label: 'ALM', pct: 70 }, { label: 'Liquidité', pct: 68 }], strengths: ['Technique ALM'], gaps: ['Engagement'], riskDeparture: true, flag: 'watch' },
  { id: 'marc', initials: 'MV', name: 'Marc Vasseur', role: 'Ingénieur DevOps', pole: 'IT & Digital', seniority: '4 ans', ring: 79, evalScore: '4,1/5', lastRh: '11 mois', aspiration: 'Mission transverse · transformation agences', aspirationHorizon: 'Dès septembre', skills: [{ label: 'DevOps', pct: 88 }, { label: 'Cloud', pct: 82 }, { label: 'Cybersécurité', pct: 60 }], strengths: ['Automatisation'], gaps: ['Cybersécurité (ISO 27001)'], riskDeparture: true, flag: null },
  { id: 'omar', initials: 'OT', name: 'Omar Tazi', role: 'Analyste Crédit Junior', pole: 'Corporate', seniority: '1 an', ring: 68, evalScore: '3,8/5', lastRh: '4 mois', aspiration: 'Analyste confirmé', aspirationHorizon: '24 mois', skills: [{ label: 'Analyse crédit', pct: 66 }, { label: 'Excel', pct: 72 }], strengths: ['Motivation'], gaps: ['Autonomie'], flag: null },
]

/** Familles de compétences (colonnes de la heatmap). */
export const CARTO_SKILLS = ['Analyse', 'Risque', 'Digital', 'Compliance', 'Leadership', 'Data'] as const

/** Cartographie des compétences par pôle (9 pôles × 6 familles). */
export const CARTO_POLES: CartoPole[] = [
  { name: 'Corporate & Investment', levels: [5, 4, 2, 3, 4, 2], people: ['Sofia Haddad', 'Omar Tazi'], analyse: { text: 'Pôle mature en analyse et risque. Digitalisation à renforcer.', criticite: 'modéré', focus: 'Digital' } },
  { name: 'Retail', levels: [3, 3, 4, 2, 3, 1], people: [], analyse: { text: 'Bonne culture digitale, socle compliance et data à consolider.', criticite: 'modéré', focus: 'Compliance' } },
  { name: 'Risques', levels: [4, 5, 1, 4, 3, 2], people: ['Aya Bennani', 'Karim Idrissi'], analyse: { text: 'Expertise risque de référence. Déficit digital marqué à combler.', criticite: 'modéré', focus: 'Digital' } },
  { name: 'IT & Digital', levels: [2, 1, 5, 2, 2, 5], people: ['Marc Vasseur'], analyse: { text: 'Excellence digitale et data, mais déficit Cybersécurité critique (écart 24 % sur les certifications ISO 27001).', criticite: 'critique', focus: 'Cybersécurité' } },
  { name: 'Finance', levels: [4, 3, 3, 5, 4, 3], people: ['Youssef Amrani', 'Mehdi Chraibi'], analyse: { text: 'Pôle équilibré, fort en compliance et leadership.', criticite: 'bénin' } },
  { name: 'Conformité', levels: [3, 4, 2, 5, 3, 2], people: ['Leïla Fassi'], analyse: { text: 'Compliance excellente. Montée en compétences data recommandée.', criticite: 'bénin', focus: 'Data' } },
  { name: 'International', levels: [4, 3, 3, 3, 3, 2], people: [], analyse: { text: 'Profil homogène, à renforcer sur la data.', criticite: 'bénin' } },
  { name: 'Opérations', levels: [3, 2, 4, 3, 3, 3], people: [], analyse: { text: 'Bonne base digitale et data, expertise risque à renforcer.', criticite: 'modéré', focus: 'Risque' } },
  { name: 'Ressources Humaines', levels: [3, 2, 3, 4, 4, 3], people: ['Nadia Alami'], analyse: { text: 'Fort leadership et compliance, data en progression.', criticite: 'bénin' } },
]

export const RH_KPIS: RhKpi[] = [
  { icon: 'team', value: '2 850', label: 'Effectif total', hint: '+2,4 % / an' },
  { icon: 'route', value: '18,5 %', label: 'Promotion interne', to: 'rh.hautsPotentiels' },
  { icon: 'spark', value: '7,8/10', label: 'Engagement' },
  { icon: 'award', value: '12', label: 'Hauts potentiels', to: 'rh.hautsPotentiels' },
]

export const RH_ALERTS: RhAlert[] = [
  { id: 'a1', kind: 'retention', icon: 'shield', severity: 'crit', title: 'Risque de départ · IT & Digital', text: '2 profils clés présentent des signaux de désengagement (dont Marc Vasseur).', cta: 'Analyser la rétention', to: 'rh.retention' },
  { id: 'a2', kind: 'potential', icon: 'spark', severity: 'info', title: 'Hauts potentiels identifiés', text: 'Le moteur IA a identifié Sofia Haddad (92) apte au management de transition.', cta: 'Consulter', to: 'rh.hautsPotentiels' },
  { id: 'a3', kind: 'succession', icon: 'flag', severity: 'warn', title: 'Poste critique · succession', text: '« Directeur Asset Management » sans successeur désigné.', cta: 'Lancer une analyse', to: 'rh.hautsPotentiels' },
]

export const HAUTS_POTENTIELS: HautPotentiel[] = [
  { personId: 'sofia', score: 92, readiness: 'Prêt · 6-12 mois', target: 'Management de transition' },
  { personId: 'leila', score: 86, readiness: 'Prêt · 12 mois', target: 'Responsable Conformité' },
  { personId: 'aya', score: 88, readiness: 'À développer · 12 mois', target: "Manager d'équipe Risques" },
]

export const VEILLE: VeilleType[] = [
  { key: 'annuels', label: 'Entretiens annuels (managers)', desc: 'Menés par les managers auprès de leurs équipes.', done: 114, planned: 34, late: 12 },
  { key: 'rh', label: 'Entretiens RH (RH ↔ collaborateur)', desc: 'Menés par la RH : mobilité, aspirations, bien-être.', done: 34, planned: 18, late: 5 },
]

/** Candidature à une offre — le matching est un SCORE interprétable (couverture
 * des compétences du poste), jamais un filtre : tous les candidats restent visibles. */
export interface RhCandidate {
  personId: string
  /** Id de la candidature backend (pour la décision RH/manager). Absent en mock. */
  candidatureId?: string
  name: string
  initials: string
  role: string
  pole: string
  score: number
  matched: string[]
  gaps: string[]
  status: 'retenu' | 'entretien' | 'preselection' | 'nouveau' | 'ecarte'
  note?: string
}

export interface RhOffer {
  key: string
  title: string
  type: string
  ligne: string
  status: 'brouillon' | 'validation' | 'ouvert' | 'clôturé'
  candidates: number
  compatible: number
  retenu?: string
  /** Sous-ensemble nommé des candidatures (les autres sont sous le seuil de compatibilité). */
  candidateList?: RhCandidate[]
}
export const RH_OFFERS: RhOffer[] = [
  {
    key: 'resp-conformite', title: 'Responsable Conformité', type: 'Poste', ligne: 'Conformité',
    status: 'validation', candidates: 11, compatible: 4, retenu: 'Leïla Fassi',
    candidateList: [
      { personId: 'leila', name: 'Leïla Fassi', initials: 'LF', role: 'Chargée de Conformité', pole: 'Conformité', score: 94, matched: ['Conformité', 'KYC/LCB-FT', 'Réglementaire'], gaps: ['Outils data'], status: 'retenu', note: "Retenue par le comité — validation finale RH en cours." },
      { personId: 'sofia', name: 'Sofia Haddad', initials: 'SH', role: 'Analyste Middle Office', pole: 'Corporate', score: 81, matched: ['Conformité', 'Leadership'], gaps: ['KYC/LCB-FT', 'Exposition stratégique'], status: 'entretien' },
      { personId: 'karim', name: 'Karim Idrissi', initials: 'KI', role: 'Analyste Risque', pole: 'Risques', score: 72, matched: ['Réglementaire', 'Data / Python'], gaps: ['Conformité opérationnelle'], status: 'preselection' },
      { personId: 'youssef', name: 'Youssef Amrani', initials: 'YA', role: 'Contrôleur de Gestion', pole: 'Finance', score: 68, matched: ['Reporting', 'Analyse financière'], gaps: ['Conformité', 'KYC/LCB-FT'], status: 'preselection' },
      { personId: 'omar', name: 'Omar Tazi', initials: 'OT', role: 'Analyste Crédit Junior', pole: 'Corporate', score: 47, matched: ['Motivation'], gaps: ['Conformité', 'Séniorité', 'KYC/LCB-FT'], status: 'ecarte', note: 'Sous le seuil de compatibilité — reste consultable.' },
    ],
  },
  {
    key: 'analyste-risque-senior', title: 'Analyste Risque Senior', type: 'Poste', ligne: 'Risque',
    status: 'ouvert', candidates: 7, compatible: 3,
    candidateList: [
      { personId: 'karim', name: 'Karim Idrissi', initials: 'KI', role: 'Analyste Risque', pole: 'Risques', score: 87, matched: ['IFRS 9', 'Data / Python', 'Modélisation'], gaps: ['Communication'], status: 'entretien' },
      { personId: 'aya', name: 'Aya Bennani', initials: 'AB', role: "Chargée d'Affaires Senior", pole: 'Risques', score: 79, matched: ['Analyse crédit', 'Réglementaire'], gaps: ['Modélisation avancée'], status: 'preselection' },
      { personId: 'omar', name: 'Omar Tazi', initials: 'OT', role: 'Analyste Crédit Junior', pole: 'Corporate', score: 61, matched: ['Analyse crédit'], gaps: ['Séniorité', 'IFRS 9'], status: 'nouveau' },
    ],
  },
  { key: 'mission-esg', title: 'Mission · Rapport ESG 2026', type: 'Mission transverse', ligne: 'Finance', status: 'ouvert', candidates: 5, compatible: 2 },
  { key: 'cyber-lead', title: 'Lead Cybersécurité', type: 'Poste', ligne: 'IT & Digital', status: 'brouillon', candidates: 0, compatible: 0 },
]

export const RH_NOTIFICATIONS: NotificationItem[] = [
  { id: 'rn1', icon: 'flag', title: 'Entretien RH en retard', text: "Aya Bennani n'a pas eu d'entretien RH depuis 14 mois.", time: 'Il y a 1 h', unread: true, to: 'rh.annuaire' },
  { id: 'rn2', icon: 'route', title: "Nouveau souhait d'évolution", text: 'Marc Vasseur souhaite rejoindre une mission transverse.', time: 'Il y a 3 h', unread: true, to: 'rh.annuaire' },
  { id: 'rn3', icon: 'spark', title: 'Haut potentiel détecté', text: 'Sofia Haddad (score 92) apte au management de transition.', time: 'Il y a 5 h', unread: true, to: 'rh.hautsPotentiels' },
  { id: 'rn4', icon: 'award', title: "Campagne d'évaluation", text: '62 % complétée · 3 pôles en retard.', time: 'Hier', unread: false, to: 'rh.entretiens' },
  { id: 'rn5', icon: 'check', title: 'Revue automatique terminée', text: 'La revue nocturne a corrigé 3 anomalies.', time: 'Hier', unread: false, to: 'rh.supervision' },
]

export const NADIA_PROFILE: CollabProfile = {
  progressionPct: 78,
  posteVise: 'Directrice des Talents',
  horizon: 'Horizon 2 ans',
  description:
    "Responsable Développement RH, je pilote la mobilité interne, la cartographie des compétences et les hauts potentiels du Groupe. Objectif : Directrice des Talents.",
  aspirations: ['Direction des Talents', 'Stratégie RH Groupe', 'People analytics'],
  zones: 'Casablanca · Paris',
  stations: [
    { period: '2014 · 2018', title: 'Chargée de mobilité', desc: 'Mobilité interne.', state: 'past' },
    { period: '2018 · 2022', title: 'Business Partner RH', desc: 'Accompagnement des pôles.', state: 'past' },
    { period: '2022 · présent', title: 'Responsable Développement RH', desc: 'Talents & cartographie.', state: 'current' },
    { period: 'Objectif', title: 'Directrice des Talents', desc: 'Station visée · horizon 2028.', state: 'goal' },
  ],
  todos: [
    { icon: 'flag', title: 'Entretiens RH en retard', text: '12 entretiens à programmer.', linkLabel: 'Voir', to: 'rh.entretiens' },
    { icon: 'spark', title: 'Hauts potentiels', text: '3 profils à positionner.', linkLabel: 'Consulter', to: 'rh.hautsPotentiels' },
  ],
  skills: [
    { label: 'People analytics', pct: 84 },
    { label: 'Droit social', pct: 80 },
    { label: 'Mobilité interne', pct: 88 },
    { label: 'Leadership Groupe', pct: 62 },
    { label: 'Conduite du changement', pct: 66 },
  ],
  peerReviews: [
    { initials: 'SK', name: 'Sarah K.', role: 'DRH', text: 'Vision talents remarquable, pilotage data au top.', stars: 5 },
  ],
}
