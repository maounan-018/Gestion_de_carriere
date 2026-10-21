"""Évaluation de MISSION (Workstream C) : le manager note les compétences utilisées
par un participant ; une compétence absente du profil est AJOUTÉE (source
evaluation_mission) avec attribution (évaluateur + mission), et son % d'acquisition
reflète la note du manager. Auto-seed minimal (le fixture `db` fournit un schéma nu)."""

from sqlalchemy import select

from app.models.offre import Offre
from app.models.profil import CompetenceSource, Profil, ProfilCompetence
from app.models.user import Role, User
from app.services import evaluation_service as ev


def _setup(db):
    mgr = User(email="mgr.test@bmci.local", name="Karim Naji", role=Role.MANAGER)
    profil = Profil(nom="El Amrani", prenom="Youssef")
    offre = Offre(titre="Mission Cartographie des risques", type="mission")
    db.add_all([mgr, profil, offre])
    db.commit()
    return profil, offre, mgr


def test_evaluer_mission_ajoute_competence_et_attribue(db):
    profil, offre, mgr = _setup(db)

    res = ev.evaluer_mission(
        db,
        profil_id=profil.id,
        offre_id=offre.id,
        evaluateur_id=mgr.id,
        items=[{"libelle": "Compétence mission test", "skill_id": None, "score": 8}],
    )
    assert res == {"evaluees": 1, "ajoutees": 1}

    pc = db.scalars(select(ProfilCompetence).where(ProfilCompetence.profil_id == profil.id)).first()
    assert pc is not None
    assert pc.libelle == "Compétence mission test"
    assert pc.source == CompetenceSource.EVAL_MISSION  # ajoutée via la mission

    # % d'acquisition = note manager 8 → 80 (seule source manager, renormalisée)
    assert ev.acquisition_map(db, profil.id)[pc.id] == 80

    # attribution : évaluée par le manager, au titre de la mission
    attr = ev.attribution_map(db, profil.id)
    assert pc.id in attr
    assert attr[pc.id]["evaluee_par"] == "Karim Naji"
    assert attr[pc.id]["mission"] == "Mission Cartographie des risques"


def test_evaluer_mission_reevalue_competence_existante_sans_doublon(db):
    profil, offre, mgr = _setup(db)
    pc = ProfilCompetence(
        profil_id=profil.id, libelle="gestion des risques", source=CompetenceSource.DECLARATIF
    )
    db.add(pc)
    db.commit()

    res = ev.evaluer_mission(
        db,
        profil_id=profil.id,
        offre_id=offre.id,
        evaluateur_id=mgr.id,
        items=[{"libelle": "gestion des risques", "skill_id": None, "score": 5}],
    )
    assert res == {"evaluees": 1, "ajoutees": 0}  # pas de doublon
    assert (
        db.scalar(
            select(ProfilCompetence)
            .where(ProfilCompetence.profil_id == profil.id)
            .with_only_columns(ProfilCompetence.id)
            .order_by(None)
        )
        is not None
    )
    assert (
        len(
            db.scalars(
                select(ProfilCompetence).where(ProfilCompetence.profil_id == profil.id)
            ).all()
        )
        == 1
    )
    assert ev.acquisition_map(db, profil.id)[pc.id] == 50  # 5 → 50
