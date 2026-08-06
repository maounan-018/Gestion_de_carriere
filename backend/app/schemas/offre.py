#!/usr/bin/env python3
"""
schemas/offre.py — Contrats d'entrée/sortie d'une Offre (dérivée d'une Fiche).

RÔLE
    Forme des données d'une opportunité à pourvoir (offre de poste RH, ou
    mission/projet/gig manager) et de ses ATTENDUS overridables. À la création,
    si une `fiche_id` de référence est fournie, les compétences de la Fiche sont
    COPIÉES en attendus (`source="fiche"`) puis éditables au niveau de l'offre —
    la Fiche de référence, elle, n'est jamais modifiée.

    Le `score` d'une candidature s'évalue contre ces attendus (cf. candidature).

EMPLACEMENT MVC
    Couche "schemas" : validation/sérialisation (Pydantic).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Miroirs des constantes de models.offre (validation d'entrée).
TypeOffre = Literal["offre_poste", "mission", "projet", "gig"]
StatutOffre = Literal["brouillon", "ouverte", "pourvue", "fermee", "annulee"]
Importance = Literal["essentielle", "souhaitee"]
SourceComp = Literal["fiche", "ajout_offre"]


class OffreCompetenceIn(BaseModel):
    libelle: str = Field(..., min_length=1, max_length=300)
    categorie: str | None = Field(None, max_length=24,
                                  description="metier | comportementale | transversale | outil_technologie")
    skill_id: int | None = Field(None, description="Ancrage graphe (compétence canonique ESCO/O*NET/SFIA).")
    skill_label_fr: str | None = Field(None, max_length=300)
    importance: Importance = Field("essentielle", description="essentielle (bloquante) | souhaitee (bonus).")
    niveau_requis: int | None = Field(None, ge=1, le=5, description="Niveau requis 1-5 (aligné SFIA).")
    source: SourceComp = Field("ajout_offre", description="fiche (héritée) | ajout_offre (ajoutée au niveau offre).")


class OffreCompetenceOut(OffreCompetenceIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    rerank_score: float | None = None


class OffreCompetenceUpdate(BaseModel):
    """Override d'un attendu au niveau de l'offre (partiel, champs non-None seulement)."""
    libelle: str | None = Field(None, min_length=1, max_length=300)
    categorie: str | None = None
    importance: Importance | None = None
    niveau_requis: int | None = Field(None, ge=1, le=5)


class OffreCreate(BaseModel):
    titre: str = Field(..., min_length=1, max_length=200)
    fiche_id: int | None = Field(None, description="Fiche de référence dont dérive l'offre (attendus copiés).")
    heriter_competences: bool = Field(True, description="Copier les compétences de la Fiche comme attendus (si fiche_id).")
    type: TypeOffre = "offre_poste"
    description: str | None = None
    localisation: str | None = Field(None, max_length=120, description="Ville / site.")
    duree: str | None = Field(None, max_length=64, description="Durée (mission/projet), ex : « 6 mois ».")
    perimetre_bmci: str | None = Field(None, max_length=160)
    departement_key: str | None = Field(None, max_length=48)
    statut: StatutOffre = "brouillon"
    created_by: int | None = Field(None, description="Utilisateur qui pousse l'offre (RH ou manager).")
    manager_id: int | None = Field(None, description="Manager concerné (notification).")
    date_ouverture: datetime | None = None
    date_cloture: datetime | None = None
    synthetique: bool = Field(False, description="True = donnée de démonstration fabriquée (à étiqueter).")
    competences: list[OffreCompetenceIn] = Field(
        default_factory=list,
        description="Attendus ajoutés explicitement (en plus de ceux hérités de la Fiche).")


class OffreUpdate(BaseModel):
    """Mise à jour partielle de l'offre (jamais la Fiche de référence)."""
    titre: str | None = Field(None, min_length=1, max_length=200)
    type: TypeOffre | None = None
    description: str | None = None
    perimetre_bmci: str | None = Field(None, max_length=160)
    departement_key: str | None = Field(None, max_length=48)
    statut: StatutOffre | None = Field(None, description="Transition de statut (dates ouverture/clôture posées auto).")
    manager_id: int | None = None
    date_ouverture: datetime | None = None
    date_cloture: datetime | None = None


class OffreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fiche_id: int | None
    type: str
    titre: str
    description: str | None
    localisation: str | None = None
    duree: str | None = None
    perimetre_bmci: str | None
    departement_key: str | None
    statut: str
    created_by: int | None
    manager_id: int | None
    date_ouverture: datetime | None
    date_cloture: datetime | None
    synthetique: bool
    created_at: datetime
    competences: list[OffreCompetenceOut] = Field(default_factory=list)


class OffreCompatOut(BaseModel):
    """Offre + compatibilité calculée POUR UN PROFIL donné (écran offres du
    collaborateur). `score_compat` = score d'évaluation (0-100) du profil vs les
    attendus ; `couvertes`/`ecarts` = compte des compétences. Compétences = libellés."""
    id: int
    type: str
    titre: str
    description: str | None
    perimetre_bmci: str | None
    departement_key: str | None
    statut: str
    competences: list[str] = Field(default_factory=list)
    score_compat: int | None = None
    couvertes: int = 0
    ecarts: int = 0


class OffreCandidatOut(BaseModel):
    """Candidat à une offre (écran RH « revue des candidatures »). Le score et les
    compétences couvertes/écarts proviennent du snapshot d'évaluation de la
    candidature ; l'identité vient du profil."""
    profil_id: int
    candidature_id: int
    nom: str
    prenom: str | None
    poste_actuel: str | None
    departement_key: str | None
    score: float | None
    statut: str                              # statut de la candidature (deposee/retenue/…)
    couvertes: list[str] = Field(default_factory=list)  # libellés des compétences couvertes
    ecarts: list[str] = Field(default_factory=list)     # libellés des écarts


class RhOffreOut(BaseModel):
    """Offre vue côté RH, avec les statistiques de candidatures (liste RH + revue)."""
    id: int
    titre: str
    type: str
    departement_key: str | None
    perimetre_bmci: str | None
    statut: str
    candidats_total: int = 0
    candidats_compatibles: int = 0          # au-dessus du seuil de compatibilité
    retenu_nom: str | None = None           # nom du candidat retenu, s'il y en a un


class VacancyRecoOut(BaseModel):
    """Profil interne recommandé pour un poste (MATCHING INVERSE : le poste évalué
    contre les compétences détenues d'un membre de l'équipe). `score` réutilise
    l'évaluateur des candidatures ; matched/gaps = compétences couvertes/écarts."""
    profil_id: int
    nom: str
    prenom: str | None
    poste_actuel: str | None
    score: int
    matched: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class VacancyOut(BaseModel):
    """Poste à pourvoir de l'équipe d'un manager + profils internes recommandés."""
    id: int
    titre: str
    type: str
    departement_key: str | None
    perimetre_bmci: str | None
    description: str | None
    statut: str
    created_at: datetime
    recos: list[VacancyRecoOut] = Field(default_factory=list)


# --- Évaluation de MISSION (post-clôture) : le manager note les compétences
#     utilisées par les participants RETENUS (Workstream C). ------------------
class MissionParticipantOut(BaseModel):
    profil_id: int
    nom: str
    poste_actuel: str | None = None


class MissionExpectedComp(BaseModel):
    libelle: str
    skill_id: int | None = None
    importance: str = "essentielle"


class MissionEvalContextOut(BaseModel):
    """Contexte d'évaluation d'une mission : l'offre, ses compétences attendues et
    ses participants retenus — tout ce qu'il faut pour l'écran d'évaluation manager."""
    offre_id: int
    titre: str
    type: str
    statut: str
    competences: list[MissionExpectedComp] = Field(default_factory=list)
    participants: list[MissionParticipantOut] = Field(default_factory=list)


class MissionCompetenceScore(BaseModel):
    libelle: str = Field(..., min_length=1, max_length=300)
    skill_id: int | None = None
    categorie: str | None = None
    score: int = Field(..., ge=1, le=10)


class MissionEvaluationIn(BaseModel):
    competences: list[MissionCompetenceScore] = Field(default_factory=list)


class MissionEvaluationOut(BaseModel):
    evaluees: int
    ajoutees: int
