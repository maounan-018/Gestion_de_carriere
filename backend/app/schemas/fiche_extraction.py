#!/usr/bin/env python3
"""
schemas/fiche_extraction.py — Contrats d'entrée/sortie de l'extraction de FICHE DE POSTE.

RÔLE
    Forme exacte des données échangées : en entrée, les rubriques de la fiche (selon
    le gabarit éditable) ; en sortie, les métadonnées du poste + les compétences
    TYPÉES (catégorie déclarée par la fiche) et ANCRÉES au graphe, réexploitables
    par le matching et les recommandations. Expose aussi le gabarit (typologie).

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic), sans logique métier.
"""

from pydantic import BaseModel, Field

from app.schemas.skill_extraction import MatchedSkill


class FicheRequest(BaseModel):
    sections: dict[str, str] = Field(
        ..., description="Rubriques de la fiche : clé de section (gabarit) -> texte.")
    top_k: int = Field(1, ge=1, le=5,
                       description="Nombre de compétences canoniques rapprochées par compétence.")


class FicheCompetence(BaseModel):
    libelle: str = Field(..., description="Compétence telle que lue/extraite de la fiche.")
    categorie: str | None = Field(None, description="metier | comportementale | transversale | outil_technologie")
    source_section: str = Field(..., description="Rubrique d'origine (clé du gabarit).")
    implicite: bool = Field(False, description="True = déduite d'un texte libre (mission/activités).")
    matches: list[MatchedSkill] = Field(default_factory=list,
                                        description="Compétences canoniques du graphe rapprochées.")


class Langue(BaseModel):
    langue: str
    niveau: str | None = None


class FicheResponse(BaseModel):
    poste: dict[str, str] = Field(default_factory=dict, description="Métadonnées (famille, périmètre, code, intitulé…).")
    competences: list[FicheCompetence]
    langues: list[Langue] = Field(default_factory=list)
    indicateurs_performance: list[str] = Field(default_factory=list)


# ---- Gabarit (typologie éditable) ----

class GabaritSection(BaseModel):
    key: str
    label: str
    kind: str = Field(..., description="metadata | freetext | skill_list | languages | kpi")
    categorie: str | None = None
    aide: str | None = None


class GabaritResponse(BaseModel):
    version: int | None = None
    sections: list[GabaritSection]


# ---- Cartographie & génération de fiche ----

class DepartementInfo(BaseModel):
    key: str
    nom: str
    pole: str | None = None
    metiers: list[str] = Field(default_factory=list)


class FicheGenerationRequest(BaseModel):
    metier: str = Field(..., min_length=2, description="Intitulé du métier à générer.")
    departement_key: str = Field(..., description="Clé de département (cartographie).")


class FicheGeneree(BaseModel):
    metier: str
    departement: str
    synthetique: bool = Field(True, description="Contenu généré (jamais des données réelles).")
    sections: dict[str, str] = Field(..., description="Fiche au format du gabarit.")
    competences_reference: list[str] = Field(default_factory=list,
                                             description="Compétences du graphe ayant ancré la génération.")
