#!/usr/bin/env python3
"""
services/cv_generation_service.py — Génération de CV PDF à partir des données du profil.

RÔLE
    Produit un CV PDF SOBRE, ESSENTIELLEMENT TEXTE (pas de bandeaux colorés ni de
    barres/segments), sur le modèle des CV classiques : en-tête (nom, intitulé de
    poste, contact) puis sections en capitales — EXPÉRIENCE PROFESSIONNELLE,
    FORMATION, COMPÉTENCES, PROJET D'ÉVOLUTION.

    Le FOND dérive des données RÉELLES en base (parcours `ProfilStation`,
    compétences `ProfilCompetence`, poste visé / aspirations) → le CV reste
    COHÉRENT avec ce qu'exploitent les moteurs (reco, passerelles, inférence de
    trajectoires). Les éléments non stockés (formation, e-mail, téléphone,
    langues) sont SYNTHÉTIQUES mais DÉTERMINISTES par profil (seed = id), et le
    document est explicitement marqué « données synthétiques » en pied de page.

DÉPENDANCE
    fpdf2 (pur Python). Polices « core » (Helvetica) → texte ramené à latin-1.

EMPLACEMENT MVC
    Couche "services" : logique métier (génération de document), sans HTTP.
"""

from __future__ import annotations

import os
import random
import unicodedata
from datetime import UTC, datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.carriere import ProfilStation, StationEtat
from app.models.profil import Profil, ProfilCompetence

# Même répertoire que le contrôleur (surchargeable par env CV_PROFIL_DIR → isole les tests).
_CV_DIR = os.environ.get("CV_PROFIL_DIR", os.path.join("data", "cv_profil"))

# Palette sobre : encre (noir), gris, filets clairs. Aucun aplat de couleur.
INK = (0x1A, 0x1A, 0x1A)
GREY = (0x55, 0x55, 0x55)
GREY_LIGHT = (0x8A, 0x8A, 0x8A)
RULE = (0xBB, 0xBB, 0xBB)

_REPL = {
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
    "–": "-",
    "—": "-",
    "…": "...",
    "•": "-",
    "·": "-",
    "œ": "oe",
    "Œ": "OE",
    " ": " ",
    " ": " ",
    " ": " ",
    "​": "",
}


def _lat(s: str | None) -> str:
    """Ramène une chaîne aux caractères représentables par les polices core (latin-1)."""
    s = "".join(_REPL.get(c, c) for c in (s or ""))
    return s.encode("latin-1", "replace").decode("latin-1")


def _cap(s: str) -> str:
    """Première lettre en capitale (les libellés ESCO sont en minuscules)."""
    s = (s or "").strip()
    return (s[:1].upper() + s[1:]) if s else s


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)
    )


# ---------------------------------------------------------------- Éléments synthétiques

_ECOLES = [
    ("ISCAE", "Casablanca"),
    ("ENCG", "Settat"),
    ("ENCG", "Casablanca"),
    ("ENCG", "Tanger"),
    ("Université Hassan II", "Casablanca"),
    ("Université Mohammed V", "Rabat"),
    ("HEM Business School", "Casablanca"),
    ("Al Akhawayn University", "Ifrane"),
    ("EMI - École Mohammadia d'Ingénieurs", "Rabat"),
    ("ENSIAS", "Rabat"),
    ("INPT", "Rabat"),
    ("ENSA", "Marrakech"),
    ("Toulouse Business School", "Casablanca"),
    ("FSJES", "Casablanca"),
]
_MENTIONS = [
    "Mention Bien",
    "Mention Très Bien",
    "Mention Assez Bien",
    "Major de promotion",
    "",
    "",
]
_DIPLOMES_DEFAUT = [
    "Master en Management (Bac+5)",
    "Master Économie & Gestion",
    "Master Sciences de Gestion",
    "Diplôme de l'ESC (Grande École)",
]
_DIPLOMES_PAR_FAMILLE = {
    "risque": [
        "Master Gestion des Risques & Contrôle",
        "Master Finance de Marché",
        "Diplôme d'Ingénieur - Ingénierie Financière",
    ],
    "finance": [
        "Master Finance d'Entreprise",
        "Master Comptabilité, Contrôle, Audit",
        "Diplôme d'Expertise Comptable (en cours)",
    ],
    "it": [
        "Diplôme d'Ingénieur en Informatique",
        "Master Ingénierie des Systèmes d'Information",
        "Master Data Science & Big Data",
    ],
    "rh": ["Master Management des Ressources Humaines", "Master Gestion des Talents"],
    "corporate": [
        "Master Finance d'Entreprise",
        "Master Management (Grande École)",
        "Diplôme d'Ingénieur Financier",
    ],
    "conformite": ["Master Droit des Affaires", "Master Conformité & Contrôle Interne"],
}


