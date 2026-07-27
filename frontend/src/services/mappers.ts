/**
 * mappers.ts — Adaptateurs schémas backend → types front.
 *
 * Le backend renvoie des schémas NATIFS (français, sans présentation). Le front a
 * ses propres types (icônes, tons, libellés). Ces mappers font la traduction, en
 * un seul endroit, pour que les schémas back ne « fuient » jamais dans les vues.
 */

import type {
  IconKey, NotificationItem, Formation, Role, PillTone,
  Souhait, SouhaitStatus, CollabProfile, ProgressionStation, SkillLevel, PeerReview, Colleague,
  Offer, OfferType, MetaItem, Candidature, CandidatureStatus,
} from '@/types/domain'
import type { SouhaitRecu, KpiCard, TeamSkill, TeamMember } from '@/types/manager'
import type { RhKpi, RhAlert, HautPotentiel, VeilleType, RhPerson } from '@/types/rh'

/* ------------------------------------------------------------------ Backend */
export interface NotificationOut {
  id: number
  type: string
  titre: string
  texte: string | null
  to_route: string | null
  lu: boolean
  created_at: string
}

export interface FormationOut {
  id: number
  titre: string
  provider: string | null
  duree: string | null
  niveau: string | null
  domaine: string | null
  tags: string[]
  skill_cible: string | null
  synthetique: boolean
}

/* -------------------------------------------------------------------- Utils */
/** Temps relatif court en français (« à l'instant », « il y a 3 h », « il y a 2 j »). */
export function relativeTime(iso: string): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ''
  const s = Math.max(0, Math.floor((Date.now() - then) / 1000))
  if (s < 60) return "à l'instant"
  const m = Math.floor(s / 60)
  if (m < 60) return `il y a ${m} min`
  const h = Math.floor(m / 60)
  if (h < 24) return `il y a ${h} h`
  const j = Math.floor(h / 24)
  if (j < 7) return `il y a ${j} j`
  const sem = Math.floor(j / 7)
  return `il y a ${sem} sem`
}

const NOTIF_ICONS: Record<string, IconKey> = {
  offre: 'brief',
  entretien: 'chat',
  souhait: 'route',
  action: 'bolt',
  info: 'bell',
}

// Résolution `to_route` (clé backend/maquette) → NOM de route Vue Router valide,
// par rôle. Toute clé inconnue retombe sur le tableau de bord du rôle (jamais de
// nom invalide, qui casserait le <RouterLink :to="{ name }">).
const NOTIF_ROUTE: Record<Role, Record<string, string>> = {
  collab: {
    offres: 'collab.offres', souhaitSuivi: 'collab.souhaits', entretien: 'collab.entretien',
    reco: 'collab.reco', formation: 'collab.formation', profil: 'collab.profil',
    recherche: 'collab.recherche', coach: 'collab.coach', mesCandidatures: 'collab.mesCandidatures',
  },
  manager: {
    souhaitsRecus: 'manager.souhaitsRecus', entretien: 'manager.entretien', offres: 'manager.offres',
    equipe: 'manager.equipe', reco: 'manager.reco', coach: 'manager.coach',
  },
  rh: {
    rhOffres: 'rh.offres', offres: 'rh.offres', cartographie: 'rh.cartographie',
    hautsPotentiels: 'rh.hautsPotentiels', veille: 'rh.entretiens', alertes: 'rh.alertes',
    annuaire: 'rh.annuaire', souhaitsRecus: 'rh.annuaire',
  },
}

function notifRoute(role: Role, key: string | null): string {
  return (key && NOTIF_ROUTE[role]?.[key]) || `${role}.dashboard`
}

/* ----------------------------------------------------------------- Mappers */
export function mapNotification(n: NotificationOut, role: Role): NotificationItem {
  return {
    id: String(n.id),
    icon: NOTIF_ICONS[n.type] ?? 'bell',
    title: n.titre,
    text: n.texte ?? '',
    time: relativeTime(n.created_at),
    unread: !n.lu,
    to: notifRoute(role, n.to_route),
  }
}

