#!/usr/bin/env python3
"""
tests/test_profil_cv.py — CV de profil conservé (Lot 4).

Le collaborateur dépose/remplace SON CV (PDF) ; il est conservé côté serveur,
sa présence est reflétée dans la vue carrière, et il est servi au propriétaire
(et, par les règles d'ownership, à son manager / RH-ADMIN).
"""

from app.tests.conftest import anon, auth, hdr

_PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def test_upload_cv_ok_et_reflete_dans_carriere(client):
    csrf = auth(client, "collab")
    r = client.post(
        "/api/profils/me/cv",
        headers=hdr(csrf),
        files={"fichier": ("mon_cv.pdf", _PDF, "application/pdf")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["cv_filename"] == "mon_cv.pdf"
    assert body["cv_uploaded_at"]
    # La vue carrière reflète bien la présence du CV (persisté).
    car = client.get("/api/profils/me/carriere").json()
    assert car["cv_filename"] == "mon_cv.pdf"


def test_upload_cv_refuse_non_pdf(client):
    csrf = auth(client, "collab")
    r = client.post(
        "/api/profils/me/cv",
        headers=hdr(csrf),
        files={"fichier": ("cv.txt", b"pas un pdf", "text/plain")},
    )
    assert r.status_code == 400


def test_download_cv_par_proprietaire(client):
    csrf = auth(client, "collab")
    client.post(
        "/api/profils/me/cv",
        headers=hdr(csrf),
        files={"fichier": ("cv.pdf", _PDF, "application/pdf")},
    )
    pid = client.get("/api/profils/me/carriere").json()["profil_id"]
    r = client.get(f"/api/profils/{pid}/cv")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"


def test_upload_cv_exige_auth(client):
    anon(client)
    r = client.post("/api/profils/me/cv", files={"fichier": ("cv.pdf", _PDF, "application/pdf")})
    assert r.status_code in (401, 403)
