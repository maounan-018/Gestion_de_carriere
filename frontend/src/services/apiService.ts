import { OFFERS } from '@/data/offers'
import { CANDIDATURES } from '@/data/candidatures'
import { NOTIFICATIONS } from '@/data/notifications'
import { COLLAB_PROFILE } from '@/data/profile'
import { SOUHAITS } from '@/data/souhaits'
import { RECO } from '@/data/reco'
import { FORMATIONS } from '@/data/formations'
import { COLLEAGUES } from '@/data/colleagues'
import { TEAM, VACANCIES, SOUHAITS_RECUS } from '@/data/team'
import {
  MANAGER_PROFILE, MANAGER_RECO, MANAGER_OFFERS, MANAGER_NOTIFICATIONS, MANAGER_KPIS,
} from '@/data/manager'
import type { TeamMember, Vacancy, SouhaitRecu, KpiCard } from '@/types/manager'
import {
  RH_PEOPLE, CARTO_POLES, CARTO_SKILLS, RH_KPIS, RH_ALERTS, HAUTS_POTENTIELS, VEILLE, RH_OFFERS, RH_NOTIFICATIONS, NADIA_PROFILE,
} from '@/data/rh'
import type { RhOffer } from '@/data/rh'
import type { RhPerson, CartoMatrix, RhKpi, RhAlert, HautPotentiel, VeilleType, FamilleTension, SyntheseRh, FicheListItem, FicheDetail, EntretienCas } from '@/types/rh'
import type {
  Offer, Candidature, NotificationItem, CollabProfile, ProfilEditable, MyCvStatus,
  Souhait, RecoData, Formation, Colleague, Role, ChatMessage, MobiliteItem,
} from '@/types/domain'
import type { GabaritDoc, CartoDoc, FicheGeneree } from '@/types/referentiel'
import { apiFetch, apiUpload, getCsrf, ApiError } from './http'
import { formatCoachReply } from './coachFormat'
import { useSessionStore } from '@/stores/session'
import {
  mapNotification, mapFormation, mapSouhait, mapSouhaitRecu, mapKpi, mapKpiCard,
  mapHautPotentiel, mapVeille, mapAlerte, mapCollabProfile, mapProfil, mapTeamMember, mapColleague,
  mapOffre, mapCandidature, mapRhOffre, mapRhCandidate, mapVacancy, mapCartoMatrix, mapReco,
  mapMobilite, mapFamille, mapSyntheseRh,
  type MobiliteOut, type FamilleOut, type SyntheseRhOut,
  type NotificationOut, type FormationOut, type SouhaitOut, type SouhaitRecuOut,
  type KpiItemOut, type HautPotentielOut, type VeilleOut, type AlerteOut,
  type ProfilCarriereOut, type ProfilOut, type AnnuaireOut, type OffreCompatOut,
  type CandidatureMineOut, type RhOffreOut, type OffreCandidatOut, type VacancyOut,
  type RecommendationOut, type CartoMatrixOut,
} from './mappers'

/**
 * Couche d'accès aux données — bascule MOCK → LIVE, domaine par domaine.
 * Même signature stable pour les vues ; chaque méthode renvoie les types front.
 * - LIVE (défaut) : appelle `/api/*` puis mappe les schémas backend vers les types front.
 * - MOCK : renvoie les fixtures (forcé via `VITE_API_MODE=mock`), utile hors backend.
 * Les méthodes non encore basculées restent en mock quel que soit le mode.
 */
const MODE: 'mock' | 'live' = import.meta.env.VITE_API_MODE === 'mock' ? 'mock' : 'live'
const delay = (ms = 260): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms))

/** Rôle courant (pour la résolution des routes de notification). */
const currentRole = (): Role => useSessionStore().role ?? 'collab'

const stripHtml = (s: string): string => s.replace(/<[^>]*>/g, '')

/** Événements du flux SSE du Coach (voir backend `chat_agent_stream`). */
type CoachStreamEvent =
  | { type: 'token'; text: string }
  | { type: 'tool'; name: string }
  | { type: 'reset' }
  | { type: 'done'; model: string; outils?: string[] }

/** Callbacks de consommation du flux Coach (tous optionnels). */
export interface CoachStreamHandlers {
  onToken?: (text: string) => void
  onTool?: (name: string) => void
  onReset?: () => void
  onDone?: (info: { model: string; outils: string[] }) => void
}

/** Options d'un tour de conversation coach. Vide/omis = coach carrière (défaut).
 *  Les modes `entretien_*` activent le rôle NATIF backend (system prompt dédié). */
export interface CoachTurnOpts {
  mode?: 'carriere' | 'entretien_copilote' | 'entretien_roleplay' | 'entretien_copilote_equipe'
  section?: string
  focus?: string
  ouverture?: boolean
  sujet?: { nom: string; poste?: string; aspiration?: string; ecarts?: string[]; pole?: string }
}

/** Reco en mode ASYNCHRONE : lance le job puis interroge jusqu'à complétion.
 *  Requêtes courtes (plus de HTTP tenu ~85 s) → robuste aux timeouts proxy ;
 *  le cache backend rend un job déjà calculé quasi instantané. */
async function fetchRecoLive(): Promise<RecoData> {
  const { job_id } = await apiFetch<{ job_id: string }>('/competences/ma-reco/async', {
    method: 'POST',
  })
  for (let i = 0; i < 90; i++) {
    // ~90 × 2 s = 3 min de marge (le 1er calcul froid dure ~85 s).
    await delay(2000)
    const s = await apiFetch<{ status: string; result?: RecommendationOut; error?: string }>(
      `/competences/ma-reco/jobs/${job_id}`,
    )
    if (s.status === 'done' && s.result) return mapReco(s.result)
    if (s.status === 'error') throw new Error(s.error || 'Échec de la recommandation.')
  }
  throw new Error('La recommandation a expiré (délai dépassé).')
}

/** Passerelles de mobilité (mock hors backend). */
const MOBILITE_MOCK: MobiliteItem[] = [
  { id: 1, metier: 'Chargé de clientèle patrimoniale', source: 'ESCO', partagees: 6 },
  { id: 2, metier: 'Analyste crédit corporate', source: 'ESCO', partagees: 5 },
  { id: 3, metier: 'Conseiller en investissements financiers', source: 'O*NET', partagees: 4 },
]

