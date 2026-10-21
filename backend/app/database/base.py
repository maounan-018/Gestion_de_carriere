#!/usr/bin/env python3
"""
database/base.py — Base déclarative SQLAlchemy 2.0.

RÔLE
    Déclare la classe de base ORM dont héritent tous les modèles. Un seul point
    d'import pour `Base`, afin que `Base.metadata` connaisse toutes les tables.

EMPLACEMENT MVC
    Couche "database" : fondations de la persistance.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base déclarative commune à tous les modèles ORM."""

    pass
