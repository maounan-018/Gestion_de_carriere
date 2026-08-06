"""Inférence de faisabilité d'aspiration (Workstream D) : à partir des parcours de
la population, distingue une aspiration accessible d'une aspiration ambitieuse et
détecte les trajectoires NON LINÉAIRES (changement de filière). Auto-seed minimal."""

from app.services import trajectory_service as ts
from app.models.profil import Profil
from app.models.carriere import ProfilStation, StationEtat


def _seed_pop(db):
    # Filière RISQUES : un directeur (avec parcours) + le collaborateur junior.
    dirp = Profil(nom="Dir", prenom="R", poste_actuel="Directeur·rice Risques",
                  departement_key="risques")
    db.add(dirp)
    db.flush()
    db.add_all([
        ProfilStation(profil_id=dirp.id, periode="2016", titre="Analyste risques",
                      etat=StationEtat.PASSE, ordre=0),
        ProfilStation(profil_id=dirp.id, periode="2020", titre="Responsable Risk manager crédit",
                      etat=StationEtat.PASSE, ordre=1),
        ProfilStation(profil_id=dirp.id, periode="Aujourd'hui", titre="Directeur·rice Risques",
                      etat=StationEtat.ACTUEL, ordre=2),
    ])
    collab = Profil(nom="Jr", prenom="A", poste_actuel="Analyste risques",
                    departement_key="risques")
    db.add(collab)
    db.commit()
    return collab


def test_aspiration_ambitieuse_avec_intermediaires(db):
    collab = _seed_pop(db)
    collab.poste_vise = "Directeur·rice Risques"
    db.commit()

    r = ts.analyser_aspiration(db, collab.id)
    assert r is not None
    assert r["reachable"] is True
    assert r["verdict"] == "ambitieuse"        # 3 niveaux au-dessus
    assert r["ecart_niveau"] == 3
    assert r["lineaire"] is True               # même filière (risques)
    assert "Responsable Risk manager crédit" in r["intermediaires"]


def test_aspiration_non_lineaire_change_de_filiere(db):
    collab = _seed_pop(db)
    # même dept que le collab = risques ; aspiration dans une AUTRE filière
    other = Profil(nom="P", prenom="D", poste_actuel="Directeur·rice Retail Banking",
                   departement_key="retail_banking")
    db.add(other)
    db.commit()
    collab.poste_vise = "Directeur·rice Retail Banking"
    db.commit()

    r = ts.analyser_aspiration(db, collab.id)
    assert r["reachable"] is True
    assert r["lineaire"] is False              # risques → retail = non linéaire


def test_sans_poste_vise_renvoie_none(db):
    collab = _seed_pop(db)
    assert ts.analyser_aspiration(db, collab.id) is None