/** Synthèse RH consolidée (mock hors backend). */
const SYNTHESE_MOCK: SyntheseRh = {
  effectif: 14,
  parPole: [
    { pole: 'Risques', effectif: 5 },
    { pole: 'Corporate Banking', effectif: 4 },
    { pole: 'Retail Banking', effectif: 3 },
    { pole: 'Ressources Humaines', effectif: 2 },
  ],
  candidaturesParStatut: [
    { statut: 'deposee', nombre: 5 },
    { statut: 'en_evaluation', nombre: 2 },
    { statut: 'retenue', nombre: 2 },
  ],
  famillesEnTension: 1,
}

/** Tensions par famille de compétences (mock hors backend). */
const FAMILLES_MOCK: FamilleTension[] = [
  { famille: 'Métier', detenues: 62, profilsCouverts: 25, niveauMoyen: 3.4, demande: 30, tension: 'forte' },
  { famille: 'Comportementale', detenues: 40, profilsCouverts: 12, niveauMoyen: 3.1, demande: 12, tension: 'moyenne' },
  { famille: 'Outils & Tech', detenues: 18, profilsCouverts: 8, niveauMoyen: 2.8, demande: 2, tension: 'faible' },
]

/** Départements + plan de succession (mocks hors backend). */
const DEPTS_MOCK: { key: string; nom: string }[] = [
  { key: 'risques', nom: 'Risques' },
  { key: 'corporate_banking', nom: 'Corporate Banking' },
  { key: 'ressources_humaines', nom: 'Ressources Humaines' },
]
const SUCCESSION_MOCK = {
  effectif: 8,
  plan:
    'PLAN DE SUCCESSION — synthèse (démonstration)\n\n' +
    '1. Rôles clés et successeurs internes potentiels : le poste de Directeur de pôle a 2 successeurs pressentis.\n' +
    '2. Préparation : 1 prêt à 12 mois, 1 à développer sur 24 mois.\n' +
    '3. Écarts à combler : management d’équipe, pilotage budgétaire.\n' +
    '4. Risques : 1 poste critique sans relève identifiée — vivier à constituer.',
  model: 'mock',
}

/** Référentiels éditables (mocks hors backend). */
const GABARIT_MOCK: GabaritDoc = {
  version: 1,
  sections: [
    { key: 'intitule_poste', label: 'Intitulé du poste', kind: 'metadata' },
    { key: 'mission', label: 'Mission', kind: 'freetext', categorie: 'metier' },
    { key: 'competences_metiers', label: 'Compétences métiers', kind: 'skill_list', categorie: 'metier' },
    { key: 'langues', label: 'Langues', kind: 'languages' },
  ],
}
const CARTO_MOCK: CartoDoc = {
  version: 2,
  departements: [
    { key: 'risques', nom: 'Risques', pole: 'Fonctions support', metiers: ['Analyste risques', 'Credit officer'] },
    { key: 'corporate_banking', nom: 'Corporate Banking', pole: 'Lignes métiers commerciales', metiers: ["Chargé d'affaires entreprises"] },
  ],
}

