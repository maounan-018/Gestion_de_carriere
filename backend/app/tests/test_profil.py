#!/usr/bin/env python3
"""
tests/test_profil.py — Tests de la couche métier Profil (services/profil_service).

Couvre : création (+ compétences), lecture, 404, mise à jour partielle des
aspirations (« poste visé »), ajout de compétences, listing filtré.
"""

from app.schemas.profil import ProfilCompetenceIn, ProfilCreate, ProfilUpdate
from app.services import profil_service


def test_create_and_get(db):
    out = profil_service.create_profil(db, ProfilCreate(
        nom="El Amrani", prenom="Aya", poste_actuel="Chargée d'Affaires Senior",
        departement_key="risques", aspirations="Manager d'équipe Risques",
        synthetique=True,
        competences=[ProfilCompetenceIn(libelle="Analyse crédit", niveau=4, source="declaratif")],
    ))
    assert out.id > 0
    assert out.synthetique is True
    assert out.aspirations.startswith("Manager")
    assert len(out.competences) == 1
    assert out.competences[0].niveau == 4

    got = profil_service.get_profil(db, out.id)
    assert got is not None
    assert got.nom == "El Amrani"
    assert len(got.competences) == 1


def test_get_missing_returns_none(db):
    assert profil_service.get_profil(db, 999) is None


def test_update_partial_aspirations(db):
    out = profil_service.create_profil(db, ProfilCreate(nom="Naji", poste_actuel="Analyste"))
    upd = profil_service.update_profil(db, out.id, ProfilUpdate(
        aspirations="Directeur Exécutif Risques", poste_actuel="Directeur de Pôle"))
    assert upd is not None
    assert upd.aspirations == "Directeur Exécutif Risques"
    assert upd.poste_actuel == "Directeur de Pôle"
    assert upd.nom == "Naji"  # champ non fourni : inchangé


def test_update_missing_returns_none(db):
    assert profil_service.update_profil(db, 999, ProfilUpdate(nom="X")) is None


def test_add_competences_and_list_filter(db):
    out = profil_service.create_profil(db, ProfilCreate(
        nom="Idrissi", departement_key="risques", synthetique=True))
    profil_service.add_competences(db, out.id, [
        ProfilCompetenceIn(libelle="Modélisation", niveau=5, source="cv")])

    got = profil_service.get_profil(db, out.id)
    assert len(got.competences) == 1
    assert got.competences[0].source == "cv"

    listed = profil_service.list_profils(db, departement_key="risques", synthetique=True)
    assert any(p.id == out.id for p in listed)
    # un persona d'un autre département ne remonte pas
    assert profil_service.list_profils(db, departement_key="finance") == []
