#!/usr/bin/env python3
"""
tests/test_import_excel.py — Import de profils depuis Excel (openpyxl, 100 % local).

Construit un .xlsx en mémoire et le POST : import correct (+ lignes ignorées),
RBAC (RH/ADMIN), fichier illisible -> 400.
"""

import io

from openpyxl import Workbook

from app.tests.conftest import auth, hdr


def _xlsx(rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _upload(content: bytes, name: str = "profils.xlsx"):
    return {"fichier": (name, content,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


def test_import_profils_ok_et_lignes_ignorees(client):
    data = _xlsx([
        ["nom", "prenom", "poste_actuel", "departement_key", "competences"],
        ["Testimport", "Alice", "Analyste", "risques", "Python, IFRS 9"],
        ["Deuxième", "Bob", "Conseiller", "retail_banking", ""],
        ["", "", "", "", ""],  # ligne sans nom -> ignorée
    ])
    csrf = auth(client, "rh")
    r = client.post("/api/profils/import-excel", files=_upload(data), headers=hdr(csrf))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["importes"] == 2
    assert body["ignorees"] == 1


def test_import_profils_entete_nom_manquant_400(client):
    data = _xlsx([["prenom", "poste_actuel"], ["Alice", "Analyste"]])
    csrf = auth(client, "rh")
    r = client.post("/api/profils/import-excel", files=_upload(data), headers=hdr(csrf))
    assert r.status_code == 400
    assert "nom" in r.json()["detail"].lower()


def test_import_profils_interdit_au_collab(client):
    csrf = auth(client, "collab")
    r = client.post("/api/profils/import-excel", files=_upload(b"peu-importe"), headers=hdr(csrf))
    assert r.status_code == 403


def test_import_fichier_illisible_400(client):
    csrf = auth(client, "rh")
    r = client.post("/api/profils/import-excel",
                    files=_upload(b"ceci-n-est-pas-un-xlsx"), headers=hdr(csrf))
    assert r.status_code == 400