export const apiService = {
  async getOffers(): Promise<Offer[]> {
    if (MODE === 'mock') {
      await delay()
      return OFFERS
    }
    const rows = await apiFetch<OffreCompatOut[]>('/offres/compatibles')
    return rows.map(mapOffre)
  },
  async getOffer(key: string): Promise<Offer | undefined> {
    if (MODE === 'mock') {
      await delay(160)
      return OFFERS.find((o) => o.key === key)
    }
    const rows = await apiFetch<OffreCompatOut[]>('/offres/compatibles')
    return rows.map(mapOffre).find((o) => o.key === key)
  },
  async getCandidatures(): Promise<Candidature[]> {
    if (MODE === 'mock') {
      await delay()
      return CANDIDATURES
    }
    const rows = await apiFetch<CandidatureMineOut[]>('/candidatures/mes')
    return rows.map(mapCandidature)
  },
  /** Retire une de mes candidatures (statut → « retiree »). Réservé au candidat. */
  async retirerCandidature(id: string): Promise<void> {
    if (MODE === 'mock') {
      await delay()
      return
    }
    await apiFetch(`/candidatures/${id}/retrait`, { method: 'PATCH' })
  },
  async getNotifications(): Promise<NotificationItem[]> {
    if (MODE === 'mock') {
      await delay(200)
      return NOTIFICATIONS
    }
    const rows = await apiFetch<NotificationOut[]>('/notifications')
    const role = currentRole()
    return rows.map((n) => mapNotification(n, role))
  },
  async getCollabProfile(): Promise<CollabProfile> {
    if (MODE === 'mock') {
      await delay()
      return COLLAB_PROFILE
    }
    return mapCollabProfile(await apiFetch<ProfilCarriereOut>('/profils/me/carriere'))
  },
  /** Passerelles de mobilité du collaborateur connecté (métiers proches de ses
   *  compétences détenues ancrées). Résout le profil via /profils/me/carriere. */
  async getMyMobilite(): Promise<MobiliteItem[]> {
    if (MODE === 'mock') {
      await delay(200)
      return MOBILITE_MOCK
    }
    const me = await apiFetch<ProfilCarriereOut>('/profils/me/carriere')
    const rows = await apiFetch<MobiliteOut[]>(`/profils/${me.profil_id}/mobilite`)
    return rows.map(mapMobilite)
  },
  async getSouhaits(): Promise<Souhait[]> {
    if (MODE === 'mock') {
      await delay()
      return SOUHAITS
    }
    const rows = await apiFetch<SouhaitOut[]>('/souhaits')
    return rows.map(mapSouhait)
  },
  /** Crée un souhait d'évolution (option `pushed` : le pousser aussitôt au manager). */
  async createSouhait(input: {
    titre: string; kind?: 'carriere' | 'mission'; horizon?: string; description?: string; pushed?: boolean
  }): Promise<Souhait> {
    if (MODE === 'mock') {
      await delay()
      return {
        id: `mock-${Date.now()}`, title: input.titre, horizon: input.horizon || '—',
        desc: input.description || '', status: input.pushed ? 'Transmise au manager' : 'Brouillon',
        tone: input.pushed ? 'ai' : 'mut', pushed: !!input.pushed,
      }
    }
    return mapSouhait(await apiFetch<SouhaitOut>('/souhaits', { method: 'POST', body: input }))
  },
  /** Édite un souhait existant (titre / horizon / description / type). */
  async updateSouhait(id: string, patch: {
    titre?: string; kind?: 'carriere' | 'mission'; horizon?: string; description?: string
  }): Promise<Souhait> {
    if (MODE === 'mock') {
      await delay()
      return {
        id, title: patch.titre || '', horizon: patch.horizon || '—',
        desc: patch.description || '', status: 'Brouillon', tone: 'mut', pushed: false,
      }
    }
    return mapSouhait(await apiFetch<SouhaitOut>(`/souhaits/${id}`, { method: 'PATCH', body: patch }))
  },
  /** Enrôlement (pré-auth) : infos RH DÉJÀ EN BASE pour un e-mail — l'inscription
   *  ACTIVE un compte pré-existant et pré-remplit poste/manager/département. */
  async annuairePreload(email: string): Promise<{
    found: boolean; nom?: string; prenom?: string
    poste_actuel?: string; departement?: string; manager_nom?: string
  }> {
    if (MODE === 'mock') {
      return {
        found: true, nom: 'El Amrani', prenom: 'Youssef',
        poste_actuel: 'Conseiller clientèle particuliers',
        departement: 'Retail Banking', manager_nom: 'Karim Naji',
      }
    }
    return apiFetch(`/auth/annuaire-preload?email=${encodeURIComponent(email)}`)
  },
  async getReco(): Promise<RecoData> {
    if (MODE === 'mock') {
      await delay()
      return RECO
    }
    // ⚠️ Ollama : extraction + reranker + conseil (peut prendre quelques secondes).
    return fetchRecoLive()
  },
  /** Outil de normalisation réutilisable : saisie libre bruitée → intitulé canonique
   *  + confiance (clair/ambigu/indisponible). Ex. valider un objectif au profil. */
  async normaliserCible(
    texte: string,
  ): Promise<{ intitule: string; confiance: 'clair' | 'ambigu' | 'indisponible'; model: string }> {
    if (MODE === 'mock') {
      await delay(300)
      return { intitule: texte.trim(), confiance: 'clair', model: 'mock' }
    }
    return apiFetch('/normalisation/cible', { method: 'POST', body: { texte } })
  },
  /** Coach Carrière : envoie un message (+ historique) et renvoie la réponse (HTML sûr). */
  async sendCoachMessage(message: string, history: ChatMessage[]): Promise<string> {
    if (MODE === 'mock') {
      await delay(600)
      return "D'après votre profil, un levier clé est de combler l'écart « Diriger une équipe » : mentorat + formation management. Voulez-vous un plan détaillé ?"
    }
    const hist = history
      .filter((m) => (m.text || '').trim())
      .map((m) => ({ role: m.from === 'me' ? 'user' : 'assistant', content: stripHtml(m.text) }))
    const r = await apiFetch<{ reply: string }>('/coach', {
      method: 'POST',
      body: { message, history: hist },
    })
    return formatCoachReply(r.reply)
  },
  /** Coach Carrière en STREAMING (SSE) : émet outils interrogés + tokens au fil
   *  de l'eau. Lit `/coach/stream` via `fetch` + reader (POST + cookie + CSRF ;
   *  `EventSource` ne gère ni en-tête ni corps). En mock : pseudo-stream local. */
  async streamCoachMessage(
    message: string,
    history: ChatMessage[],
    handlers: CoachStreamHandlers,
    opts: CoachTurnOpts = {},
  ): Promise<void> {
    if (MODE === 'mock') {
      const mock =
        "D'après votre profil, un levier clé est de combler l'écart « Diriger une équipe » : mentorat + formation management. Voulez-vous un plan détaillé ?"
      for (const chunk of mock.match(/\S+\s*/g) ?? []) {
        await delay(28)
        handlers.onToken?.(chunk)
      }
      handlers.onDone?.({ model: 'mock', outils: [] })
      return
    }

    const hist = history
      .filter((m) => (m.text || '').trim())
      .map((m) => ({ role: m.from === 'me' ? 'user' : 'assistant', content: stripHtml(m.text) }))

    const csrf = getCsrf()
    const res = await fetch('/api/coach/stream', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...(csrf ? { 'X-CSRF-Token': csrf } : {}),
      },
      body: JSON.stringify({ message, history: hist, ...opts }),
    })
    if (!res.ok || !res.body) {
      throw new ApiError(res.status, `Erreur ${res.status}`)
    }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    for (;;) {
      const { value, done } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      // Trames SSE séparées par une ligne vide ; on garde le reliquat partiel.
      const frames = buf.split('\n\n')
      buf = frames.pop() ?? ''
      for (const frame of frames) {
        const line = frame.split('\n').find((l) => l.startsWith('data:'))
        if (!line) continue
        let ev: CoachStreamEvent
        try {
          ev = JSON.parse(line.slice(5).trim())
        } catch {
          continue
        }
        if (ev.type === 'token') handlers.onToken?.(ev.text)
        else if (ev.type === 'tool') handlers.onTool?.(ev.name)
        else if (ev.type === 'reset') handlers.onReset?.()
        else if (ev.type === 'done') handlers.onDone?.({ model: ev.model, outils: ev.outils ?? [] })
      }
    }
  },
  /** Conserver la synthèse de MA préparation d'entretien (sortie IA persistée, upsert). */
  async enregistrerMaSynthese(synthese: string): Promise<{ enregistre_le: string } | null> {
    if (MODE === 'mock') { await delay(120); return { enregistre_le: new Date().toISOString() } }
    try {
      return await apiFetch<{ synthese: string; enregistre_le: string }>('/entretiens/ma-synthese', {
        method: 'PUT', body: { synthese },
      })
    } catch {
      return null // best-effort : ne bloque pas l'export PDF
    }
  },
  /** Relire la synthèse persistée de MA préparation d'entretien (null si aucune). */
  async chargerMaSynthese(): Promise<{ synthese: string; enregistre_le: string } | null> {
    if (MODE === 'mock') { await delay(100); return null }
    try {
      return await apiFetch<{ synthese: string; enregistre_le: string } | null>('/entretiens/ma-synthese')
    } catch {
      return null
    }
  },
  async getFormations(): Promise<Formation[]> {
    if (MODE === 'mock') {
      await delay()
      return FORMATIONS
    }
    const rows = await apiFetch<FormationOut[]>('/formations')
    return rows.map(mapFormation)
  },
  async getColleagues(): Promise<Colleague[]> {
    if (MODE === 'mock') {
      await delay()
      return COLLEAGUES
    }
    const rows = await apiFetch<AnnuaireOut[]>('/profils/annuaire?limit=500')
    return rows.map(mapColleague)
  },
  async getColleague(id: string): Promise<Colleague | undefined> {
    if (MODE === 'mock') {
      await delay(160)
      return COLLEAGUES.find((c) => c.id === id)
    }
    const rows = await apiFetch<AnnuaireOut[]>('/profils/annuaire?limit=500')
    return rows.map(mapColleague).find((c) => c.id === id)
  },

  // ---------------------------------------------------------------- Manager
  async getTeam(): Promise<TeamMember[]> {
    if (MODE === 'mock') {
      await delay()
      return TEAM
    }
    // Équipe = profils dont le manager est l'utilisateur connecté (id backend).
    const meId = useSessionStore().user?.id
    const rows = await apiFetch<ProfilOut[]>('/profils?limit=200')
    const mine = meId != null ? rows.filter((p) => String(p.manager_id) === String(meId)) : rows
    return mine.map(mapTeamMember)
  },
  async getTeamMember(id: string): Promise<TeamMember | undefined> {
    if (MODE === 'mock') {
      await delay(160)
      return TEAM.find((m) => m.id === id)
    }
    try {
      return mapTeamMember(await apiFetch<ProfilOut>(`/profils/${id}`))
    } catch {
      return undefined
    }
  },
  async getManagerProfile(): Promise<CollabProfile> {
    if (MODE === 'mock') {
      await delay()
      return MANAGER_PROFILE
    }
    return mapCollabProfile(await apiFetch<ProfilCarriereOut>('/profils/me/carriere'))
  },
  async getManagerReco(): Promise<RecoData> {
    if (MODE === 'mock') {
      await delay()
      return MANAGER_RECO
    }
    return fetchRecoLive()
  },
  async getManagerOffers(): Promise<Offer[]> {
    if (MODE === 'mock') {
      await delay()
      return MANAGER_OFFERS
    }
    const rows = await apiFetch<OffreCompatOut[]>('/offres/compatibles')
    return rows.map(mapOffre)
  },
  async getManagerOffer(key: string): Promise<Offer | undefined> {
    if (MODE === 'mock') {
      await delay(160)
      return MANAGER_OFFERS.find((o) => o.key === key)
    }
    const rows = await apiFetch<OffreCompatOut[]>('/offres/compatibles')
    return rows.map(mapOffre).find((o) => o.key === key)
  },
  async getVacancies(): Promise<Vacancy[]> {
    if (MODE === 'mock') {
      await delay()
      return VACANCIES
    }
    const rows = await apiFetch<VacancyOut[]>('/offres/vacances')
    return rows.map(mapVacancy)
  },
  async getVacancy(key: string): Promise<Vacancy | undefined> {
    if (MODE === 'mock') {
      await delay(160)
      return VACANCIES.find((v) => v.key === key)
    }
    const rows = await apiFetch<VacancyOut[]>('/offres/vacances')
    return rows.map(mapVacancy).find((v) => v.key === key)
  },
  async getSouhaitsRecus(): Promise<SouhaitRecu[]> {
    if (MODE === 'mock') {
      await delay()
      return SOUHAITS_RECUS
    }
    const rows = await apiFetch<SouhaitRecuOut[]>('/souhaits/recus')
    return rows.map(mapSouhaitRecu)
  },
  async getManagerNotifications(): Promise<NotificationItem[]> {
    if (MODE === 'mock') {
      await delay(200)
      return MANAGER_NOTIFICATIONS
    }
    const rows = await apiFetch<NotificationOut[]>('/notifications')
    const role = currentRole()
    return rows.map((n) => mapNotification(n, role))
  },
  async getManagerKpis(): Promise<KpiCard[]> {
    if (MODE === 'mock') {
      await delay(120)
      return MANAGER_KPIS
    }
    const res = await apiFetch<{ scope: string; kpis: KpiItemOut[] }>('/dashboards/kpis?scope=manager')
    return res.kpis.map(mapKpiCard)
  },

  // -------------------------------------------------------------------- RH
  async getRhPeople(): Promise<RhPerson[]> {
    if (MODE === 'mock') {
      await delay()
      return RH_PEOPLE
    }
    const rows = await apiFetch<ProfilOut[]>('/profils?limit=200')
    return rows.map(mapProfil)
  },
  async getRhPerson(id: string): Promise<RhPerson | undefined> {
    if (MODE === 'mock') {
      await delay(160)
      return RH_PEOPLE.find((p) => p.id === id)
    }
    try {
      return mapProfil(await apiFetch<ProfilOut>(`/profils/${id}`))
    } catch {
      return undefined
    }
  },
  async getCarto(): Promise<CartoMatrix> {
    if (MODE === 'mock') {
      await delay()
      return {
        familles: [...CARTO_SKILLS],
        lignes: CARTO_POLES.map((p) => ({
          departementKey: p.name, label: p.name, pole: p.pole ?? null, effectif: p.people.length,
          niveauMoyen: p.levels.length ? p.levels.reduce((a, b) => a + b, 0) / p.levels.length : null,
          niveaux: p.levels, people: p.people,
        })),
      }
    }
    return mapCartoMatrix(await apiFetch<CartoMatrixOut>('/dashboards/cartographie'))
  },
  /** Cartographie de MON équipe (lignes = collaborateurs), même nomenclature que la
   *  carto RH (familles). Pour l'écran « Mon équipe ». */
  async getTeamCarto(): Promise<CartoMatrix> {
    if (MODE === 'mock') {
      await delay()
      const familles = ['Métier', 'Comportementale', 'Transversale', 'Outils & tech.']
      const membres = [
        ['Youssef El Amrani', [3.5, 4, 3, 2]], ['Salma Idrissi', [4, 3, 3.5, 2.5]],
        ['Youssef Alaoui', [3, 3.5, 2.5, null]], ['Hicham Berrada', [2.5, 3, 3, 2]],
        ['Imane Cherkaoui', [4.5, 4, 4, 3]], ['Karim Sabri', [4, 3.5, 3.5, 3]],
      ] as [string, (number | null)[]][]
      return {
        familles,
        lignes: membres.map(([nom, niveaux]) => ({
          departementKey: nom, label: nom, pole: null, effectif: 1,
          niveauMoyen: (niveaux.filter((n): n is number => n != null).reduce((a, b) => a + b, 0)
            / Math.max(1, niveaux.filter((n) => n != null).length)),
          niveaux, people: [nom],
        })),
      }
    }
    return mapCartoMatrix(await apiFetch<CartoMatrixOut>('/dashboards/equipe/cartographie'))
  },
  /** Manager → RH : envoie un message (crée une notification par destinataire RH). */
  async communiquerRH(sujet: string, message: string): Promise<{ destinataires: number }> {
    if (MODE === 'mock') {
      await delay(400)
      return { destinataires: 1 }
    }
    return apiFetch('/notifications/message-rh', { method: 'POST', body: { sujet, message } })
  },
  /** RH/manager → collaborateur : notification ciblée. `delivered=false` si le profil
   *  n'a pas de compte actif (persona synthétique). */
  async messageProfil(
    profilId: string, sujet: string, message: string, toRoute?: string,
  ): Promise<{ delivered: boolean }> {
    if (MODE === 'mock') {
      await delay(300)
      return { delivered: true }
    }
    return apiFetch('/notifications/message-profil', {
      method: 'POST',
      body: { profil_id: Number(profilId), sujet, message, to_route: toRoute },
    })
  },
  /** Analyse stratégique RH par l'IA : synthèse des indicateurs consolidés de la
   *  plateforme (tensions, potentiels, rétention, qualité data). ⚠️ LLM local. */
  async lancerAnalyseRh(): Promise<{ synthese: string; model: string; genere_le: string }> {
    if (MODE === 'mock') {
      await delay(1200)
      return {
        synthese:
          '1. Constats clés — effectif bien cartographié ; quelques familles de compétences en tension.\n'
          + "2. Tensions — surveiller les compétences data et réglementaires.\n"
          + '3. Rétention — sécuriser les hauts potentiels et traiter les entretiens en retard.\n'
          + "4. Priorités — planifier les entretiens en retard, lancer des passerelles de mobilité.",
        model: 'mock', genere_le: new Date().toISOString(),
      }
    }
    return apiFetch('/rh/analyse', { method: 'POST' })
  },
  /** Dernière analyse HRBP PERSISTÉE (sans relancer le LLM) — présentation
   *  immédiate du tableau de bord ; `null` si aucune n'a encore été produite. */
  async getDerniereAnalyseRh(): Promise<{ synthese: string; model: string; genere_le: string } | null> {
    if (MODE === 'mock') return null
    return apiFetch('/rh/analyse/latest')
  },
  /** Synthèse RH consolidée (effectifs par pôle, pipeline candidatures, tensions). */
  async getSyntheseRh(): Promise<SyntheseRh> {
    if (MODE === 'mock') {
      await delay(120)
      return SYNTHESE_MOCK
    }
    return mapSyntheseRh(await apiFetch<SyntheseRhOut>('/dashboards/synthese'))
  },
  /** Tensions par famille de compétences (offre interne détenue vs demande des
   *  offres ouvertes). Complète la cartographie par pôle. */
  async getFamilles(): Promise<FamilleTension[]> {
    if (MODE === 'mock') {
      await delay()
      return FAMILLES_MOCK
    }
    const rows = await apiFetch<FamilleOut[]>('/dashboards/familles')
    return rows.map(mapFamille)
  },
  /** Enrichissement RH : ancre au graphe les compétences détenues non ancrées.
   *  ⚠️ Peut prendre ~1-2 min au 1er lancement (embeddings + reranker). */
  async ancrerCompetences(): Promise<{ examinees: number; ancrees: number; categorisees: number }> {
    if (MODE === 'mock') {
      await delay(1200)
      return { examinees: 45, ancrees: 39, categorisees: 6 }
    }
    return apiFetch('/profils/ancrer-competences', { method: 'POST' })
  },
  async getRhKpis(): Promise<RhKpi[]> {
    if (MODE === 'mock') {
      await delay(120)
      return RH_KPIS
    }
    const res = await apiFetch<{ scope: string; kpis: KpiItemOut[] }>('/dashboards/kpis?scope=rh')
    return res.kpis.map(mapKpi)
  },
  async getRhAlerts(): Promise<RhAlert[]> {
    if (MODE === 'mock') {
      await delay()
      return RH_ALERTS
    }
    const rows = await apiFetch<AlerteOut[]>('/rh/alertes')
    return rows.map(mapAlerte)
  },
  async getHautsPotentiels(): Promise<HautPotentiel[]> {
    if (MODE === 'mock') {
      await delay()
      return HAUTS_POTENTIELS
    }
    const rows = await apiFetch<HautPotentielOut[]>('/dashboards/hauts-potentiels')
    return rows.map(mapHautPotentiel)
  },
  /** Supervision qualité des données : scans RÉELS de la base (RH). Chaque item =
   *  un contrôle et le nombre d'anomalies détectées sur une population. */
  async getSupervision(): Promise<{ titre: string; found: number; total: number }[]> {
    if (MODE === 'mock') {
      await delay()
      return [
        { titre: 'Profils sans compétence renseignée', found: 2, total: 8 },
        { titre: 'Profils sans poste renseigné', found: 0, total: 8 },
        { titre: 'Profils sans aspiration exprimée', found: 4, total: 8 },
        { titre: 'Compétences non ancrées au graphe', found: 6, total: 48 },
        { titre: 'Compétences non catégorisées', found: 0, total: 48 },
      ]
    }
    return apiFetch('/dashboards/supervision')
  },
  async getVeille(): Promise<VeilleType[]> {
    if (MODE === 'mock') {
      await delay()
      return VEILLE
    }
    const rows = await apiFetch<VeilleOut[]>('/rh/veille')
    return rows.map(mapVeille)
  },
  /** Cas concrets d'entretiens à traiter (en retard / à planifier) avec collaborateur,
   *  manager responsable et ancienneté du dernier entretien. */
  async getEntretiensATraiter(): Promise<EntretienCas[]> {
    if (MODE === 'mock') {
      await delay(150)
      return []
    }
    const rows = await apiFetch<{
      profil_id: number; nom: string; prenom: string | null; poste_actuel: string | null
      departement_key: string | null; type: string; statut: string
      date_prevue: string | null; mois_depuis_dernier: number | null; manager_nom: string | null
    }[]>('/dashboards/entretiens/a-traiter')
    return rows.map((r) => ({
      profilId: r.profil_id, nom: r.nom, prenom: r.prenom, posteActuel: r.poste_actuel,
      departementKey: r.departement_key, type: r.type as 'annuel' | 'rh',
      statut: r.statut as 'en_retard' | 'planifie', datePrevue: r.date_prevue,
      moisDepuisDernier: r.mois_depuis_dernier, managerNom: r.manager_nom,
    }))
  },
  async getRhOffers(): Promise<RhOffer[]> {
    if (MODE === 'mock') {
      await delay()
      return RH_OFFERS
    }
    const rows = await apiFetch<RhOffreOut[]>('/offres/rh-liste')
    return rows.map(mapRhOffre)
  },
  async getRhOffer(key: string): Promise<RhOffer | undefined> {
    if (MODE === 'mock') {
      await delay(160)
      return RH_OFFERS.find((o) => o.key === key)
    }
    const rows = await apiFetch<RhOffreOut[]>('/offres/rh-liste')
    const offre = rows.map(mapRhOffre).find((o) => o.key === key)
    if (!offre) return undefined
    // Détail : joindre la liste nominative des candidats (score + couvertes/écarts).
    const cands = await apiFetch<OffreCandidatOut[]>(`/offres/${key}/candidats`)
    offre.candidateList = cands.map(mapRhCandidate)
    return offre
  },
  async getRhNotifications(): Promise<NotificationItem[]> {
    if (MODE === 'mock') {
      await delay(200)
      return RH_NOTIFICATIONS
    }
    const rows = await apiFetch<NotificationOut[]>('/notifications')
    const role = currentRole()
    return rows.map((n) => mapNotification(n, role))
  },
  async getRhProfile(): Promise<CollabProfile> {
    if (MODE === 'mock') {
      await delay()
      return NADIA_PROFILE
    }
    return mapCollabProfile(await apiFetch<ProfilCarriereOut>('/profils/me/carriere'))
  },
  /** Liste des départements (cartographie) — pour les sélecteurs RH. */
  async getDepartements(): Promise<{ key: string; nom: string }[]> {
    if (MODE === 'mock') {
      await delay(120)
      return DEPTS_MOCK
    }
    const rows = await apiFetch<{ key: string; nom: string }[]>('/fiches/departements')
    return rows.map((d) => ({ key: d.key, nom: d.nom }))
  },
  /** Générer une fiche de poste via IA (RH/ADMIN). ⚠️ Ollama : quelques secondes.
   *  Contenu SYNTHÉTIQUE (compétences inférées du graphe + rédaction FR). */
  async genererFiche(input: { metier: string; departementKey: string }): Promise<FicheGeneree> {
    if (MODE === 'mock') {
      await delay(400)
      return {
        metier: input.metier,
        departement: input.departementKey,
        synthetique: true,
        sections: {
          finalite: `Fiche de démonstration pour « ${input.metier} » (générée localement, mock).`,
          competences_requises: 'Compétences inférées du référentiel ESCO/O*NET/SFIA.',
        },
        competences_reference: ['Analyse', 'Communication', 'Rigueur'],
      }
    }
    return apiFetch<FicheGeneree>('/fiches/generation', {
      method: 'POST',
      body: { metier: input.metier, departement_key: input.departementKey },
    })
  },
  /** Plan de succession raisonné d'un département (RH). ⚠️ En live : IA de
   *  raisonnement lourde (qwen3.6, ~4 min) → mode ASYNCHRONE (job + polling),
   *  comme la reco : requêtes courtes, pas de HTTP tenu (timeout proxy) ni de
   *  verrou GPU maintenu pendant l'attente du client. */
  async getSuccession(departementKey: string): Promise<{ effectif: number; plan: string; model: string }> {
    if (MODE === 'mock') {
      await delay(800)
      return SUCCESSION_MOCK
    }
    const { job_id } = await apiFetch<{ job_id: string }>('/rh/succession/async', {
      method: 'POST',
      body: { departement_key: departementKey },
    })
    for (let i = 0; i < 180; i++) {
      // ~180 × 2 s = 6 min de marge (le raisonnement qwen3.6 dure ~4 min).
      await delay(2000)
      const s = await apiFetch<{
        status: string
        result?: { departement_key: string; effectif: number; plan: string; model: string }
        error?: string
      }>(`/rh/succession/jobs/${job_id}`)
      if (s.status === 'done' && s.result) {
        return { effectif: s.result.effectif, plan: s.result.plan, model: s.result.model }
      }
      if (s.status === 'error') throw new Error(s.error || 'Échec du plan de succession.')
    }
    throw new Error('Le plan de succession a expiré (délai dépassé).')
  },
  /** Gabarit de fiche (référentiel éditable). */
  async getGabarit(): Promise<GabaritDoc> {
    if (MODE === 'mock') {
      await delay(150)
      return structuredClone(GABARIT_MOCK)
    }
    return apiFetch<GabaritDoc>('/fiches/gabarit')
  },
  /** Enregistre le gabarit (RH/ADMIN). Rejette (ApiError 400) si invalide. */
  async saveGabarit(doc: GabaritDoc): Promise<GabaritDoc> {
    if (MODE === 'mock') {
      await delay(300)
      return doc
    }
    return apiFetch<GabaritDoc>('/fiches/gabarit', { method: 'PUT', body: doc })
  },
  /** Cartographie départements→métiers (référentiel éditable). */
  async getCartographie(): Promise<CartoDoc> {
    if (MODE === 'mock') {
      await delay(150)
      return structuredClone(CARTO_MOCK)
    }
    return apiFetch<CartoDoc>('/fiches/cartographie')
  },
  /** Enregistre la cartographie (RH/ADMIN). Rejette (ApiError 400) si invalide. */
  async saveCartographie(doc: CartoDoc): Promise<CartoDoc> {
    if (MODE === 'mock') {
      await delay(300)
      return doc
    }
    return apiFetch<CartoDoc>('/fiches/cartographie', { method: 'PUT', body: doc })
  },

  // ============================================================ Écritures
  /** Postuler à une offre (collab). `offerKey` = id backend (mapOffre). Le profil
   *  du candidat est résolu depuis la session (/profils/me/carriere). */
  async postuler(offerKey: string, motivation?: string): Promise<string> {
    if (MODE === 'mock') {
      await delay(220)
      return `mock-${Date.now()}`
    }
    const me = await apiFetch<ProfilCarriereOut>('/profils/me/carriere')
    const c = await apiFetch<{ id: number }>('/candidatures', {
      method: 'POST',
      body: { offre_id: Number(offerKey), profil_id: me.profil_id, motivation: motivation ?? null },
    })
    return String(c.id)
  },
  /** Téléverse le CV (PDF) à jour lié à une candidature (multipart). */
  async uploaderCandidatureCv(candidatureId: string, file: File): Promise<void> {
    if (MODE === 'mock') {
      await delay(300)
      return
    }
    const fd = new FormData()
    fd.append('fichier', file)
    await apiUpload(`/candidatures/${candidatureId}/cv`, fd)
  },
  /** Marquer une notification comme lue. */
  async markNotificationRead(id: string): Promise<void> {
    if (MODE === 'mock') {
      await delay(100)
      return
    }
    await apiFetch(`/notifications/${id}/lu`, { method: 'PATCH' })
  },
  /** Tout marquer lu. */
  async markAllNotificationsRead(): Promise<void> {
    if (MODE === 'mock') {
      await delay(120)
      return
    }
    await apiFetch('/notifications/lues', { method: 'POST' })
  },
  /** Décision humaine sur une candidature (RH/manager). Le score reste indicatif :
   *  un candidat < 100 % peut être retenu. */
  async decideCandidature(
    candidatureId: string,
    statut: 'retenue' | 'rejetee' | 'en_evaluation',
  ): Promise<void> {
    if (MODE === 'mock') {
      await delay(160)
      return
    }
    await apiFetch(`/candidatures/${candidatureId}/decision`, { method: 'PATCH', body: { statut } })
  },
  /** Recalculer le score d'une candidature (attendus de l'offre modifiés depuis
   *  le dépôt). Déterministe (sans Ollama). Renvoie le nouveau score arrondi. */
  async reevaluerCandidature(candidatureId: string): Promise<number> {
    if (MODE === 'mock') {
      await delay(200)
      return 0
    }
    const c = await apiFetch<{ score: number | null }>(
      `/candidatures/${candidatureId}/reevaluation`,
      { method: 'POST' },
    )
    return Math.round(c.score ?? 0)
  },
  /** Pousser un souhait existant à son manager (collab). */
  async pushSouhait(id: string): Promise<void> {
    if (MODE === 'mock') {
      await delay(160)
      return
    }
    await apiFetch(`/souhaits/${id}`, { method: 'PATCH', body: { pushed: true, statut: 'pousse' } })
  },
  /** Publier une offre (manager/RH). Part en brouillon → validation RH.
   *  Marquée `synthetique` (donnée de démo étiquetée). */
  async publishOffer(input: {
    titre: string
    type: 'Poste' | 'Mission transverse' | 'Projet innovation'
    ficheId?: number | null
    description?: string
    localisation?: string
    duree?: string
    /** Compétences canoniques attendues déclarées par le manager (ancrées si skill_id). */
    competences?: { libelle: string; skill_id?: number | null; importance?: 'essentielle' | 'souhaitee' }[]
  }): Promise<void> {
    if (MODE === 'mock') {
      await delay(220)
      return
    }
    const typeMap = {
      'Poste': 'offre_poste',
      'Mission transverse': 'mission',
      'Projet innovation': 'projet',
    } as const
    await apiFetch('/offres', {
      method: 'POST',
      body: {
        titre: input.titre, type: typeMap[input.type], statut: 'brouillon',
        fiche_id: input.ficheId ?? null,
        heriter_competences: !!input.ficheId,
        description: input.description || null,
        localisation: input.localisation || null,
        duree: input.duree || null,
        competences: (input.competences ?? []).map((c) => ({
          libelle: c.libelle,
          skill_id: c.skill_id ?? null,
          importance: c.importance ?? 'essentielle',
        })),
        synthetique: false,
      },
    })
  },
  /** Autocomplétion du référentiel de compétences CANONIQUES (déclaration d'attendus). */
  async rechercherCompetences(q: string): Promise<{ skill_id: number; label: string }[]> {
    if (MODE === 'mock') return []
    return apiFetch(`/competences/rechercher?q=${encodeURIComponent(q)}`)
  },
  /** Fiches de poste (sélecteur « Publier une offre »). Filtre optionnel sur l'intitulé. */
  async getFiches(q?: string): Promise<FicheListItem[]> {
    if (MODE === 'mock') {
      await delay(150)
      return []
    }
    const qs = q ? `?q=${encodeURIComponent(q)}` : ''
    return apiFetch<FicheListItem[]>(`/fiches${qs}`)
  },
  /** Détail d'une fiche de poste (mission, activités, compétences attendues). */
  async getFiche(id: number): Promise<FicheDetail> {
    return apiFetch<FicheDetail>(`/fiches/${id}`)
  },
  /** Transition de statut d'une offre (RH/manager). Les dates d'ouverture/clôture
   *  sont posées automatiquement côté serveur. `id` = id backend. */
  async updateOffreStatut(
    id: string,
    statut: 'brouillon' | 'ouverte' | 'pourvue' | 'fermee' | 'annulee',
  ): Promise<void> {
    if (MODE === 'mock') {
      await delay(200)
      return
    }
    await apiFetch(`/offres/${id}`, { method: 'PATCH', body: { statut } })
  },
  /** Éditer un profil (RH/ADMIN). `id` = profil_id backend. Champs éditables :
   *  poste actuel + aspirations. (Un collaborateur ne peut PAS éditer son propre
   *  profil : PATCH /profils/{id} est réservé RH/ADMIN — pas d'endpoint self-service.) */
  /** Éditer MON profil (collab, auto-service) : poste actuel + aspirations. */
  async updateMyProfil(patch: ProfilEditable): Promise<void> {
    if (MODE === 'mock') {
      await delay(200)
      return
    }
    await apiFetch('/profils/me', { method: 'PATCH', body: patch })
  },
  /** Valeurs auto-déclarées de MON profil, pour préremplir « Éditer mon profil »
   *  (indépendant du rôle : collab, manager, RH). null si le compte n'a pas de profil. */
  async getMyProfilEditable(): Promise<ProfilEditable | null> {
    if (MODE === 'mock') {
      await delay(150)
      return { poste_actuel: '', aspirations: '', bio: '', poste_vise: '', horizon: '',
        type_evolution: '', mobilite_geo: '', disponibilite: '' }
    }
    try {
      const c = await apiFetch<ProfilCarriereOut>('/profils/me/carriere')
      return {
        poste_actuel: c.poste_actuel ?? '', aspirations: c.aspirations ?? '',
        bio: c.bio ?? '', poste_vise: c.poste_vise ?? '', horizon: c.horizon ?? '',
        type_evolution: c.type_evolution ?? '', mobilite_geo: c.mobilite_geo ?? '',
        disponibilite: c.disponibilite ?? '',
      }
    } catch {
      return null
    }
  },
  async updateProfil(
    id: string,
    patch: { poste_actuel?: string; aspirations?: string },
  ): Promise<void> {
    if (MODE === 'mock') {
      await delay(200)
      return
    }
    await apiFetch(`/profils/${id}`, { method: 'PATCH', body: patch })
  },
  /** Extraire les compétences DÉMONTRÉES d'une évaluation (manager/RH) et les
   *  ajouter au profil (source=evaluation_mission|performance). Renvoie le nombre
   *  de compétences détectées pour ce type. ⚠️ Utilise Ollama en live. */
  async extraireEvaluation(
    profilId: string,
    texte: string,
    type: 'mission' | 'performance' = 'mission',
  ): Promise<number> {
    if (MODE === 'mock') {
      await delay(500)
      return 3
    }
    const p = await apiFetch<ProfilOut>(`/profils/${profilId}/extraction-evaluation`, {
      method: 'POST',
      body: { texte, type },
    })
    const src = type === 'mission' ? 'evaluation_mission' : 'evaluation_performance'
    return (p.competences ?? []).filter((c) => c.source === src).length
  },
  /** Évaluer une compétence détenue (manager/RH) sur une échelle 1-10. Score
   *  PERSISTÉ (source manager, poids prépondérant) → alimente le % d'acquisition. */
  async evaluerCompetence(profilId: string, competenceId: number, score: number,
                          commentaire?: string): Promise<void> {
    if (MODE === 'mock') { await delay(200); return }
    await apiFetch(`/profils/${profilId}/competences/${competenceId}/evaluation`, {
      method: 'POST', body: { score, commentaire },
    })
  },
  /** Self-service collab : extraire MES compétences détenues depuis mon CV et les
   *  ajouter à mon profil (source=cv, remplace les précédentes issues d'un CV).
   *  Résout mon profil via /profils/me/carriere. Renvoie le nb de compétences. */
  async extraireMonCv(texte: string): Promise<number> {
    if (MODE === 'mock') {
      await delay(500)
      return 4
    }
    const me = await apiFetch<ProfilCarriereOut>('/profils/me/carriere')
    const p = await apiFetch<ProfilOut>(`/profils/${me.profil_id}/extraction-cv`, {
      method: 'POST',
      body: { texte, remplacer: true },
    })
    return (p.competences ?? []).filter((c) => c.source === 'cv').length
  },
  /** Statut du CV conservé de MON profil (présence + horodatage + id pour le lien). */
  async getMyCvStatus(): Promise<MyCvStatus | null> {
    if (MODE === 'mock') {
      await delay(120)
      return { profilId: 1, filename: null, uploadedAt: null }
    }
    try {
      const c = await apiFetch<ProfilCarriereOut>('/profils/me/carriere')
      return { profilId: c.profil_id, filename: c.cv_filename ?? null, uploadedAt: c.cv_uploaded_at ?? null }
    } catch {
      return null
    }
  },
  /** Téléverser / remplacer MON CV (PDF, conservé côté serveur). Renvoie le statut à jour. */
  async uploaderMonCv(file: File): Promise<MyCvStatus> {
    const fd = new FormData()
    fd.append('fichier', file)
    const c = await apiUpload<ProfilCarriereOut>('/profils/me/cv', fd)
    return { profilId: c.profil_id, filename: c.cv_filename ?? null, uploadedAt: c.cv_uploaded_at ?? null }
  },
  /** URL de téléchargement du CV d'un profil (même origine via proxy ; cookies inclus
   *  par la navigation). Le backend applique l'ownership (propriétaire / manager / RH). */
  cvUrl(profilId: number): string {
    return `/api/profils/${profilId}/cv`
  },
}