def _famille_diplome(dept_key: str | None, poste: str | None) -> str | None:
    txt = f"{dept_key or ''} {poste or ''}".lower()
    for fam, keys in {
        "risque": ("risque", "risk"),
        "conformite": ("conformite", "conform", "compliance", "kyc", "lcb"),
        "it": ("si", "informatique", "data", "digital", "tech", "systeme"),
        "rh": ("ressources_humaines", "rh", "talent", "hrbp"),
        "finance": ("finance", "comptab", "controle", "audit", "reporting"),
        "corporate": ("corporate", "entreprise", "financement", "investissement", "affaires"),
    }.items():
        if any(k in txt for k in keys):
            return fam
    return None


def _annee_diplome(profil: Profil, stations: list[ProfilStation], rng: random.Random) -> int:
    """Année de diplôme plausible : quelques années avant l'entrée / le 1er poste."""
    base = None
    if getattr(profil, "date_entree", None):
        base = profil.date_entree.year
    else:
        for st in stations:
            for tok in (st.periode or "").replace("-", " ").split():
                if tok.isdigit() and 1980 <= int(tok) <= 2100:
                    base = int(tok)
                    break
            if base:
                break
    base = base or 2016
    return max(1995, base - rng.randint(0, 2))


def _contact(profil: Profil, rng: random.Random) -> tuple[str, str]:
    prenom = _strip_accents(profil.prenom or "").lower().replace(" ", "").replace("'", "")
    nom = _strip_accents(profil.nom or "").lower().replace(" ", "").replace("'", "")
    email = f"{prenom}.{nom}@bmci.local" if (prenom or nom) else "collaborateur@bmci.local"
    tel = f"+212 6 {rng.randint(0, 99):02d} {rng.randint(0, 99):02d} {rng.randint(0, 99):02d} {rng.randint(0, 99):02d}"
    return email, tel


def _langues(rng: random.Random) -> str:
    parts = [
        "Arabe (langue maternelle)",
        "Français ({})".format(rng.choice(["courant", "bilingue", "langue maternelle"])),
        "Anglais ({})".format(
            rng.choice(["courant", "professionnel", "intermédiaire", "B2", "C1"])
        ),
    ]
    if rng.random() < 0.35:
        parts.append("Espagnol ({})".format(rng.choice(["notions", "B1", "intermédiaire"])))
    return ", ".join(parts)


# ---------------------------------------------------------------- Gabarit PDF (sobre)


class _CvPdf(FPDF):
    def __init__(self):
        super().__init__(format="A4", unit="mm")
        self.set_auto_page_break(auto=True, margin=16)
        self.set_margins(18, 16, 18)

    def footer(self):
        self.set_y(-13)
        self.set_draw_color(*RULE)
        self.set_line_width(0.2)
        self.line(18, self.get_y(), self.w - 18, self.get_y())
        self.set_y(-10.5)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*GREY_LIGHT)
        stamp = datetime.now(UTC).strftime("%d/%m/%Y")
        self.cell(
            0,
            5,
            _lat(f"Document de démonstration - données synthétiques - BMCI Carrière - {stamp}"),
            align="C",
        )


def _txt_w(pdf: _CvPdf) -> float:
    return pdf.w - pdf.l_margin - pdf.r_margin