export function mapFormation(f: FormationOut): Formation {
  return {
    id: String(f.id),
    title: f.titre,
    provider: f.provider ?? '',
    duration: f.duree ?? '',
    level: f.niveau ?? '',
    status: 'recommended', // le backend n'a pas de suivi par collaborateur (LMS)
    progress: 0,
    tags: f.tags ?? [],
    reason: f.skill_cible ? `Compétence visée : ${f.skill_cible}` : undefined,
  }
}

/* ===================================================================== */
/*  Souhaits                                                             */
/* ===================================================================== */
export interface SouhaitOut {
  id: number
  profil_id: number
  titre: string
  kind: string
  horizon: string | null
  description: string | null
  statut: string
  pushed: boolean
  created_at: string
  decided_at: string | null
}
export interface SouhaitRecuOut extends SouhaitOut {
  membre_nom: string
  membre_prenom: string | null
  membre_matricule: string | null
}

const SOUHAIT_STATUS: Record<string, { status: SouhaitStatus; tone: PillTone }> = {
  brouillon: { status: 'Brouillon', tone: 'mut' },
  pousse: { status: 'Poussé au manager', tone: 'ai' },
  en_discussion: { status: 'En discussion', tone: 'new' },
  accorde: { status: 'En discussion', tone: 'ok' },
  refuse: { status: 'En discussion', tone: 'warn' },
}
const RECU_STATUS: Record<string, SouhaitRecu['status']> = {
  brouillon: 'à traiter', pousse: 'à traiter', en_discussion: 'transmis RH',
  accorde: 'accordé', refuse: 'refusé',
}

function initialsOf(name: string): string {
  const p = name.trim().split(/\s+/)
  return ((p[0]?.[0] ?? '') + (p[1]?.[0] ?? '')).toUpperCase()
}

export function mapSouhait(s: SouhaitOut): Souhait {
  const m = SOUHAIT_STATUS[s.statut] ?? SOUHAIT_STATUS.brouillon
  return {
    title: s.titre,
    horizon: s.horizon ?? '',
    desc: s.description ?? '',
    status: m.status,
    tone: m.tone,
    pushed: s.pushed,
  }
}

export function mapSouhaitRecu(s: SouhaitRecuOut): SouhaitRecu {
  const name = `${s.membre_prenom ?? ''} ${s.membre_nom}`.trim()
  return {
    id: String(s.id),
    memberId: String(s.profil_id),
    memberName: name,
    memberInitials: initialsOf(name),
    title: s.titre,
    kind: s.kind === 'mission' ? 'mission' : 'carriere',
    horizon: s.horizon ?? '',
    desc: s.description ?? '',
    date: relativeTime(s.created_at),
    status: RECU_STATUS[s.statut] ?? 'à traiter',
  }
}

/* ===================================================================== */
/*  Dashboards : KPIs, hauts potentiels, veille, alertes                 */
/* ===================================================================== */
export interface KpiItemOut { key: string; value: number; label: string; hint: string | null }
export interface HautPotentielOut {
  profil_id: number; nom: string; prenom: string | null; poste_actuel: string | null
  departement_key: string | null; score: number; nb_competences: number; niveau_moyen: number | null
}
export interface VeilleOut { key: string; label: string; realises: number; planifies: number; en_retard: number }
export interface AlerteOut {
  kind: string; severity: string; titre: string; texte: string; cta: string; to_route: string | null
}

const KPI_ICON: Record<string, IconKey> = {
  effectif: 'team', offres_ouvertes: 'brief', offres: 'brief', candidatures: 'send',
  competences: 'grid', formations: 'book', equipe: 'team', souhaits: 'route',
}
const KPI_ROUTE: Record<string, string | undefined> = {
  effectif: 'rh.annuaire', offres_ouvertes: 'rh.offres', competences: 'rh.cartographie',
  equipe: 'manager.equipe', offres: 'manager.offres', souhaits: 'manager.souhaitsRecus',
}
export function mapKpi(k: KpiItemOut): RhKpi {
  return {
    icon: KPI_ICON[k.key] ?? 'grid',
    value: String(k.value),
    label: k.label,
    hint: k.hint ?? undefined,
    to: KPI_ROUTE[k.key],
  }
}
// Structurellement identique à RhKpi (icon/value/label/hint/to).
export const mapKpiCard = (k: KpiItemOut): KpiCard => mapKpi(k)

