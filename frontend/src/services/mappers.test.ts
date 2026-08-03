import { describe, it, expect } from 'vitest'
import {
  relativeTime,
  mapNotification,
  mapFormation,
  mapSouhait,
  mapSouhaitRecu,
  mapOffre,
  mapCandidature,
  mapProfil,
  mapTeamMember,
  mapCollabProfile,
  mapColleague,
  mapKpi,
  mapKpiCard,
  mapHautPotentiel,
  mapVeille,
  mapAlerte,
  mapReco,
  mapMobilite,
  mapFamille,
  mapSyntheseRh,
  mapRhOffre,
  mapRhCandidate,
  mapVacancy,
  mapVacancyReco,
  mapCartoMatrix,
  type CartoMatrixOut,
  type NotificationOut,
  type FormationOut,
  type SouhaitOut,
  type SouhaitRecuOut,
  type OffreCompatOut,
  type CandidatureMineOut,
  type ProfilOut,
  type ProfilCarriereOut,
  type AnnuaireOut,
  type KpiItemOut,
  type HautPotentielOut,
  type VeilleOut,
  type AlerteOut,
  type RecommendationOut,
  type RhOffreOut,
  type OffreCandidatOut,
  type VacancyOut,
  type VacancyRecoOut,
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

describe('mapSouhaitRecu', () => {
  const base: SouhaitRecuOut = {
    id: 4, profil_id: 9, titre: 'Évoluer manager', kind: 'carriere', horizon: '1 an',
    description: 'desc', statut: 'en_discussion', pushed: true,
    created_at: new Date(Date.now() - 2 * 3_600_000).toISOString(), decided_at: null,
    membre_nom: 'Idrissi', membre_prenom: 'Karim', membre_matricule: 'KI-1',
  }
  it('assemble nom/initiales du membre et mappe le statut reçu', () => {
    const r = mapSouhaitRecu(base)
    expect(r.id).toBe('4')
    expect(r.memberId).toBe('9')
    expect(r.memberName).toBe('Karim Idrissi')
    expect(r.memberInitials).toBe('KI')
    expect(r.kind).toBe('carriere')
    expect(r.status).toBe('transmis RH') // en_discussion
  })
  it('kind mission ; statut inconnu → « à traiter »', () => {
    expect(mapSouhaitRecu({ ...base, kind: 'mission' }).kind).toBe('mission')
    expect(mapSouhaitRecu({ ...base, statut: 'zzz' }).status).toBe('à traiter')
  })
})

describe('mapKpiCard', () => {
  it('délègue à mapKpi (icône/route/valeur)', () => {
    const k: KpiItemOut = { key: 'equipe', value: 8, label: 'Équipe', hint: '2 à risque' }
    const r = mapKpiCard(k)
    expect(r.icon).toBe('team')
    expect(r.value).toBe('8')
    expect(r.to).toBe('manager.equipe')
    expect(r.hint).toBe('2 à risque')
  })
})

describe('mapHautPotentiel', () => {
  const base: HautPotentielOut = {
    profil_id: 5, nom: 'Haddad', prenom: 'Sofia', poste_actuel: 'Quant',
    departement_key: 'risques', score: 88, nb_competences: 6, niveau_moyen: 4,
  }
  it('seuils de readiness selon le score', () => {
    expect(mapHautPotentiel(base).readiness).toBe('Prêt · 6-12 mois') // >= 85
    expect(mapHautPotentiel({ ...base, score: 78 }).readiness).toBe('Prêt · 12-18 mois') // >= 75
    expect(mapHautPotentiel({ ...base, score: 60 }).readiness).toBe('À développer · 18-24 mois')
  })
  it('cible = poste_actuel, repli « Évolution »', () => {
    expect(mapHautPotentiel(base).personId).toBe('5')
    expect(mapHautPotentiel(base).target).toBe('Quant')
    expect(mapHautPotentiel({ ...base, poste_actuel: null }).target).toBe('Évolution')
  })
})

describe('mapVeille', () => {
  const v: VeilleOut = { key: 'rh', label: 'RH ↔ collab', realises: 34, planifies: 49, en_retard: 12 }
  it('mappe compteurs + libellé de synthèse', () => {
    const r = mapVeille(v)
    expect(r.key).toBe('rh')
    expect(r.done).toBe(34)
    expect(r.planned).toBe(49)
    expect(r.late).toBe(12)
    expect(r.desc).toBe('34 réalisés · 49 planifiés · 12 en retard')
  })
  it('toute clé non « rh » → « annuels »', () => {
    expect(mapVeille({ ...v, key: 'annuels' }).key).toBe('annuels')
    expect(mapVeille({ ...v, key: 'zzz' }).key).toBe('annuels')
  })
})

describe('mapCollabProfile', () => {
  const c: ProfilCarriereOut = {
    profil_id: 3, nom: 'Bennani', prenom: 'Marc', poste_actuel: 'Analyste',
    departement_key: 'risques', aspirations: 'Manager',
    competences: [
      { libelle: 'A', categorie: null, niveau: 4 },
      { libelle: 'B', categorie: null, niveau: 2 },
    ],
    stations: [
      { periode: '2020', titre: 'Junior', description: null, etat: 'passe', ordre: 1 },
      { periode: 'Objectif', titre: 'Manager', description: 'cible', etat: 'objectif', ordre: 3 },
      { periode: '2023', titre: 'Senior', description: null, etat: 'actuel', ordre: 2 },
    ],
    avis_pairs: [{ auteur_nom: 'Jean Dupont', auteur_role: 'Manager', initiales: null, texte: 'top', etoiles: 5 }],
  }
  it('progression, stations triées, avis, poste visé', () => {
    const r = mapCollabProfile(c)
    expect(r.progressionPct).toBe(60) // moy (4+2)/2 = 3 → 60
    expect(r.posteVise).toBe('Manager') // titre du goal
    expect(r.skills.map((s) => s.pct)).toEqual([80, 40])
    expect(r.stations.map((s) => s.title)).toEqual(['Junior', 'Senior', 'Manager']) // trié par ordre
    expect(r.stations[2].state).toBe('goal')
    expect(r.peerReviews[0].initials).toBe('JD') // initiales null → dérivées du nom
  })
  it('replis neutres documentés (horizon/zones/todos)', () => {
    const r = mapCollabProfile(c)
    expect(r.horizon).toBe('')
    expect(r.zones).toBe('')
    expect(r.todos).toEqual([])
  })
  it('poste visé : poste_actuel puis « — » sans goal', () => {
    expect(mapCollabProfile({ ...c, stations: [], aspirations: null }).posteVise).toBe('Analyste')
    expect(mapCollabProfile({ ...c, stations: [], poste_actuel: null, aspirations: null }).posteVise).toBe('—')
  })
})

describe('mapColleague', () => {
  const a: AnnuaireOut = {
    id: 7, nom: 'Idrissi', prenom: 'Karim', poste_actuel: 'Analyste Risque',
    departement_key: 'corporate_banking', competences: ['Scoring'],
  }
  it('nom/initiales/entité + compétences', () => {
    const r = mapColleague(a)
    expect(r.id).toBe('7')
    expect(r.initials).toBe('KI')
    expect(r.name).toBe('Karim Idrissi')
    expect(r.entity).toBe('Corporate Banking')
    expect(r.skills).toEqual(['Scoring'])
  })
  it('replis : poste « — », pôle inconnu title-casé, pôle null « — »', () => {
    expect(mapColleague({ ...a, poste_actuel: null }).role).toBe('—')
    expect(mapColleague({ ...a, departement_key: 'un_pole_inconnu' }).entity).toBe('Un Pole Inconnu')
    expect(mapColleague({ ...a, departement_key: null }).entity).toBe('—')
  })
})

describe('mapTeamMember', () => {
  const p: ProfilOut = {
    id: 3, user_id: 4, nom: 'Martin', prenom: 'Alice', matricule: 'AM-1',
    poste_actuel: 'Analyste Senior', departement_key: 'risques', manager_id: 3,
    aspirations: 'Lead', synthetique: true, created_at: new Date().toISOString(),
    competences: [
      { id: 1, libelle: 'Analyse', categorie: null, niveau: 5, source: 'declaratif', skill_id: null, skill_label_fr: null },
      { id: 2, libelle: 'Python', categorie: null, niveau: 3, source: 'declaratif', skill_id: null, skill_label_fr: null },
    ],
  }
  it('identité, ring, forces', () => {
    const r = mapTeamMember(p)
    expect(r.id).toBe('3')
    expect(r.name).toBe('Alice Martin')
    expect(r.initials).toBe('AM')
    expect(r.ring).toBe(80) // moy (5+3)/2 = 4 → 80
    expect(r.strengths).toEqual(['Analyse']) // niveau >= 4
    expect(r.skills[0]).toEqual({ label: 'Analyse', pct: 100 })
  })
  it('replis neutres documentés (§3) : seniority/eval/entretien/gaps/evals/flag', () => {
    const r = mapTeamMember(p)
    expect(r.seniority).toBe('—')
    expect(r.evalScore).toBe('—')
    expect(r.lastEntretien).toBe('—')
    expect(r.aspirationHorizon).toBe('')
    expect(r.gaps).toEqual([])
    expect(r.evals).toEqual([])
    expect(r.flag).toBeNull()
  })
})

describe('mapProfil (replis neutres §3)', () => {
  const p: ProfilOut = {
    id: 3, user_id: 4, nom: 'Bennani', prenom: 'Marc', matricule: 'CB-3390',
    poste_actuel: 'Analyste', departement_key: 'risques', manager_id: 3,
    aspirations: null, synthetique: true, created_at: new Date().toISOString(),
    competences: [{ id: 1, libelle: 'A', categorie: null, niveau: 4, source: 'declaratif', skill_id: null, skill_label_fr: null }],
  }
  it('ancienneté / éval / dernier entretien = « — », gaps=[], flag=null', () => {
    const r = mapProfil(p)
    expect(r.seniority).toBe('—')
    expect(r.evalScore).toBe('—')
    expect(r.lastRh).toBe('—')
    expect(r.gaps).toEqual([])
    expect(r.flag).toBeNull()
    expect(r.aspiration).toBe('') // aspirations null → ''
  })
})

describe('mapReco', () => {
  const base: RecommendationOut = {
    poste_vise: 'Manager', score_actuel: 68, modele_extraction: 'm', modele_conseil: 'c',
    competences_a_developper: [
      { competence: 'Diriger une équipe', importance: 'essentielle', type: 'comportementale', niveau_sfia: 5, description: null, sous_competences: ['a', 'b', 'c', 'd'] },
      { competence: 'Data', importance: 'utile', type: 'outil_technologie', niveau_sfia: null, description: 'Analyser', sous_competences: [] },
    ],
    passerelles_metiers: [
      { metier: 'Manager Risques', source: 'ESCO', pertinence: 0.82 },
      { metier: 'Chef de projet', source: 'O*NET', pertinence: 0.5 },
    ],
    plan_developpement: 'Plan X',
  }
  it('compétences : criticité, icône, tag SFIA, desc dérivée des sous-compétences', () => {
    const d = mapReco(base)
    expect(d.posteVise).toBe('Manager')
    expect(d.pct).toBe(68)
    expect(d.plan).toBe('Plan X')
    expect(d.skills[0].critical).toBe(true) // importance « essent… »
    expect(d.skills[0].icon).toBe('user') // comportementale
    expect(d.skills[0].tag).toBe('Niveau SFIA 5')
    expect(d.skills[0].desc).toBe('Étapes : a · b · c') // 3 premières, description null
    expect(d.skills[1].critical).toBe(false)
    expect(d.skills[1].desc).toBe('Analyser')
    expect(d.skills[1].tag).toBe('outil_technologie') // pas de SFIA → type
  })
  it('passerelles : pct, label/ton par seuil', () => {
    const d = mapReco(base)
    expect(d.passerelles[0].pct).toBe(82)
    expect(d.passerelles[0].label).toBe('Forte affinité')
    expect(d.passerelles[0].tone).toBe('new')
    expect(d.passerelles[1].label).toBe('Affinité modérée') // 50 < 55
    expect(d.passerelles[1].tone).toBe('mut')
  })
  it('replis : poste visé & plan par défaut', () => {
    expect(mapReco({ ...base, poste_vise: null }).posteVise).toBe('Votre poste visé')
    expect(mapReco({ ...base, plan_developpement: '' }).plan).toBe('Plan de développement personnalisé en cours.')
  })
})

describe('mapRhOffre', () => {
  const o: RhOffreOut = {
    id: 6, titre: 'Responsable Conformité', type: 'offre_poste', departement_key: 'conformite',
    perimetre_bmci: null, statut: 'ouverte', candidats_total: 11, candidats_compatibles: 4, retenu_nom: 'Leïla Fassi',
  }
  it('clé/type/statut/compteurs/retenu', () => {
    const r = mapRhOffre(o)
    expect(r.key).toBe('6')
    expect(r.type).toBe('Poste')
    expect(r.status).toBe('ouvert')
    expect(r.ligne).toBe('Conformité')
    expect(r.candidates).toBe(11)
    expect(r.compatible).toBe(4)
    expect(r.retenu).toBe('Leïla Fassi')
  })
  it('retenu absent → undefined ; pourvue → clôturé', () => {
    expect(mapRhOffre({ ...o, retenu_nom: null }).retenu).toBeUndefined()
    expect(mapRhOffre({ ...o, statut: 'pourvue' }).status).toBe('clôturé')
  })
})

describe('mapRhCandidate', () => {
  const c: OffreCandidatOut = {
    profil_id: 8, candidature_id: 8, nom: 'Fassi', prenom: 'Leïla', poste_actuel: 'Risk Officer',
    departement_key: 'risques', score: 74.6, statut: 'retenue', couvertes: ['Réglementaire'], ecarts: ['Crédit'],
  }
  it('ids, score arrondi, statut de revue, couvertes/écarts', () => {
    const r = mapRhCandidate(c)
    expect(r.personId).toBe('8')
    expect(r.candidatureId).toBe('8')
    expect(r.name).toBe('Leïla Fassi')
    expect(r.initials).toBe('LF')
    expect(r.score).toBe(75) // arrondi 74.6
    expect(r.status).toBe('retenu')
    expect(r.matched).toEqual(['Réglementaire'])
    expect(r.gaps).toEqual(['Crédit'])
  })
  it('statut déposée → nouveau ; score null → 0', () => {
    expect(mapRhCandidate({ ...c, statut: 'deposee' }).status).toBe('nouveau')
    expect(mapRhCandidate({ ...c, score: null }).score).toBe(0)
  })
})

describe('mapVacancy + mapVacancyReco', () => {
  const v: VacancyOut = {
    id: 12, titre: 'Analyste Crédit Senior', type: 'offre_poste', departement_key: 'corporate_banking',
    perimetre_bmci: null, description: null, statut: 'ouverte',
    created_at: new Date(Date.now() - 3 * 86_400_000).toISOString(),
    recos: [
      { profil_id: 1, nom: 'Martin', prenom: 'Alice', poste_actuel: 'Analyste', score: 82, matched: ['IFRS 9', 'Crédit'], gaps: [] },
      { profil_id: 2, nom: 'Tazi', prenom: 'Omar', poste_actuel: 'Junior', score: 30, matched: [], gaps: ['Crédit'] },
    ],
  }
  it('poste + recos triées par adéquation', () => {
    const r = mapVacancy(v)
    expect(r.key).toBe('12')
    expect(r.type).toBe('Poste')
    expect(r.ligne).toBe('Corporate Banking')
    expect(r.status).toBe('ouvert')
    expect(r.sub).toBe('Poste · Corporate Banking') // description null
    expect(r.openSince).toMatch(/^Ouvert /)
    expect(r.recos).toHaveLength(2)
    expect(r.recos[0]).toMatchObject({ memberId: '1', score: 82, label: 'Forte adéquation', tone: 'new' })
    expect(r.recos[0].why).toBe('Points forts : IFRS 9, Crédit')
    expect(r.recos[1].label).toBe('À explorer') // score 30 < 40
    expect(r.recos[1].why).toBe('Profil à faire monter en compétence sur ce poste.') // matched vide
  })
  it('mapVacancyReco : seuil « bonne adéquation »', () => {
    const rr: VacancyRecoOut = { profil_id: 5, nom: 'X', prenom: null, poste_actuel: null, score: 55, matched: ['A'], gaps: [] }
    expect(mapVacancyReco(rr)).toMatchObject({ memberId: '5', score: 55, label: 'Bonne adéquation', tone: 'ai', why: 'Points forts : A' })
  })
})

describe('mapMobilite', () => {
  it('mappe une passerelle et libelle la source', () => {
    const m = mapMobilite({ occupation_id: 42, metier: 'Analyste crédit', source: 'esco', competences_partagees: 5 })
    expect(m).toMatchObject({ id: 42, metier: 'Analyste crédit', source: 'ESCO', partagees: 5 })
  })
  it('conserve une source inconnue telle quelle', () => {
    expect(mapMobilite({ occupation_id: 1, metier: 'X', source: 'maison', competences_partagees: 2 }).source).toBe('maison')
  })
})

describe('mapFamille', () => {
  it('mappe et humanise la famille', () => {
    const f = mapFamille({ famille: 'outil_technologie', detenues: 18, profils_couverts: 8, niveau_moyen: 2.8, demande: 2, tension: 'faible' })
    expect(f).toMatchObject({ famille: 'Outils & Tech', profilsCouverts: 8, demande: 2, tension: 'faible' })
  })
  it('replie une tension inconnue sur faible', () => {
    expect(mapFamille({ famille: 'metier', detenues: 1, profils_couverts: 1, niveau_moyen: null, demande: 0, tension: 'bizarre' }).tension).toBe('faible')
  })
})

describe('mapSyntheseRh', () => {
  it('mappe les clés snake_case vers camelCase', () => {
    const s = mapSyntheseRh({
      effectif: 14,
      par_pole: [{ pole: 'Risques', effectif: 5 }],
      candidatures_par_statut: [{ statut: 'retenue', nombre: 2 }],
      familles_en_tension: 1,
    })
    expect(s).toMatchObject({
      effectif: 14, famillesEnTension: 1,
      parPole: [{ pole: 'Risques', effectif: 5 }],
      candidaturesParStatut: [{ statut: 'retenue', nombre: 2 }],
    })
  })
})

describe('mapCartoMatrix', () => {
  it('humanise les familles, propage le pôle et aligne les niveaux', () => {
    const out: CartoMatrixOut = {
      familles: ['metier', 'data'],
      lignes: [
        { departement_key: 'retail_banking', label: 'Retail Banking', pole: 'Lignes métiers commerciales',
          effectif: 3, niveau_moyen: 3.5, niveaux: [4, 3], people: ['Youssef Alaoui'] },
        { departement_key: 'risques', label: 'Risques', pole: 'Risques, conformité & contrôle',
          effectif: 1, niveau_moyen: 4, niveaux: [5, null], people: [] },
      ],
    }
    const m = mapCartoMatrix(out)
    expect(m.familles).toEqual(['Métier', 'Data & Analyse'])
    expect(m.lignes[0]).toMatchObject({
      departementKey: 'retail_banking', label: 'Retail Banking',
      pole: 'Lignes métiers commerciales', effectif: 3, niveaux: [4, 3],
    })
    expect(m.lignes[1].pole).toBe('Risques, conformité & contrôle')
    expect(m.lignes[1].niveaux).toEqual([5, null])
  })

  it('tolère un pôle absent (repli null)', () => {
    const out: CartoMatrixOut = {
      familles: ['metier'],
      lignes: [{ departement_key: 'x', label: 'X', effectif: 1, niveau_moyen: 2, niveaux: [2], people: [] }],
    }
    expect(mapCartoMatrix(out).lignes[0].pole).toBeNull()
  })
})