def _section(pdf: _CvPdf, titre: str):
    if pdf.get_y() > pdf.h - 34:
        pdf.add_page()
    pdf.ln(3.2)
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*INK)
    pdf.cell(0, 5.5, _lat(titre.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    y = pdf.get_y() + 0.3
    pdf.set_draw_color(*RULE)
    pdf.set_line_width(0.3)
    pdf.line(18, y, pdf.w - 18, y)
    pdf.ln(2.2)


def _entete(pdf: _CvPdf, nom: str, poste: str, contact: str, meta: str):
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*INK)
    pdf.cell(0, 8.5, _lat(nom.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if poste:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(*GREY)
        pdf.cell(0, 5.6, _lat(poste), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 8.7)
    pdf.set_text_color(*GREY)
    pdf.cell(0, 5, _lat(contact), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    if meta:
        pdf.set_text_color(*GREY_LIGHT)
        pdf.cell(0, 4.6, _lat(meta), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    y = pdf.get_y() + 1.4
    pdf.set_draw_color(*INK)
    pdf.set_line_width(0.5)
    pdf.line(18, y, pdf.w - 18, y)
    pdf.ln(2.6)


def _est_formation(st: ProfilStation) -> bool:
    """Une station de FORMATION initiale (marquée par le seed), à router vers la
    section Formation plutôt que vers l'expérience professionnelle."""
    return "formation initiale" in (st.description or "").lower()


def _clean_edu_titre(t: str) -> str:
    """Retire un suffixe « – diplômé-e / – obtention du diplôme » du titre de
    formation (tout type de tiret)."""
    t = (t or "").strip()
    norm = t.replace("–", "-").replace("—", "-")
    if " - " in norm:
        head, tail = norm.rsplit(" - ", 1)
        if "diplôm" in tail.lower() or "diplom" in tail.lower():
            return head.strip()
    return t


def _experience(pdf: _CvPdf, profil: Profil, stations: list[ProfilStation]):
    # Postes RÉELLEMENT occupés (on exclut l'objectif = projet, et la formation
    # initiale = section Formation), en ordre anté-chronologique (plus récent d'abord).
    postes = [s for s in stations if s.etat != StationEtat.OBJECTIF and not _est_formation(s)]
    postes = sorted(postes, key=lambda s: s.ordre, reverse=True)
    if not postes:
        return
    _section(pdf, "Expérience professionnelle")
    w = _txt_w(pdf)
    for st in postes:
        if pdf.get_y() > pdf.h - 26:
            pdf.add_page()
        actuel = st.etat == StationEtat.ACTUEL
        # Ligne titre (gras) + période (grise, alignée à droite).
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*INK)
        titre = st.titre + ("  (poste actuel)" if actuel else "")
        pdf.cell(w * 0.72, 5.4, _lat(titre))
        pdf.set_font("Helvetica", "", 8.7)
        pdf.set_text_color(*GREY)
        pdf.cell(
            w * 0.28, 5.4, _lat(st.periode or ""), align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )
        if st.description:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*GREY)
            pdf.multi_cell(w, 4.5, _lat(st.description.strip()))
        pdf.ln(2.0)


def _formation(pdf: _CvPdf, profil: Profil, stations: list[ProfilStation], rng: random.Random):
    _section(pdf, "Formation")
    w = _txt_w(pdf)
    edu = sorted((s for s in stations if _est_formation(s)), key=lambda s: s.ordre, reverse=True)
    if edu:
        # Formation RÉELLE issue du parcours (cohérente avec le reste de la plateforme).
        for st in edu:
            pdf.set_font("Helvetica", "B", 9.7)
            pdf.set_text_color(*INK)
            pdf.cell(w * 0.78, 5.2, _lat(_clean_edu_titre(st.titre)))
            pdf.set_font("Helvetica", "", 8.7)
            pdf.set_text_color(*GREY)
            pdf.cell(
                w * 0.22,
                5.2,
                _lat(st.periode or ""),
                align="R",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            pdf.ln(0.8)
        return
    # Aucune formation en base → entrée SYNTHÉTIQUE déterministe.
    (ecole, ville) = rng.choice(_ECOLES)
    annee = _annee_diplome(profil, stations, rng)
    fam = _famille_diplome(profil.departement_key, profil.poste_actuel)
    diplome = rng.choice(_DIPLOMES_PAR_FAMILLE.get(fam, _DIPLOMES_DEFAUT))
    mention = rng.choice(_MENTIONS)
    pdf.set_font("Helvetica", "B", 9.7)
    pdf.set_text_color(*INK)
    pdf.cell(w * 0.72, 5.2, _lat(f"{ecole} - {ville}"))
    pdf.set_font("Helvetica", "", 8.7)
    pdf.set_text_color(*GREY)
    pdf.cell(
        w * 0.28,
        5.2,
        _lat(f"{annee - rng.randint(3, 5)} - {annee}"),
        align="R",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GREY)
    ligne = diplome + (f"  |  {mention}" if mention else "")
    pdf.multi_cell(w, 4.6, _lat(ligne))
    pdf.ln(0.6)


_CAT_LABEL = {
    "metier": "Métier",
    "métier": "Métier",
    "business": "Métier",
    "outil_technologie": "Outils & technologies",
    "outils": "Outils & technologies",
    "outil": "Outils & technologies",
    "technique": "Outils & technologies",
    "tech": "Outils & technologies",
    "technologie": "Outils & technologies",
    "digital": "Outils & technologies",
    "data": "Data & analyse",
    "transversale": "Compétences transverses",
    "transversal": "Compétences transverses",
    "leadership": "Leadership & management",
    "management": "Leadership & management",
    "comportementale": "Comportementales",
    "comportemental": "Comportementales",
    "comportement": "Comportementales",
    "soft": "Comportementales",
    "langue": "Langues",
    "langues": "Langues",
}
_CAT_ORDER = [
    "Métier",
    "Outils & technologies",
    "Data & analyse",
    "Compétences transverses",
    "Leadership & management",
    "Comportementales",
    "Autres compétences",
]


def _competences(pdf: _CvPdf, comps: list[ProfilCompetence], rng: random.Random):
    _section(pdf, "Compétences")
    groupes: dict[str, list[str]] = {}
    for c in comps[:26]:
        label = _cap(_comp_label(c))
        if not label:
            continue
        cat = _CAT_LABEL.get(
            (getattr(c, "categorie", None) or "").strip().lower(), "Autres compétences"
        )
        groupes.setdefault(cat, [])
        if label not in groupes[cat]:
            groupes[cat].append(label)
    w = _txt_w(pdf)
    ordered = [c for c in _CAT_ORDER if c in groupes] + [c for c in groupes if c not in _CAT_ORDER]
    for cat in ordered:
        libs = groupes[cat]
        if not libs:
            continue
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(*INK)
        pdf.cell(0, 4.8, _lat(cat), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*GREY)
        pdf.multi_cell(w, 4.6, _lat(", ".join(libs)))
        pdf.ln(1.2)
    # Langues (synthétiques, déterministes).
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*INK)
    pdf.cell(0, 4.8, _lat("Langues"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GREY)
    pdf.multi_cell(w, 4.6, _lat(_langues(rng)))


def _projet(pdf: _CvPdf, profil: Profil):
    lignes = []
    if getattr(profil, "poste_vise", None):
        details = " - ".join(
            x
            for x in (getattr(profil, "horizon", None), getattr(profil, "type_evolution", None))
            if x
        )
        cible = f"Poste visé : {profil.poste_vise}" + (f"  ({details})" if details else "")
        lignes.append(cible)
    if getattr(profil, "aspirations", None):
        lignes.append(profil.aspirations.strip())
    if not lignes:
        return
    _section(pdf, "Projet d'évolution")
    w = _txt_w(pdf)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GREY)
    for txt in lignes:
        pdf.multi_cell(w, 4.6, _lat(txt))
        pdf.ln(0.6)


# ---------------------------------------------------------------- Collecte & API


def _comp_label(c: ProfilCompetence) -> str:
    """Libellé d'affichage : le libellé DÉCLARÉ (naturel, ex. « Veille réglementaire »)
    est préféré au libellé canonique ESCO (verbeux, ex. « suivre l'évolution de la
    législation »)."""
    return (c.libelle or c.skill_label_fr or "").strip()


def _collecter(db: Session, profil: Profil):
    stations = list(
        db.scalars(
            select(ProfilStation)
            .where(ProfilStation.profil_id == profil.id)
            .order_by(ProfilStation.ordre)
        ).all()
    )
    comps = list(
        db.scalars(select(ProfilCompetence).where(ProfilCompetence.profil_id == profil.id)).all()
    )
    poste_l = (profil.poste_actuel or "").strip().lower()
    # Dédoublonnage par libellé (naturel) en conservant le meilleur niveau connu ;
    # on écarte toute « compétence » égale à l'intitulé de poste (pseudo-compétence).
    best: dict[str, ProfilCompetence] = {}
    for c in comps:
        lib = _comp_label(c)
        if not lib or lib.lower() == poste_l:
            continue
        cur = best.get(lib.lower())
        if cur is None or (c.niveau or 0) > (cur.niveau or 0):
            best[lib.lower()] = c
    ordered = sorted(best.values(), key=lambda c: (-(c.niveau or 0), _comp_label(c).lower()))
    return stations, ordered


def _nom_complet(profil: Profil) -> str:
    return " ".join(x for x in (profil.prenom, profil.nom) if x).strip() or (
        profil.nom or "Collaborateur"
    )


def _humaniser_dept(key: str | None) -> str | None:
    if not key:
        return None
    label = key.replace("_", " ").title()
    for acro in ("Bmci", "Pme", "Rh", "Si", "Rse", "Esg"):
        label = label.replace(acro, acro.upper())
    return label


def generer_cv_profil(db: Session, profil_id: int, *, out_dir: str = _CV_DIR) -> str | None:
    """Génère (ou régénère) le CV PDF SOBRE du profil et le marque `cv_filename`.
    Renvoie le chemin du fichier écrit, ou None si le profil n'existe pas.
    Déterministe (seed = id) : mêmes données → même document."""
    profil = db.get(Profil, profil_id)
    if profil is None:
        return None

    rng = random.Random(profil_id)
    stations, comps = _collecter(db, profil)

    nom = _nom_complet(profil)
    poste = profil.poste_actuel or "Collaborateur BMCI"
    email, tel = _contact(profil, rng)
    contact = f"{email}   |   {tel}"
    meta_parts = []
    dept = _humaniser_dept(profil.departement_key)
    if dept:
        meta_parts.append(dept)
    if profil.matricule:
        meta_parts.append(f"Matricule {profil.matricule}")
    if getattr(profil, "date_entree", None):
        meta_parts.append(f"Chez BMCI depuis {profil.date_entree.year}")
    meta = "   -   ".join(meta_parts)

    pdf = _CvPdf()
    pdf.set_title(_lat(f"CV - {nom}"))
    pdf.set_creator("BMCI Carriere")
    pdf.add_page()

    _entete(pdf, nom, poste, contact, meta)
    _experience(pdf, profil, stations)
    _formation(pdf, profil, stations, rng)
    if comps:
        _competences(pdf, comps, rng)
    _projet(pdf, profil)

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{profil_id}.pdf")
    pdf.output(path)

    slug = "-".join(nom.split())
    profil.cv_filename = _lat(f"CV-{slug}.pdf")[:255]
    profil.cv_uploaded_at = datetime.now(UTC)
    db.commit()
    return path


def generer_tous_les_cv(db: Session, *, out_dir: str = _CV_DIR, only_missing: bool = False) -> dict:
    """Génère les CV de TOUS les profils. `only_missing` saute ceux qui ont déjà un
    `cv_filename`. Renvoie un résumé {generes, ignores, total}."""
    profils = list(db.scalars(select(Profil).order_by(Profil.id)).all())
    generes, ignores = 0, 0
    for p in profils:
        if only_missing and p.cv_filename:
            ignores += 1
            continue
        if generer_cv_profil(db, p.id, out_dir=out_dir):
            generes += 1
    return {"generes": generes, "ignores": ignores, "total": len(profils)}
