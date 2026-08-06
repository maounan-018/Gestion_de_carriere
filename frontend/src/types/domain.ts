/** Rôles de la plateforme. */
export type Role = 'collab' | 'manager' | 'rh'

/** Utilisateur connecté (persona en mock-first). */
export interface User {
  id: string
  role: Role
  name: string
  firstName: string
  initials: string
  email: string
  title: string // intitulé de poste
  entity: string
  roleLabel: string // 'Collaborateur' | 'Manager' | 'RH'
  photo?: string
}

/** Clés d'icônes (miroir des `ic('…')` des maquettes) — résolues en composants lucide via AppIcon. */
export type IconKey =
  | 'pin' | 'brief' | 'cal' | 'clock' | 'team' | 'book' | 'spark' | 'route'
  | 'award' | 'shield' | 'bell' | 'send' | 'check' | 'user' | 'mail'
  | 'grid' | 'search' | 'chat' | 'bolt' | 'filter' | 'lock' | 'flag'

export type PillTone = 'new' | 'hot' | 'warn' | 'mut' | 'ai' | 'ok'

export interface MetaItem {
  icon: IconKey
  label: string
}

/* ------------------------------------------------------------------ Offres */
export type OfferType = 'Poste' | 'Mission transverse' | 'Mentorat' | 'Projet'

export interface Offer {
  key: string
  type: OfferType
  tone: PillTone
  pct: number
  adq: string
  ligne: string
  title: string
  sub: string
  meta: MetaItem[]
  managerInformed: boolean
  managerName?: string
  ctx: string
  missionTitle: string
  mission: string[]
  skills: string[]
  infos: MetaItem[]
  noteIcon: IconKey
  noteText: string
  noteOk: boolean
  cta: string
  ctaDetail: string
  fitTitle: string
  fitText: string
  tpill?: string | null
}

/* ------------------------------------------------------------- Candidatures */
export type CandidatureStatus =
  | 'Envoyée' | 'En revue' | 'Entretien planifié' | 'Refusée' | 'Retenue' | 'Retirée'

export interface Candidature {
  /** Id backend (pour retirer la candidature). Absent en mock. */
  id?: string
  icon: IconKey
  title: string
  type: string
  date: string
  status: CandidatureStatus
  tone: PillTone
}

/* ----------------------------------------------------------- Notifications */
export interface NotificationItem {
  id: string
  icon: IconKey
  title: string
  text: string
  time: string
  unread: boolean
  to?: string // nom de route de destination
}

/* --------------------------------------------------------- Profil & courbe */
export interface ProgressionStation {
  period: string
  title: string
  desc?: string
  state: 'past' | 'current' | 'goal'
}

export interface TodoItem {
  icon: IconKey
  title: string
  text: string
  linkLabel: string
  to: string
}

export interface SkillLevel {
  label: string
  pct: number
  evaluee?: boolean // false = en attente d'évaluation (déclarée, pas encore scorée)
}

export interface PeerReview {
  initials: string
  name: string
  role: string
  text: string
  stars: number
}

export interface CollabProfile {
  progressionPct: number
  posteVise: string
  horizon: string
  description: string
  aspirations: string[]
  zones: string
  disponibilite: string
  typeEvolution: string
  stations: ProgressionStation[]
  todos: TodoItem[]
  skills: SkillLevel[]
  peerReviews: PeerReview[]
}

/** Champs AUTO-DÉCLARÉS éditables de son propre profil (collab / manager / RH).
 *  Sert au composant partagé « Éditer mon profil » et à `updateMyProfil`. */
export interface ProfilEditable {
  poste_actuel?: string
  aspirations?: string
  bio?: string
  poste_vise?: string
  horizon?: string
  type_evolution?: string
  mobilite_geo?: string
  disponibilite?: string
}

/** État du CV conservé de MON profil (Lot 4) : présence + horodatage + lien de
 *  téléchargement. `profilId` sert à construire l'URL de service du fichier. */
export interface MyCvStatus {
  profilId: number
  filename: string | null
  uploadedAt: string | null
}

/* --------------------------------------------------------------- Souhaits */
export type SouhaitStatus = 'Brouillon' | 'Transmise au manager' | 'En discussion'
export interface Souhait {
  /** Id backend (pour pousser / éditer). Absent en mock. */
  id?: string
  title: string
  horizon: string
  desc: string
  status: SouhaitStatus
  tone: PillTone
  pushed: boolean
}

/* --------------------------------------------------------- Recommandations */
export interface RecoSkill {
  icon: IconKey
  title: string
  desc: string
  tag: string
  critical?: boolean
}
export interface Passerelle {
  title: string
  pct: number
  label: string
  source: string
  tone: PillTone
}
export interface RecoData {
  posteVise: string
  pct: number
  skills: RecoSkill[]
  passerelles: Passerelle[]
  plan: string
  /** Fiabilité de l'objectif détecté : 'ambigu' → objectif à préciser (bandeau). */
  confiance: 'clair' | 'ambigu' | 'indisponible'
}

/** Passerelle de mobilité fondée sur les compétences détenues (graphe ESCO/O*NET). */
export interface MobiliteItem {
  id: number
  metier: string
  source: string       // esco | onet | sfia
  partagees: number    // nb de compétences détenues partagées avec ce métier
}

/* ------------------------------------------------------------- Formations */
export type FormationStatus = 'recommended' | 'in-progress' | 'done'
export interface Formation {
  id: string
  title: string
  provider: string
  duration: string
  level: string
  status: FormationStatus
  progress: number
  tags: string[]
  reason?: string
}

/* --------------------------------------------------------------- Collègues */
export interface Colleague {
  id: string
  initials: string
  name: string
  role: string
  entity: string
  skills: string[]
}

/* -------------------------------------------------------------------- Chat */
export interface ChatMessage {
  from: 'bot' | 'me'
  text: string
}
export interface ChatSuggestion {
  label: string
  q: string
}
