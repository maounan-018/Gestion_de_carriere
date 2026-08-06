#!/usr/bin/env python3
"""
services/cv_generation_service.py — Génération de CV PDF à partir des données du profil.

RÔLE
    Produit un CV PDF professionnel et déterministe pour un profil, construit à
    partir de ses données RÉELLES en base : parcours (`ProfilStation`), compétences
    détenues (`ProfilCompetence`) et projet d'évolution (aspirations / poste visé).
    Le fichier est écrit là où le contrôleur le sert (`data/cv_profil/{id}.pdf`) et
    le profil est marqué `cv_filename`/`cv_uploaded_at` → il apparaît côté manager /
    HRBP exactement comme un CV téléversé.

    Comme le contenu dérive des compétences et du parcours déjà en base, le CV reste
    COHÉRENT avec les données qu'exploitent les moteurs (reco, passerelles, inférence
    de trajectoires) : il matérialise, en document, la « data » du collaborateur.

DÉPENDANCE
    fpdf2 (pur Python, sans binaire natif). Polices « core » (Helvetica) → le texte
    est ramené à latin-1 (`_lat`) pour éviter tout embarquement de police.

EMPLACEMENT MVC
    Couche "services" : logique métier (génération de document), sans HTTP.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profil import Profil, ProfilCompetence
from app.models.carriere import ProfilStation, StationEtat

# Même répertoire que le contrôleur (surchargeable par env CV_PROFIL_DIR → isole les tests).
_CV_DIR = os.environ.get("CV_PROFIL_DIR", os.path.join("data", "cv_profil"))

# Palette BMCI (miroir de frontend/src/styles/tokens.css) — hex → (r, g, b).
GREEN = (0x00, 0x91, 0x5A)
GREEN_DEEP = (0x00, 0x78, 0x4B)
GREEN_SOFT = (0xE4, 0xF2, 0xEA)
GREEN_LINE = (0xB9, 0xDE, 0xC9)
INK = (0x0E, 0x1A, 0x14)
INK2 = (0x41, 0x50, 0x4A)
INK3 = (0x6E, 0x7C, 0x75)
GOLD = (0xB8, 0x89, 0x2E)
WARNING = (0x8A, 0x5C, 0x12)
DANGER = (0xC2, 0x3A, 0x32)
PAPER = (0xFF, 0xFF, 0xFF)

# Remplacements pour ramener un texte Unicode aux polices « core » latin-1.
_REPL = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", "•": "-",
    "œ": "oe", "Œ": "OE", " ": " ", " ": " ",
    " ": " ", "​": "",
}


def _lat(s: str | None) -> str:
    """Ramène une chaîne aux caractères représentables par les polices core (latin-1)."""
    s = "".join(_REPL.get(c, c) for c in (s or ""))
    return s.encode("latin-1", "replace").decode("latin-1")


def _niveau_color(niveau: int | None) -> tuple:
    """Couleur d'un segment de maîtrise (miroir du code couleur Lot 2 : vert/ambre/rouge)."""
    if niveau is None:
        return INK3
    pct = niveau * 20
    if pct >= 70:
        return GREEN
    if pct >= 40:
        return WARNING
    return DANGER


