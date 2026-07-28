import { describe, it, expect } from 'vitest'
import {
  relativeTime,
  mapNotification,
  mapFormation,
  mapSouhait,
  mapOffre,
  mapCandidature,
  mapProfil,
  mapKpi,
  mapAlerte,
  type NotificationOut,
  type FormationOut,
  type SouhaitOut,
  type OffreCompatOut,
  type CandidatureMineOut,
  type ProfilOut,
  type KpiItemOut,
  type AlerteOut,
} from './mappers'

describe('relativeTime', () => {
  it("renvoie « à l'instant » pour maintenant", () => {
    expect(relativeTime(new Date().toISOString())).toBe("à l'instant")
  })
  it('formate minutes / heures / jours', () => {
    const ago = (ms: number) => new Date(Date.now() - ms).toISOString()
    expect(relativeTime(ago(5 * 60_000))).toBe('il y a 5 min')
    expect(relativeTime(ago(3 * 3_600_000))).toBe('il y a 3 h')
    expect(relativeTime(ago(2 * 86_400_000))).toBe('il y a 2 j')
  })
  it('renvoie une chaîne vide pour une date invalide', () => {
    expect(relativeTime('pas-une-date')).toBe('')
  })
})

describe('mapNotification', () => {
  const base: NotificationOut = {
    id: 5, type: 'offre', titre: 'Nouvelle offre', texte: null,
    to_route: 'offres', lu: false, created_at: new Date().toISOString(),
  }
  it('mappe id, icône, non-lu et route par rôle', () => {
    const n = mapNotification(base, 'collab')
    expect(n.id).toBe('5')
    expect(n.icon).toBe('brief') // offre → brief
    expect(n.unread).toBe(true) // !lu
    expect(n.text).toBe('') // texte null → ''
    expect(n.to).toBe('collab.offres')
  })
  it('retombe sur le dashboard du rôle pour une route inconnue', () => {
    const n = mapNotification({ ...base, to_route: 'xyz' }, 'rh')
    expect(n.to).toBe('rh.dashboard')
  })
  it('icône par défaut « bell » pour un type inconnu', () => {
    expect(mapNotification({ ...base, type: 'inconnu' }, 'collab').icon).toBe('bell')
  })
})

describe('mapFormation', () => {
  it('mappe les champs et dérive la raison', () => {
    const f: FormationOut = {
      id: 12, titre: 'Python', provider: 'Coursera', duree: '20 h',
      niveau: 'Inter', domaine: 'Data', tags: ['data'], skill_cible: 'Analyse de données', synthetique: true,
    }
    const r = mapFormation(f)
    expect(r.id).toBe('12')
    expect(r.status).toBe('recommended')
    expect(r.progress).toBe(0)
    expect(r.reason).toBe('Compétence visée : Analyse de données')
  })
  it('reason undefined sans skill_cible', () => {
    const f: FormationOut = {
      id: 1, titre: 'X', provider: null, duree: null, niveau: null,
      domaine: null, tags: [], skill_cible: null, synthetique: false,
    }
    expect(mapFormation(f).reason).toBeUndefined()
    expect(mapFormation(f).provider).toBe('')
  })
})

describe('mapSouhait', () => {
  it('porte l\'id et mappe le statut « poussé »', () => {
    const s: SouhaitOut = {
      id: 2, profil_id: 3, titre: 'Mission ESG', kind: 'mission', horizon: '6 mois',
      description: 'desc', statut: 'pousse', pushed: true, created_at: new Date().toISOString(), decided_at: null,
    }
    const r = mapSouhait(s)
    expect(r.id).toBe('2')
    expect(r.status).toBe('Poussé au manager')
    expect(r.tone).toBe('ai')
    expect(r.pushed).toBe(true)
  })
})