export function mapHautPotentiel(h: HautPotentielOut): HautPotentiel {
  const readiness =
    h.score >= 85 ? 'Prêt · 6-12 mois' : h.score >= 75 ? 'Prêt · 12-18 mois' : 'À développer · 18-24 mois'
  return {
    personId: String(h.profil_id),
    score: h.score,
    readiness,
    target: h.poste_actuel ?? 'Évolution',
  }
}

export function mapVeille(v: VeilleOut): VeilleType {
  return {
    key: v.key === 'rh' ? 'rh' : 'annuels',
    label: v.label,
    desc: `${v.realises} réalisés · ${v.planifies} planifiés · ${v.en_retard} en retard`,
    done: v.realises,
    planned: v.planifies,
    late: v.en_retard,
  }
}

const ALERTE_ICON: Record<string, IconKey> = { potential: 'spark', succession: 'route', retention: 'shield' }
const ALERTE_ROUTE: Record<string, string> = {
  hautsPotentiels: 'rh.hautsPotentiels', veille: 'rh.entretiens', souhaitsRecus: 'rh.annuaire',
}
export function mapAlerte(a: AlerteOut): RhAlert {
  return {
    id: a.kind,
    kind: (['retention', 'potential', 'succession'].includes(a.kind) ? a.kind : 'potential') as RhAlert['kind'],
    icon: ALERTE_ICON[a.kind] ?? 'bell',
    severity: (['crit', 'warn', 'info'].includes(a.severity) ? a.severity : 'info') as RhAlert['severity'],
    title: a.titre,
    text: a.texte,
    cta: a.cta,
    to: (a.to_route && ALERTE_ROUTE[a.to_route]) || 'rh.dashboard',
  }
}

/* ===================================================================== */
/*  Profil carrière                                                      */
/* ===================================================================== */
export interface StationOut { periode: string; titre: string; description: string | null; etat: string; ordre: number }
export interface PeerReviewOut { auteur_nom: string; auteur_role: string | null; initiales: string | null; texte: string; etoiles: number }
export interface SkillNiveauOut { libelle: string; categorie: string | null; niveau: number | null }
export interface ProfilCarriereOut {
  profil_id: number; nom: string; prenom: string | null; poste_actuel: string | null
  departement_key: string | null; aspirations: string | null
  competences: SkillNiveauOut[]; stations: StationOut[]; avis_pairs: PeerReviewOut[]
}

const STATION_STATE: Record<string, ProgressionStation['state']> = {
  passe: 'past', actuel: 'current', objectif: 'goal',
}

export function mapCollabProfile(c: ProfilCarriereOut): CollabProfile {
  const skills: SkillLevel[] = c.competences.map((s) => ({
    label: s.libelle, pct: Math.min(100, (s.niveau ?? 3) * 20),
  }))
  const stations: ProgressionStation[] = [...c.stations]
    .sort((a, b) => a.ordre - b.ordre)
    .map((s) => ({
      period: s.periode, title: s.titre,
      desc: s.description ?? undefined, state: STATION_STATE[s.etat] ?? 'past',
    }))
  const peerReviews: PeerReview[] = c.avis_pairs.map((a) => ({
    initials: a.initiales ?? initialsOf(a.auteur_nom),
    name: a.auteur_nom, role: a.auteur_role ?? '', text: a.texte, stars: a.etoiles,
  }))
  const goal = stations.find((s) => s.state === 'goal')
  const avgNiveau =
    c.competences.length > 0
      ? c.competences.reduce((sum, s) => sum + (s.niveau ?? 0), 0) / c.competences.length
      : 0
  return {
    progressionPct: Math.round(avgNiveau * 20),
    posteVise: goal?.title ?? c.poste_actuel ?? '—',
    horizon: '',
    description: c.aspirations ?? '',
    aspirations: c.aspirations ? [c.aspirations] : [],
    zones: '',
    stations,
    todos: [],
    skills,
    peerReviews,
  }
}

/* ===================================================================== */
/*  Profil → personne (annuaire RH / hauts potentiels)                   */
/* ===================================================================== */
export interface ProfilCompetenceOut {
  id: number; libelle: string; categorie: string | null; niveau: number | null
  source: string; skill_id: number | null; skill_label_fr: string | null
}
export interface ProfilOut {
  id: number; user_id: number | null; nom: string; prenom: string | null; matricule: string | null
  poste_actuel: string | null; departement_key: string | null; manager_id: number | null
  aspirations: string | null; synthetique: boolean; created_at: string; competences: ProfilCompetenceOut[]
}