class _CvPdf(FPDF):
    """Gabarit CV : bandeau d'en-tête (page 1) + pied de page sur toutes les pages."""

    def __init__(self, nom: str, sous_titre: str, meta: str):
        super().__init__(format="A4", unit="mm")
        self._nom = nom
        self._sous_titre = sous_titre
        self._meta = meta
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(15, 15, 15)

    def header(self):
        if self.page_no() != 1:
            return
        self.set_fill_color(*GREEN_DEEP)
        self.rect(0, 0, self.w, 36, style="F")
        self.set_xy(15, 9)
        self.set_text_color(*PAPER)
        self.set_font("Helvetica", "B", 21)
        self.cell(self.w - 30, 9, _lat(self._nom), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_x(15)
        self.set_font("Helvetica", "", 11.5)
        self.set_text_color(0xDF, 0xF0, 0xE7)
        self.cell(self.w - 30, 6, _lat(self._sous_titre), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if self._meta:
            self.set_x(15)
            self.set_font("Helvetica", "", 8.5)
            self.set_text_color(*GREEN_LINE)
            self.cell(self.w - 30, 5, _lat(self._meta))
        self.set_y(44)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(*GREEN_LINE)
        self.set_line_width(0.2)
        self.line(15, self.get_y(), self.w - 15, self.get_y())
        self.set_y(-11)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*INK3)
        stamp = datetime.now(timezone.utc).strftime("%d/%m/%Y")
        self.cell(0, 5, _lat(f"Document généré par BMCI Carrière · {stamp}"), align="C")


def _section(pdf: _CvPdf, titre: str):
    """Titre de section vert + filet, avec un peu d'air au-dessus."""
    if pdf.get_y() > pdf.h - 40:
        pdf.add_page()
    pdf.ln(3.5)
    pdf.set_font("Helvetica", "B", 11.5)
    pdf.set_text_color(*GREEN_DEEP)
    pdf.cell(0, 6, _lat(titre.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    y = pdf.get_y() + 0.4
    pdf.set_draw_color(*GREEN_LINE)
    pdf.set_line_width(0.4)
    pdf.line(15, y, pdf.w - 15, y)
    pdf.ln(2.5)


def _collecter(db: Session, profil: Profil):
    """Rassemble parcours + compétences retenues pour le CV."""
    stations = list(db.scalars(
        select(ProfilStation)
        .where(ProfilStation.profil_id == profil.id)
        .order_by(ProfilStation.ordre)
    ).all())

    comps = list(db.scalars(
        select(ProfilCompetence).where(ProfilCompetence.profil_id == profil.id)
    ).all())
    # Dédoublonnage par libellé en conservant le meilleur niveau connu.
    best: dict[str, ProfilCompetence] = {}
    for c in comps:
        lib = (c.skill_label_fr or c.libelle or "").strip()
        if not lib:
            continue
        cur = best.get(lib.lower())
        if cur is None or (c.niveau or 0) > (cur.niveau or 0):
            best[lib.lower()] = c
    ordered = sorted(
        best.values(),
        key=lambda c: (-(c.niveau or 0), (c.skill_label_fr or c.libelle or "").lower()),
    )
    return stations, ordered


def _bloc_projet(pdf: _CvPdf, profil: Profil):
    """Encadré « Projet d'évolution » (poste visé / horizon / aspirations)."""
    lignes = []
    if profil.poste_vise:
        cible = f"Poste visé : {profil.poste_vise}"
        details = " · ".join(x for x in (profil.horizon, profil.type_evolution) if x)
        if details:
            cible += f"  ({details})"
        lignes.append(("b", cible))
    if profil.aspirations:
        lignes.append(("", profil.aspirations.strip()))
    if not lignes:
        return
    _section(pdf, "Projet d'évolution")
    y0 = pdf.get_y()
    pdf.set_fill_color(*GREEN_SOFT)
    pdf.set_draw_color(*GREEN_LINE)
    # Encadré : on mesure d'abord la hauteur du texte via un rendu, mais fpdf ne
    # le fait pas simplement ; on dessine le fond après coup à hauteur connue.
    pdf.set_xy(15, y0)
    for style, txt in lignes:
        pdf.set_font("Helvetica", "B" if style == "b" else "", 9.5)
        pdf.set_text_color(*INK if style == "b" else INK2)
        pdf.set_x(19)
        pdf.multi_cell(pdf.w - 38, 5, _lat(txt))
        pdf.ln(0.5)
    y1 = pdf.get_y()
    # Filet vertical d'accent à gauche de l'encadré.
    pdf.set_fill_color(*GREEN)
    pdf.rect(15, y0, 1.4, y1 - y0, style="F")
    pdf.ln(1)


def _bloc_parcours(pdf: _CvPdf, stations: list[ProfilStation]):
    if not stations:
        return
    _section(pdf, "Parcours professionnel")
    for st in stations:
        if pdf.get_y() > pdf.h - 34:
            pdf.add_page()
        etat = st.etat
        if etat == StationEtat.ACTUEL:
            dot = GREEN
        elif etat == StationEtat.OBJECTIF:
            dot = GOLD
        else:
            dot = INK3
        y0 = pdf.get_y()
        # Puce colorée sur la marge.
        pdf.set_fill_color(*dot)
        pdf.ellipse(15.5, y0 + 1.3, 2.6, 2.6, style="F")
        # Période (colorée) puis titre (gras) sur la même ligne.
        pdf.set_xy(21, y0)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*dot)
        pdf.cell(30, 5, _lat(st.periode))
        pdf.set_xy(52, y0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*INK)
        pdf.multi_cell(pdf.w - 15 - 52, 5, _lat(st.titre))
        if st.description:
            pdf.set_x(52)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.set_text_color(*INK2)
            pdf.multi_cell(pdf.w - 15 - 52, 4.4, _lat(st.description))
        pdf.ln(2.2)


def _bloc_competences(pdf: _CvPdf, comps: list[ProfilCompetence]):
    if not comps:
        return
    _section(pdf, "Compétences")
    comps = comps[:14]
    col_w = (pdf.w - 30 - 8) / 2          # deux colonnes avec gouttière
    bar_w = 26.0
    seg = bar_w / 5
    x_left = 15
    x_right = 15 + col_w + 8
    for i in range(0, len(comps), 2):
        if pdf.get_y() > pdf.h - 26:
            pdf.add_page()
        row_y = pdf.get_y()
        for j, x0 in ((0, x_left), (1, x_right)):
            if i + j >= len(comps):
                continue
            c = comps[i + j]
            label = (c.skill_label_fr or c.libelle or "").strip()
            label = label[:1].upper() + label[1:] if label else label   # 1re lettre en capitale (libellés ESCO minuscules)
            niveau = c.niveau
            pdf.set_xy(x0, row_y)
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*INK)
            # Libellé tronqué pour laisser la place à la barre.
            pdf.cell(col_w - bar_w - 3, 5.5, _lat(_ellipsize(pdf, label, col_w - bar_w - 4)))
            # Barre de maîtrise (5 segments).
            bx = x0 + col_w - bar_w
            by = row_y + 1.4
            filled = niveau or 0
            fill = _niveau_color(niveau)
            for s in range(5):
                if s < filled:
                    pdf.set_fill_color(*fill)
                else:
                    pdf.set_fill_color(0xE1, 0xEA, 0xE4)
                pdf.rect(bx + s * seg, by, seg - 0.8, 2.6, style="F")
            if niveau is None:
                pdf.set_xy(bx, by - 0.6)
                pdf.set_font("Helvetica", "", 6.5)
                pdf.set_text_color(*INK3)
                pdf.cell(bar_w, 4, _lat("en attente d'évaluation"))
        pdf.set_y(row_y + 7)


def _ellipsize(pdf: FPDF, text: str, max_w: float) -> str:
    """Tronque `text` avec « … » pour tenir dans `max_w` mm à la police courante."""
    text = _lat(text)
    if pdf.get_string_width(text) <= max_w:
        return text
    while text and pdf.get_string_width(text + "...") > max_w:
        text = text[:-1]
    return (text.rstrip() + "...") if text else ""


def _bloc_apropos(pdf: _CvPdf, profil: Profil):
    if not profil.bio:
        return
    _section(pdf, "À propos")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*INK2)
    pdf.set_x(15)
    pdf.multi_cell(pdf.w - 30, 5, _lat(profil.bio.strip()))


