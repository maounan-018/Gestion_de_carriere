"""Agrège tous les modèles pour que Base.metadata connaisse toutes les tables."""

from app.models.analyse_rh import AnalyseRh
from app.models.audit_log import AuditEventType, AuditLog
from app.models.besoin import BesoinRecrutement, BesoinStatut
from app.models.candidature import Candidature, CandidatureStatut
from app.models.carriere import PeerReview, ProfilStation, StationEtat
from app.models.coach_document import CoachDocument, CoachDocumentChunk
from app.models.competence_evaluation import CompetenceEvaluation, EvaluationSource
from app.models.entretien import Entretien, EntretienStatut, EntretienType
from app.models.entretien_synthese import EntretienSynthese
from app.models.evaluation_bilan import EvaluationBilan
from app.models.fiche import Fiche, FicheCompetence, FicheSource
from app.models.formation import Formation
from app.models.notification import Notification, NotificationType
from app.models.occupation import Occupation, OccupationSkill, SkillRequirement
from app.models.offre import Offre, OffreCompetence, OffreStatut, OffreType
from app.models.profil import CompetenceSource, Profil, ProfilCompetence
from app.models.recommandation import Recommandation
from app.models.referential import ReferentialSource, SourceCode
from app.models.skill import RelationType, Skill, SkillRelation, SkillType
from app.models.skill_crosswalk import SkillCrosswalk
from app.models.skill_mapping import MappingMethod, SkillMapping
from app.models.souhait import Souhait, SouhaitKind, SouhaitStatut
from app.models.user import Role, User, UserSession, UserType

__all__ = [
    "AnalyseRh",
    "AuditEventType",
    "AuditLog",
    "Candidature",
    "CandidatureStatut",
    "CoachDocument",
    "CoachDocumentChunk",
    "CompetenceSource",
    "Entretien",
    "EntretienStatut",
    "EntretienType",
    "EvaluationBilan",
    "Fiche",
    "FicheCompetence",
    "FicheSource",
    "Formation",
    "MappingMethod",
    "Notification",
    "NotificationType",
    "Occupation",
    "OccupationSkill",
    "Offre",
    "OffreCompetence",
    "OffreStatut",
    "OffreType",
    "PeerReview",
    "Profil",
    "ProfilCompetence",
    "ProfilStation",
    "Recommandation",
    "ReferentialSource",
    "RelationType",
    "Role",
    "Skill",
    "SkillCrosswalk",
    "SkillMapping",
    "SkillRelation",
    "SkillRequirement",
    "SkillType",
    "Souhait",
    "SouhaitKind",
    "SouhaitStatut",
    "SourceCode",
    "StationEtat",
    "User",
    "UserSession",
    "UserType",
]