const POLE_LABEL: Record<string, string> = {
  ressources_humaines: 'Ressources Humaines', retail_banking: 'Retail Banking',
  corporate_banking: 'Corporate Banking', risques: 'Risques', finance: 'Finance',
  systeme_information: "Systèmes d'Information", conformite: 'Conformité',
  chief_data_office: 'Chief Data Office', alm_treasury: 'ALM Treasury',
  digital_factory: 'Digital Factory', marketing_communication: 'Marketing & Communication',
  monetique: 'Monétique',
}
function poleLabel(key: string | null): string {
  if (!key) return '—'
  return POLE_LABEL[key] ?? key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

/** Mappe un profil backend vers une `RhPerson`. Les champs non portés par le backend
 *  (ancienneté, dernier entretien RH, éval) prennent un repli neutre — à enrichir
 *  quand les endpoints correspondants existeront. */
export function mapProfil(p: ProfilOut): RhPerson {
  const name = `${p.prenom ?? ''} ${p.nom}`.trim()
  const comps = p.competences ?? []
  const niveaux = comps.map((c) => c.niveau).filter((n): n is number => n != null)
  const moy = niveaux.length ? niveaux.reduce((a, b) => a + b, 0) / niveaux.length : 3
  const skills: TeamSkill[] = comps.slice(0, 6).map((c) => ({
    label: c.skill_label_fr || c.libelle, pct: Math.min(100, (c.niveau ?? 3) * 20),
  }))
  return {
    id: String(p.id),
    initials: initialsOf(name),
    name,
    role: p.poste_actuel ?? '—',
    pole: poleLabel(p.departement_key),
    seniority: '—',
    ring: Math.round(moy * 20),
    evalScore: '—',
    lastRh: '—',
    aspiration: p.aspirations ?? '',
    aspirationHorizon: '',
    skills,
    strengths: comps.filter((c) => (c.niveau ?? 0) >= 4).slice(0, 3).map((c) => c.skill_label_fr || c.libelle),
    gaps: [],
    flag: null,
  }
}

/* ------------------------------------------------------------------ Annuaire */
export interface AnnuaireOut {
  id: number; nom: string; prenom: string | null
  poste_actuel: string | null; departement_key: string | null; competences: string[]
}

/** Mappe une entrée d'annuaire backend vers un `Colleague` (recherche collègues). */
export function mapColleague(a: AnnuaireOut): Colleague {
  const name = `${a.prenom ?? ''} ${a.nom}`.trim()
  return {
    id: String(a.id),
    initials: initialsOf(name),
    name,
    role: a.poste_actuel ?? '—',
    entity: poleLabel(a.departement_key),
    skills: a.competences ?? [],
  }
}

/* -------------------------------------------------------------------- Offres */
export interface OffreCompatOut {
  id: number; type: string; titre: string; description: string | null
  perimetre_bmci: string | null; departement_key: string | null; statut: string
  competences: string[]; score_compat: number | null; couvertes: number; ecarts: number
}

const OFFRE_TYPE_LABEL: Record<string, OfferType> = {
  offre_poste: 'Poste', mission: 'Mission transverse',
  projet: 'Projet innovation', gig: 'Mission transverse',
}
const OFFRE_STATUT_LABEL: Record<string, string> = {
  brouillon: 'Brouillon', ouverte: 'Ouverte', pourvue: 'Pourvue',
  fermee: 'Fermée', annulee: 'Annulée',
}

/** Mappe une offre backend + compatibilité → `Offer` du front. Le % vient du
 *  score d'évaluation réel (profil du compte vs attendus) ; le narratif absent
 *  côté backend est dérivé (description, périmètre, statut). */
export function mapOffre(o: OffreCompatOut): Offer {
  const pct = o.score_compat ?? 0
  const typeLabel = OFFRE_TYPE_LABEL[o.type] ?? 'Poste'
  const isPoste = o.type === 'offre_poste'
  const ligne = o.perimetre_bmci ?? poleLabel(o.departement_key)
  const statutLabel = OFFRE_STATUT_LABEL[o.statut] ?? o.statut
  const tone: PillTone = pct >= 85 ? 'new' : pct >= 70 ? 'ai' : 'mut'
  const adq = pct >= 85 ? 'Très adapté' : pct >= 70 ? 'Adapté' : 'À explorer'
  const infos: MetaItem[] = [
    { icon: 'pin', label: `Périmètre · ${ligne}` },
    { icon: 'brief', label: `Statut · ${statutLabel}` },
  ]
  return {
    key: String(o.id),
    type: typeLabel,
    tone,
    pct,
    adq,
    ligne,
    title: o.titre,
    sub: o.description ?? `${typeLabel} · ${ligne}`,
    meta: [{ icon: 'pin', label: ligne }, { icon: 'brief', label: statutLabel }],
    managerInformed: !isPoste,
    managerName: isPoste ? undefined : 'votre manager direct',
    ctx: ligne,
    missionTitle: isPoste ? 'Le poste' : 'La mission',
    mission: o.description ? [o.description] : [`${typeLabel} au sein de ${ligne}.`],
    skills: o.competences ?? [],
    infos,
    noteIcon: isPoste ? 'shield' : 'bell',
    noteText: isPoste
      ? "Candidature confidentielle : pour un poste, votre manager n'est pas informé."
      : 'Votre manager direct sera informé de votre candidature à cette opportunité.',
    noteOk: isPoste,
    cta: 'Postuler',
    ctaDetail: isPoste ? 'Postuler à ce poste' : 'Postuler à cette opportunité',
    fitTitle: `${pct} % de compatibilité`,
    fitText: `${o.couvertes} compétence(s) couverte(s) · ${o.ecarts} à développer`,
    tpill: null,
  }
}

/* -------------------------------------------------------------- Candidatures */
export interface CandidatureMineOut {
  id: number; statut: string; score: number | null; created_at: string
  offre_titre: string; offre_type: string
}

const CAND_STATUT: Record<string, CandidatureStatus> = {
  deposee: 'Envoyée', en_evaluation: 'En revue', retenue: 'Retenue',
  rejetee: 'Refusée', retiree: 'Refusée',
}
const CAND_TONE: Record<CandidatureStatus, PillTone> = {
  'Envoyée': 'mut', 'En revue': 'ai', 'Entretien planifié': 'new',
  'Refusée': 'warn', 'Retenue': 'ok',
}

function frDate(iso: string): string {
  const d = new Date(iso)
  return isNaN(d.getTime()) ? iso : d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })
}

