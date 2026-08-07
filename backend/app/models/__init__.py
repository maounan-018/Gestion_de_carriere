"""Agrège tous les modèles pour que Base.metadata connaisse toutes les tables."""

from app.models.referential import ReferentialSource, SourceCode
from app.models.skill import Skill, SkillRelation, SkillType, RelationType
from app.models.occupation import Occupation, OccupationSkill, SkillRequirement
from app.models.skill_mapping import SkillMapping, MappingMethod
from app.models.skill_crosswalk import SkillCrosswalk
from app.models.fiche import Fiche, FicheCompetence, FicheSource
from app.models.user import User, UserSession, Role, UserType
from app.models.audit_log import AuditLog, AuditEventType
from app.models.offre import Offre, OffreCompetence, OffreType, OffreStatut
from app.models.besoin import BesoinRecrutement, BesoinStatut
from app.models.candidature import Candidature, CandidatureStatut
from app.models.profil import Profil, ProfilCompetence, CompetenceSource
from app.models.notification import Notification, NotificationType
from app.models.souhait import Souhait, SouhaitKind, SouhaitStatut
from app.models.formation import Formation
from app.models.carriere import ProfilStation, PeerReview, StationEtat
from app.models.entretien import Entretien, EntretienType, EntretienStatut
from app.models.entretien_synthese import EntretienSynthese
from app.models.competence_evaluation import CompetenceEvaluation, EvaluationSource
from app.models.evaluation_bilan import EvaluationBilan
from app.models.recommandation import Recommandation
from app.models.analyse_rh import AnalyseRh

__all__ = [
    "ReferentialSource", "SourceCode",
    "Skill", "SkillRelation", "SkillType", "RelationType",
    "Occupation", "OccupationSkill", "SkillRequirement",
    "SkillMapping", "MappingMethod",
    "SkillCrosswalk",
    "Fiche", "FicheCompetence", "FicheSource",
    "User", "UserSession", "Role", "UserType",
    "AuditLog", "AuditEventType",
    "Offre", "OffreCompetence", "OffreType", "OffreStatut",
    "Candidature", "CandidatureStatut",
    "Profil", "ProfilCompetence", "CompetenceSource",
    "Notification", "NotificationType",
    "Souhait", "SouhaitKind", "SouhaitStatut",
    "Formation",
    "ProfilStation", "PeerReview", "StationEtat",
    "Entretien", "EntretienType", "EntretienStatut",
    "EvaluationBilan",
    "Recommandation",
    "AnalyseRh",
]
