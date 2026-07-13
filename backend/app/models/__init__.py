"""Agrège tous les modèles pour que Base.metadata connaisse toutes les tables."""

from app.models.referential import ReferentialSource, SourceCode
from app.models.skill import Skill, SkillRelation, SkillType, RelationType
from app.models.occupation import Occupation, OccupationSkill, SkillRequirement
from app.models.skill_mapping import SkillMapping, MappingMethod
from app.models.skill_crosswalk import SkillCrosswalk

__all__ = [
    "ReferentialSource", "SourceCode",
    "Skill", "SkillRelation", "SkillType", "RelationType",
    "Occupation", "OccupationSkill", "SkillRequirement",
    "SkillMapping", "MappingMethod",
    "SkillCrosswalk",
]