def _nom_complet(profil: Profil) -> str:
    return " ".join(x for x in (profil.prenom, profil.nom) if x).strip() or (profil.nom or "Collaborateur")


def _humaniser_dept(key: str | None) -> str | None:
    if not key:
        return None
    label = key.replace("_", " ").title()
    for acro in ("Bmci", "Pme", "Rh", "Si", "Rse", "Esg"):          # acronymes mal cassés par title()
        label = label.replace(acro, acro.upper())
    return label


def generer_cv_profil(db: Session, profil_id: int, *, out_dir: str = _CV_DIR) -> str | None:
    """Génère (ou régénère) le CV PDF du profil et le marque `cv_filename`.
    Renvoie le chemin du fichier écrit, ou None si le profil n'existe pas.
    Idempotent : réécrit le fichier à l'identique pour des données inchangées."""
    profil = db.get(Profil, profil_id)
    if profil is None:
        return None

    stations, comps = _collecter(db, profil)

    nom = _nom_complet(profil)
    sous_titre = profil.poste_actuel or "Collaborateur BMCI"
    meta_parts = []
    dept = _humaniser_dept(profil.departement_key)
    if dept:
        meta_parts.append(dept)
    if profil.matricule:
        meta_parts.append(f"Matricule {profil.matricule}")
    if profil.date_entree:
        meta_parts.append(f"Dans la banque depuis {profil.date_entree.year}")
    meta = "  ·  ".join(meta_parts)

    pdf = _CvPdf(nom, sous_titre, meta)
    pdf.set_title(_lat(f"CV - {nom}"))
    pdf.set_creator("BMCI Carrière")
    pdf.add_page()

    _bloc_projet(pdf, profil)
    _bloc_parcours(pdf, stations)
    _bloc_competences(pdf, comps)
    _bloc_apropos(pdf, profil)

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{profil_id}.pdf")
    pdf.output(path)

    # Nom d'affichage lisible côté fiche manager / HRBP.
    slug = "-".join(nom.split())
    profil.cv_filename = _lat(f"CV-{slug}.pdf")[:255]
    profil.cv_uploaded_at = datetime.now(timezone.utc)
    db.commit()
    return path


def generer_tous_les_cv(db: Session, *, out_dir: str = _CV_DIR,
                        only_missing: bool = False) -> dict:
    """Génère les CV de TOUS les profils. `only_missing` saute ceux qui ont déjà un
    `cv_filename`. Renvoie un résumé {generes, ignores}."""
    profils = list(db.scalars(select(Profil).order_by(Profil.id)).all())
    generes, ignores = 0, 0
    for p in profils:
        if only_missing and p.cv_filename:
            ignores += 1
            continue
        if generer_cv_profil(db, p.id, out_dir=out_dir):
            generes += 1
    return {"generes": generes, "ignores": ignores, "total": len(profils)}
