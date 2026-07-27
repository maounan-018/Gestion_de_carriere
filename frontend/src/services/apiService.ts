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
  mapNotification, mapFormation,
  type NotificationOut, type FormationOut,
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
    await delay()
    return OFFERS
  },
  async getOffer(key: string): Promise<Offer | undefined> {
    await delay(160)
    return OFFERS.find((o) => o.key === key)
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
    await delay()
    return COLLAB_PROFILE
  },
  async getSouhaits(): Promise<Souhait[]> {
    await delay()
    return SOUHAITS
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
    await delay()
    return COLLEAGUES
  },
  async getColleague(id: string): Promise<Colleague | undefined> {
    await delay(160)
    return COLLEAGUES.find((c) => c.id === id)
  },

  // ---------------------------------------------------------------- Manager
  async getTeam(): Promise<TeamMember[]> {
    await delay()
    return TEAM
  },
  async getTeamMember(id: string): Promise<TeamMember | undefined> {
    await delay(160)
    return TEAM.find((m) => m.id === id)
  },
  async getManagerProfile(): Promise<CollabProfile> {
    await delay()
    return MANAGER_PROFILE
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
    await delay()
    return SOUHAITS_RECUS
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
    await delay(120)
    return MANAGER_KPIS
  },

  // -------------------------------------------------------------------- RH
  async getRhPeople(): Promise<RhPerson[]> {
    await delay()
    return RH_PEOPLE
  },
  async getRhPerson(id: string): Promise<RhPerson | undefined> {
    await delay(160)
    return RH_PEOPLE.find((p) => p.id === id)
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
    await delay(120)
    return RH_KPIS
  },
  async getRhAlerts(): Promise<RhAlert[]> {
    await delay()
    return RH_ALERTS
  },
  async getHautsPotentiels(): Promise<HautPotentiel[]> {
    await delay()
    return HAUTS_POTENTIELS
  },
  async getVeille(): Promise<VeilleType[]> {
    await delay()
    return VEILLE
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
    await delay()
    return NADIA_PROFILE
  },
}
