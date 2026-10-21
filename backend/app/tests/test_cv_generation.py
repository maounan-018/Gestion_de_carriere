"""Génération de CV PDF (Workstream D) : le CV d'un profil est produit à partir de
ses données réelles (parcours + compétences), écrit sur disque, et le profil est
marqué `cv_filename`/`cv_uploaded_at` (→ visible côté manager / HRBP). Auto-seed
minimal (le fixture `db` fournit un schéma nu)."""

from datetime import datetime

from pypdf import PdfReader

from app.models.carriere import ProfilStation, StationEtat
from app.models.profil import CompetenceSource, Profil, ProfilCompetence
from app.services import cv_generation_service as cv


def _setup(db):
    profil = Profil(
        nom="El Amrani",
        prenom="Youssef",
        poste_actuel="Conseiller clientèle particuliers",
        departement_key="retail_banking",
        matricule="CB-3390",
        poste_vise="Chargé d'affaires professionnels",
        horizon="1 an",
    )
    db.add(profil)
    db.commit()
    db.add_all(
        [
            ProfilStation(
                profil_id=profil.id,
                periode="2020",
                titre="Téléconseiller",
                etat=StationEtat.PASSE,
                ordre=0,
            ),
            ProfilStation(
                profil_id=profil.id,
                periode="Aujourd'hui",
                titre="Conseiller clientèle particuliers",
                etat=StationEtat.ACTUEL,
                ordre=1,
            ),
            ProfilCompetence(
                profil_id=profil.id,
                libelle="gestion de la relation client",
                niveau=4,
                source=CompetenceSource.FICHE,
            ),
            ProfilCompetence(
                profil_id=profil.id,
                libelle="analyse de besoins",
                niveau=None,
                source=CompetenceSource.CV,
            ),
        ]
    )
    db.commit()
    return profil


def test_generer_cv_ecrit_pdf_valide_et_marque_le_profil(db, tmp_path):
    profil = _setup(db)

    path = cv.generer_cv_profil(db, profil.id, out_dir=str(tmp_path))
    assert path is not None

    # Fichier PDF réel (magic bytes + lisible par pypdf).
    data = open(path, "rb").read()
    assert data[:5] == b"%PDF-"
    assert len(data) > 1000
    reader = PdfReader(path)
    assert len(reader.pages) >= 1
    texte = reader.pages[0].extract_text()
    # Le nom est rendu en capitales dans l'en-tête (style CV) ; le poste en casse d'origine.
    assert "YOUSSEF EL AMRANI" in texte
    assert "Conseiller clientèle particuliers" in texte

    # Le profil est marqué : le CV apparaît côté manager / HRBP comme un CV déposé.
    db.refresh(profil)
    assert profil.cv_filename == "CV-Youssef-El-Amrani.pdf"
    assert isinstance(profil.cv_uploaded_at, datetime)


def test_generer_cv_profil_inexistant_renvoie_none(db, tmp_path):
    assert cv.generer_cv_profil(db, 999999, out_dir=str(tmp_path)) is None


def test_generer_tous_les_cv_only_missing(db, tmp_path):
    p1 = Profil(nom="A", prenom="Un", poste_actuel="Conseiller")
    p2 = Profil(nom="B", prenom="Deux", poste_actuel="Conseiller", cv_filename="deja.pdf")
    db.add_all([p1, p2])
    db.commit()

    res = cv.generer_tous_les_cv(db, out_dir=str(tmp_path), only_missing=True)
    assert res["generes"] == 1  # p2 déjà pourvu → ignoré
    assert res["ignores"] == 1