describe('mapOffre', () => {
  const base: OffreCompatOut = {
    id: 7, type: 'offre_poste', titre: 'Analyste Risque', description: null,
    perimetre_bmci: 'Risques', departement_key: null, statut: 'ouverte',
    competences: ['IFRS 9'], score_compat: 88, couvertes: 3, ecarts: 1,
  }
  it('clé = id backend, type libellé, % et adéquation', () => {
    const o = mapOffre(base)
    expect(o.key).toBe('7')
    expect(o.type).toBe('Poste')
    expect(o.pct).toBe(88)
    expect(o.tone).toBe('new') // >= 85
    expect(o.adq).toBe('Très adapté')
    expect(o.fitTitle).toBe('88 % de compatibilité')
  })
  it('un POSTE est confidentiel (manager non informé)', () => {
    const o = mapOffre(base)
    expect(o.managerInformed).toBe(false)
    expect(o.noteOk).toBe(true)
  })
  it('une MISSION informe le manager', () => {
    const o = mapOffre({ ...base, type: 'mission' })
    expect(o.type).toBe('Mission transverse')
    expect(o.managerInformed).toBe(true)
    expect(o.noteOk).toBe(false)
  })
})

describe('mapCandidature', () => {
  it('mappe statut → libellé/ton et le type d\'offre', () => {
    const c: CandidatureMineOut = {
      id: 1, statut: 'retenue', score: 90, created_at: '2026-01-15T10:00:00',
      offre_titre: 'Analyste Senior', offre_type: 'mission',
    }
    const r = mapCandidature(c)
    expect(r.title).toBe('Analyste Senior')
    expect(r.status).toBe('Retenue')
    expect(r.tone).toBe('ok')
    expect(r.type).toBe('Mission transverse')
  })
})

describe('mapProfil', () => {
  it('id, initiales, ring = niveau moyen ×20, pôle libellé', () => {
    const p: ProfilOut = {
      id: 3, user_id: 4, nom: 'Bennani', prenom: 'Marc', matricule: 'CB-3390',
      poste_actuel: 'Analyste', departement_key: 'risques', manager_id: 3,
      aspirations: 'Évoluer', synthetique: true, created_at: new Date().toISOString(),
      competences: [
        { id: 1, libelle: 'A', categorie: null, niveau: 4, source: 'declaratif', skill_id: null, skill_label_fr: null },
        { id: 2, libelle: 'B', categorie: null, niveau: 2, source: 'declaratif', skill_id: null, skill_label_fr: null },
      ],
    }
    const r = mapProfil(p)
    expect(r.id).toBe('3')
    expect(r.initials).toBe('MB')
    expect(r.ring).toBe(60) // moyenne (4+2)/2 = 3 → 60
    expect(r.pole).toBe('Risques')
  })
})

describe('mapKpi', () => {
  it('mappe icône, valeur en chaîne et route', () => {
    const k: KpiItemOut = { key: 'effectif', value: 2850, label: 'Effectif', hint: null }
    const r = mapKpi(k)
    expect(r.icon).toBe('team')
    expect(r.value).toBe('2850')
    expect(r.to).toBe('rh.annuaire')
    expect(r.hint).toBeUndefined()
  })
})

describe('mapAlerte', () => {
  it('mappe kind/severity/route, valeurs sûres par défaut', () => {
    const a: AlerteOut = {
      kind: 'retention', severity: 'crit', titre: 'Risque', texte: 'Départ probable',
      cta: 'Analyser', to_route: 'hautsPotentiels',
    }
    const r = mapAlerte(a)
    expect(r.kind).toBe('retention')
    expect(r.icon).toBe('shield')
    expect(r.severity).toBe('crit')
    expect(r.to).toBe('rh.hautsPotentiels')
  })
  it('retombe sur potential/info/dashboard pour des valeurs inconnues', () => {
    const r = mapAlerte({ kind: 'zzz', severity: 'zzz', titre: 't', texte: 'x', cta: 'c', to_route: null })
    expect(r.kind).toBe('potential')
    expect(r.severity).toBe('info')
    expect(r.to).toBe('rh.dashboard')
  })
})
