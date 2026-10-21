#!/usr/bin/env python3
"""
models/coach_document.py — Documents personnels téléversés par un utilisateur
pour enrichir SON Coach Carrière (CV, fiches, notes…).

RÔLE
    Base de connaissances PERSONNELLE par utilisateur (RAG). Un document :
      - est rattaché à un compte (`uploaded_by` → users.id, isolation stricte) ;
      - est découpé en chunks (`CoachDocumentChunk`) + embeddings (vec0 /
        pgvector dans `vec_coach_docs`, clé = chunk.id) pour la recherche
        sémantique à chaque message du coach.

SÉCURITÉ / CNDP
    Isolation par propriétaire : le coach d'un utilisateur n'a jamais accès aux
    documents d'un autre (filtre `uploaded_by` partout). Tout reste local
    (texte + vecteurs + LLM Ollama). FK CASCADE pour la suppression propre.

EMPLACEMENT MVC
    Couche "models" : entités ORM.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class CoachDocument(Base):
    """Document téléversé par un utilisateur pour son Coach (CV, notes, fiche…)."""

    __tablename__ = "coach_documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    # Taille originale du fichier en octets (pour affichage dans la liste UI).
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Nombre de chunks indexés (dénormalisé pour éviter un COUNT à chaque listing).
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), nullable=False
    )

    chunks: Mapped[list["CoachDocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        # Listing « mes documents » trié par date : index composite utile.
        Index("ix_coach_documents_user_created", "uploaded_by", "created_at"),
    )


class CoachDocumentChunk(Base):
    """Fragment textuel d'un document (unité d'indexation vectorielle)."""

    __tablename__ = "coach_document_chunks"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True
    )  # = rowid pour vec_coach_docs
    document_id: Mapped[int] = mapped_column(
        ForeignKey("coach_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    document: Mapped["CoachDocument"] = relationship(back_populates="chunks")
