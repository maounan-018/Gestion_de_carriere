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
  RH_PEOPLE, CARTO_POLES, RH_KPIS, RH_ALERTS, HAUTS_POTENTIELS, VEILLE, RH_OFFERS, RH_NOTIFICATIONS, NADIA_PROFILE,
} from '@/data/rh'
import type { RhOffer } from '@/data/rh'
import type { RhPerson, CartoPole, RhKpi, RhAlert, HautPotentiel, VeilleType } from '@/types/rh'
import type {
  Offer, Candidature, NotificationItem, CollabProfile,
  Souhait, RecoData, Formation, Colleague, Role,
} from '@/types/domain'
import { apiFetch } from './http'
import { useSessionStore } from '@/stores/session'
import {
  mapNotification, mapFormation, mapSouhait, mapSouhaitRecu, mapKpi, mapKpiCard,
  mapHautPotentiel, mapVeille, mapAlerte, mapCollabProfile, mapProfil, mapTeamMember, mapColleague,
  mapOffre,
  type NotificationOut, type FormationOut, type SouhaitOut, type SouhaitRecuOut,
  type KpiItemOut, type HautPotentielOut, type VeilleOut, type AlerteOut,
  type ProfilCarriereOut, type ProfilOut, type AnnuaireOut, type OffreCompatOut,
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
    await delay()
    return CANDIDATURES
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
  async getSouhaits(): Promise<Souhait[]> {
    if (MODE === 'mock') {
      await delay()
      return SOUHAITS
    }
    const rows = await apiFetch<SouhaitOut[]>('/souhaits')
    return rows.map(mapSouhait)
  },
  async getReco(): Promise<RecoData> {
    await delay()
    return RECO
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
    const rows = await apiFetch<AnnuaireOut[]>('/profils/annuaire')
    return rows.map(mapColleague)
  },
  async getColleague(id: string): Promise<Colleague | undefined> {
    if (MODE === 'mock') {
      await delay(160)
      return COLLEAGUES.find((c) => c.id === id)
    }
    const rows = await apiFetch<AnnuaireOut[]>('/profils/annuaire')
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
    await delay()
    return MANAGER_RECO
  },
  async getManagerOffers(): Promise<Offer[]> {
    await delay()
    return MANAGER_OFFERS
  },
  async getManagerOffer(key: string): Promise<Offer | undefined> {
    await delay(160)
    return MANAGER_OFFERS.find((o) => o.key === key)
  },
  async getVacancies(): Promise<Vacancy[]> {
    await delay()
    return VACANCIES
  },
  async getVacancy(key: string): Promise<Vacancy | undefined> {
    await delay(160)
    return VACANCIES.find((v) => v.key === key)
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
  async getCarto(): Promise<CartoPole[]> {
    await delay()
    return CARTO_POLES
  },
  async getCartoPole(name: string): Promise<CartoPole | undefined> {
    await delay(160)
    return CARTO_POLES.find((p) => p.name === name)
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
  async getVeille(): Promise<VeilleType[]> {
    if (MODE === 'mock') {
      await delay()
      return VEILLE
    }
    const rows = await apiFetch<VeilleOut[]>('/rh/veille')
    return rows.map(mapVeille)
  },
  async getRhOffers(): Promise<RhOffer[]> {
    await delay()
    return RH_OFFERS
  },
  async getRhOffer(key: string): Promise<RhOffer | undefined> {
    await delay(160)
    return RH_OFFERS.find((o) => o.key === key)
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
}