/** Mappe « ma candidature » backend (candidature + offre jointe) → `Candidature`. */
export function mapCandidature(c: CandidatureMineOut): Candidature {
  const status = CAND_STATUT[c.statut] ?? 'Envoyée'
  return {
    icon: 'brief',
    title: c.offre_titre,
    type: OFFRE_TYPE_LABEL[c.offre_type] ?? 'Poste',
    date: frDate(c.created_at),
    status,
    tone: CAND_TONE[status],
  }
}

/** Mappe un profil backend vers un `TeamMember` (équipe du manager). Les champs
 *  d'évaluation (séniorité, note, dernier entretien, evals) prennent un repli
 *  neutre — pas encore portés par le backend. */
export function mapTeamMember(p: ProfilOut): TeamMember {
  const name = `${p.prenom ?? ''} ${p.nom}`.trim()
  const comps = p.competences ?? []
  const niveaux = comps.map((c) => c.niveau).filter((n): n is number => n != null)
  const moy = niveaux.length ? niveaux.reduce((a, b) => a + b, 0) / niveaux.length : 3
  return {
    id: String(p.id),
    initials: initialsOf(name),
    name,
    role: p.poste_actuel ?? '—',
    seniority: '—',
    ring: Math.round(moy * 20),
    evalScore: '—',
    lastEntretien: '—',
    skills: comps.slice(0, 6).map((c) => ({ label: c.skill_label_fr || c.libelle, pct: Math.min(100, (c.niveau ?? 3) * 20) })),
    strengths: comps.filter((c) => (c.niveau ?? 0) >= 4).slice(0, 3).map((c) => c.skill_label_fr || c.libelle),
    gaps: [],
    aspiration: p.aspirations ?? '',
    aspirationHorizon: '',
    evals: [],
    flag: null,
  }
}
