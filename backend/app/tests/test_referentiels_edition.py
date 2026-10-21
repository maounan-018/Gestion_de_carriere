#!/usr/bin/env python3
"""
tests/test_referentiels_edition.py — Édition RBAC des référentiels YAML (gabarit +
cartographie) : validation AVANT persistance, écriture atomique, rechargement à chaud.

IMPORTANT : les chemins des fichiers (SCHEMA_PATH / PATH) sont monkeypatchés vers des
COPIES temporaires — les vrais fichiers de config du dépôt ne sont jamais modifiés.
"""

import shutil

from app.tests.conftest import auth, hdr

# ------------------------------------------------------------------ Gabarit


def test_gabarit_edition_interdite_au_collab(client):
    csrf = auth(client, "collab")
    r = client.put(
        "/api/fiches/gabarit",
        headers=hdr(csrf),
        json={"sections": [{"key": "x", "label": "X", "kind": "metadata"}]},
    )
    assert r.status_code == 403


def test_gabarit_edition_rh_rechargee(client, monkeypatch, tmp_path):
    from app.services import fiche_config_service

    tmp = tmp_path / "fiche_schema.yaml"
    shutil.copy(fiche_config_service.SCHEMA_PATH, tmp)
    monkeypatch.setattr(fiche_config_service, "SCHEMA_PATH", str(tmp))

    csrf = auth(client, "rh")
    gab = client.get("/api/fiches/gabarit").json()
    gab["sections"].append({"key": "nouvelle_section", "label": "Nouvelle", "kind": "metadata"})
    r = client.put("/api/fiches/gabarit", headers=hdr(csrf), json=gab)
    assert r.status_code == 200, r.text
    # Rechargé à chaud : le GET reflète l'ajout.
    keys = [s["key"] for s in client.get("/api/fiches/gabarit").json()["sections"]]
    assert "nouvelle_section" in keys


def test_gabarit_invalide_400_fichier_intact(client, monkeypatch, tmp_path):
    from app.services import fiche_config_service

    tmp = tmp_path / "fiche_schema.yaml"
    shutil.copy(fiche_config_service.SCHEMA_PATH, tmp)
    monkeypatch.setattr(fiche_config_service, "SCHEMA_PATH", str(tmp))
    avant = tmp.read_text(encoding="utf-8")

    csrf = auth(client, "rh")
    r = client.put(
        "/api/fiches/gabarit",
        headers=hdr(csrf),
        json={"sections": [{"key": "x", "label": "X", "kind": "KIND_BIDON"}]},
    )
    assert r.status_code == 400
    assert tmp.read_text(encoding="utf-8") == avant  # fichier NON modifié


# --------------------------------------------------------------- Cartographie


def test_cartographie_edition_rh_rechargee(client, monkeypatch, tmp_path):
    from app.services import cartography_service

    tmp = tmp_path / "carto.yaml"
    shutil.copy(cartography_service.PATH, tmp)
    monkeypatch.setattr(cartography_service, "PATH", str(tmp))

    csrf = auth(client, "rh")
    doc = client.get("/api/fiches/cartographie").json()
    doc["departements"].append(
        {"key": "labo_test", "nom": "Labo Test", "pole": "Test", "metiers": ["Testeur"]}
    )
    r = client.put("/api/fiches/cartographie", headers=hdr(csrf), json=doc)
    assert r.status_code == 200, r.text
    depts = client.get("/api/fiches/departements").json()
    assert any(d["key"] == "labo_test" for d in depts)


def test_cartographie_cle_dupliquee_400_fichier_intact(client, monkeypatch, tmp_path):
    from app.services import cartography_service

    tmp = tmp_path / "carto.yaml"
    shutil.copy(cartography_service.PATH, tmp)
    monkeypatch.setattr(cartography_service, "PATH", str(tmp))
    avant = tmp.read_text(encoding="utf-8")

    csrf = auth(client, "rh")
    dup = {"departements": [{"key": "dup", "nom": "A"}, {"key": "dup", "nom": "B"}]}
    r = client.put("/api/fiches/cartographie", headers=hdr(csrf), json=dup)
    assert r.status_code == 400
    assert tmp.read_text(encoding="utf-8") == avant  # fichier NON modifié
