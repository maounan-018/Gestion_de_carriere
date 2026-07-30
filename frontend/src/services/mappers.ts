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
  RecoData, RecoSkill, Passerelle, MobiliteItem,
} from '@/types/domain'
import type { SouhaitRecu, KpiCard, TeamSkill, TeamMember, Vacancy, VacancyReco } from '@/types/manager'
import type { RhKpi, RhAlert, HautPotentiel, VeilleType, RhPerson, CartoMatrix, FamilleTension, TensionLevel } from '@/types/rh'
import type { RhOffer, RhCandidate } from '@/data/rh'

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
    id: String(s.id),
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

/* --------------------------------------------------------- Recommandation IA */
export interface EtapeFormationOut {
  competence: string; importance: string | null; type: string | null
  niveau_sfia: number | null; description: string | null; sous_competences: string[]
}
export interface PasserelleOut { metier: string; source: string; pertinence: number }
export interface RecommendationOut {
  poste_vise: string | null; score_actuel: number
  modele_extraction: string; modele_conseil: string
  competences_a_developper: EtapeFormationOut[]
  passerelles_metiers: PasserelleOut[]
  plan_developpement: string
}

const RECO_ICON: Record<string, IconKey> = {
  metier: 'brief', comportementale: 'user', transversale: 'route', outil_technologie: 'bolt',
  competence: 'grid', connaissance: 'book',
}

/** Mappe la recommandation backend (IA : extraction + reranker + conseil) → `RecoData`. */
export function mapReco(r: RecommendationOut): RecoData {
  const skills: RecoSkill[] = r.competences_a_developper.map((e) => {
    const critical = (e.importance ?? '').toLowerCase().startsWith('essent')
    const desc = e.description
      || (e.sous_competences.length ? 'Étapes : ' + e.sous_competences.slice(0, 3).join(' · ') : '')
    return {
      icon: RECO_ICON[e.type ?? ''] ?? 'spark',
      title: e.competence,
      desc,
      tag: e.niveau_sfia ? `Niveau SFIA ${e.niveau_sfia}` : (e.type ?? 'compétence'),
      critical,
    }
  })
  const passerelles: Passerelle[] = r.passerelles_metiers.map((p) => {
    const pct = Math.round(p.pertinence * 100)
    return {
      title: p.metier,
      pct,
      label: pct >= 75 ? 'Forte affinité' : pct >= 55 ? 'Bonne affinité' : 'Affinité modérée',
      source: p.source,
      tone: pct >= 75 ? 'new' : pct >= 55 ? 'ai' : 'mut',
    }
  })
  return {
    posteVise: r.poste_vise ?? 'Votre poste visé',
    pct: r.score_actuel,
    skills,
    passerelles,
    plan: r.plan_developpement || 'Plan de développement personnalisé en cours.',
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

/* ===================================================================== */
/*  Offres RH + revue des candidatures                                   */
/* ===================================================================== */
export interface RhOffreOut {
  id: number; titre: string; type: string; departement_key: string | null
  perimetre_bmci: string | null; statut: string
  candidats_total: number; candidats_compatibles: number; retenu_nom: string | null
}
export interface OffreCandidatOut {
  profil_id: number; candidature_id: number; nom: string; prenom: string | null
  poste_actuel: string | null; departement_key: string | null
  score: number | null; statut: string; couvertes: string[]; ecarts: string[]
}

const RH_OFFRE_STATUT: Record<string, RhOffer['status']> = {
  brouillon: 'brouillon', ouverte: 'ouvert', pourvue: 'clôturé', fermee: 'clôturé', annulee: 'clôturé',
}
const REVUE_STATUT: Record<string, RhCandidate['status']> = {
  deposee: 'nouveau', en_evaluation: 'preselection', retenue: 'retenu', rejetee: 'ecarte', retiree: 'ecarte',
}

export function mapRhOffre(o: RhOffreOut): RhOffer {
  return {
    key: String(o.id),
    title: o.titre,
    type: OFFRE_TYPE_LABEL[o.type] ?? 'Poste',
    ligne: o.perimetre_bmci ?? poleLabel(o.departement_key),
    status: RH_OFFRE_STATUT[o.statut] ?? 'ouvert',
    candidates: o.candidats_total,
    compatible: o.candidats_compatibles,
    retenu: o.retenu_nom ?? undefined,
  }
}

export function mapRhCandidate(c: OffreCandidatOut): RhCandidate {
  const name = `${c.prenom ?? ''} ${c.nom}`.trim()
  return {
    personId: String(c.profil_id),
    candidatureId: String(c.candidature_id),
    name,
    initials: initialsOf(name),
    role: c.poste_actuel ?? '—',
    pole: poleLabel(c.departement_key),
    score: Math.round(c.score ?? 0),
    matched: c.couvertes ?? [],
    gaps: c.ecarts ?? [],
    status: REVUE_STATUT[c.statut] ?? 'nouveau',
  }
}

/* ===================================================================== */
/*  Postes à pourvoir de l'équipe + reco de profils internes (inverse)   */
/* ===================================================================== */
export interface VacancyRecoOut {
  profil_id: number; nom: string; prenom: string | null; poste_actuel: string | null
  score: number; matched: string[]; gaps: string[]
}
export interface VacancyOut {
  id: number; titre: string; type: string; departement_key: string | null
  perimetre_bmci: string | null; description: string | null; statut: string
  created_at: string; recos: VacancyRecoOut[]
}

const VAC_STATUT: Record<string, Vacancy['status']> = {
  brouillon: 'brouillon', ouverte: 'ouvert', pourvue: 'clôturé', fermee: 'clôturé', annulee: 'clôturé',
}

function recoLabelTone(score: number): { label: string; tone: PillTone } {
  if (score >= 70) return { label: 'Forte adéquation', tone: 'new' }
  if (score >= 40) return { label: 'Bonne adéquation', tone: 'ai' }
  return { label: 'À explorer', tone: 'mut' }
}

export function mapVacancyReco(r: VacancyRecoOut): VacancyReco {
  const { label, tone } = recoLabelTone(r.score)
  const why = r.matched.length
    ? `Points forts : ${r.matched.slice(0, 3).join(', ')}`
    : 'Profil à faire monter en compétence sur ce poste.'
  return { memberId: String(r.profil_id), score: Math.round(r.score), label, tone, why }
}

export function mapVacancy(v: VacancyOut): Vacancy {
  const type = OFFRE_TYPE_LABEL[v.type] ?? 'Poste'
  const ligne = v.perimetre_bmci ?? poleLabel(v.departement_key)
  return {
    key: String(v.id),
    title: v.titre,
    type,
    ligne,
    sub: v.description ?? `${type} · ${ligne}`,
    openSince: `Ouvert ${relativeTime(v.created_at)}`,
    status: VAC_STATUT[v.statut] ?? 'ouvert',
    recos: v.recos.map(mapVacancyReco),
  }
}

/* ===================================================================== */
/*  Cartographie — matrice data-driven (pôles × familles)                */
/* ===================================================================== */
export interface CartoMatrixOut {
  familles: string[]
  lignes: {
    departement_key: string; label: string; effectif: number
    niveau_moyen: number | null; niveaux: (number | null)[]; people: string[]
  }[]
}

const FAMILLE_LABEL: Record<string, string> = {
  metier: 'Métier', comportementale: 'Comportementale', transversale: 'Transversale',
  outil_technologie: 'Outils & Tech', leadership: 'Leadership', data: 'Data & Analyse',
}
function humanizeFamille(k: string): string {
  return FAMILLE_LABEL[k] ?? k.charAt(0).toUpperCase() + k.slice(1)
}

export function mapCartoMatrix(m: CartoMatrixOut): CartoMatrix {
  return {
    familles: m.familles.map(humanizeFamille),
    lignes: m.lignes.map((l) => ({
      departementKey: l.departement_key,
      label: l.label,
      effectif: l.effectif,
      niveauMoyen: l.niveau_moyen,
      niveaux: l.niveaux,
      people: l.people ?? [],
    })),
  }
}

/* --------------------------------------------------- Familles & tensions */
export interface FamilleOut {
  famille: string
  detenues: number
  profils_couverts: number
  niveau_moyen: number | null
  demande: number
  tension: string
}

export function mapFamille(f: FamilleOut): FamilleTension {
  const tension: TensionLevel =
    f.tension === 'forte' || f.tension === 'moyenne' ? f.tension : 'faible'
  return {
    famille: humanizeFamille(f.famille),
    detenues: f.detenues,
    profilsCouverts: f.profils_couverts,
    niveauMoyen: f.niveau_moyen,
    demande: f.demande,
    tension,
  }
}

/* ------------------------------------------------------- Mobilité (passerelles) */
export interface MobiliteOut {
  occupation_id: number
  metier: string
  source: string
  competences_partagees: number
}

const SOURCE_LABEL: Record<string, string> = { esco: 'ESCO', onet: 'O*NET', sfia: 'SFIA' }

export function mapMobilite(m: MobiliteOut): MobiliteItem {
  return {
    id: m.occupation_id,
    metier: m.metier,
    source: SOURCE_LABEL[(m.source ?? '').toLowerCase()] ?? m.source,
    partagees: m.competences_partagees,
  }
}
