#!/usr/bin/env python3
"""
services/coach_rag_service.py — Base de connaissances PERSONNELLE du Coach (RAG).

RÔLE
    Ingestion / recherche / gestion des documents que CHAQUE utilisateur téléverse
    pour enrichir SON Coach Carrière (CV, fiche de poste, notes…). Isolation
    stricte : le filtre `uploaded_by = user_id` est appliqué partout — un
    utilisateur n'accède JAMAIS aux documents d'un autre.

PIPELINE
    - `ingest(db, user_id, filename, text)` : chunking par caractères + embeddings
      par lots (bge-m3) + stockage dans `coach_documents` / `coach_document_chunks`
      et dans la table vectorielle `vec_coach_docs` (vec0 ou pgvector).
    - `retrieve(db, user_id, query, top_k, max_distance)` : KNN sémantique
      restreint aux chunks dont le document appartient à `user_id`.
    - `list_documents(db, user_id)` / `delete_document(db, user_id, doc_id)` :
      vue et retrait depuis l'UI, 404 propre si l'utilisateur n'est pas propriétaire.

SÉCURITÉ / CNDP
    100 % local : extraction, embeddings et stockage restent sur la machine.
    FK CASCADE : la suppression d'un document supprime chunks + vecteurs d'un bloc.

EMPLACEMENT MVC
    Couche "services" : orchestration RAG, sans route HTTP.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.vector_search import knn_sql
from app.models.coach_document import CoachDocument, CoachDocumentChunk
from app.services.embedding_service import embed_batch, embed_text

logger = logging.getLogger(__name__)

# Chunking : taille volontairement modeste pour un rappel sémantique précis
# (bge-m3 → 1024 dim, qualité par chunk >>> volume). Overlap pour ne pas couper
# une idée en deux à la frontière.
_CHUNK_CHARS = 1000
_CHUNK_OVERLAP = 150


# ================================================================= Chunking


def _chunk_text(
    content: str, max_chars: int = _CHUNK_CHARS, overlap: int = _CHUNK_OVERLAP
) -> list[str]:
    """Découpe `content` en fragments ≤ max_chars, avec recouvrement, en coupant
    de préférence sur une frontière de paragraphe/phrase (meilleur que couper au
    milieu d'un mot). Fragments vides filtrés."""
    text_in = (content or "").strip()
    if not text_in:
        return []

    chunks: list[str] = []
    cursor = 0
    n = len(text_in)
    while cursor < n:
        end = min(cursor + max_chars, n)
        # Coupe sur le dernier \n\n ou . dans la dernière moitié du chunk
        # (évite d'arracher une phrase courante).
        if end < n:
            window_start = cursor + max_chars // 2
            cut = max(
                text_in.rfind("\n\n", window_start, end),
                text_in.rfind(". ", window_start, end),
                text_in.rfind("\n", window_start, end),
            )
            if cut != -1 and cut > cursor:
                end = cut + 1
        piece = text_in[cursor:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        cursor = max(end - overlap, cursor + 1)
    return chunks


# ================================================================= Ingestion


def ingest(
    db: Session, user_id: int, filename: str, text_content: str, size_bytes: int = 0
) -> CoachDocument:
    """Indexe un document pour l'utilisateur : CoachDocument + chunks + vecteurs.
    Lève ValueError si rien n'est exploitable (texte vide après chunking)."""
    chunks = _chunk_text(text_content)
    if not chunks:
        raise ValueError("Aucun fragment exploitable n'a pu être extrait du document.")

    vectors = embed_batch(chunks)  # repli adaptatif intégré au service
    if len(vectors) != len(chunks):
        raise RuntimeError("Nombre d'embeddings reçus ≠ nombre de chunks (anomalie).")

    doc = CoachDocument(
        uploaded_by=user_id,
        filename=filename or "document",
        size_bytes=max(0, int(size_bytes)),
        chunk_count=len(chunks),
    )
    db.add(doc)
    db.flush()  # alloue doc.id avant d'insérer les chunks

    # Insertion ORM des chunks pour récupérer les ids (= rowid de la table vec0).
    ins_vec = text("INSERT INTO vec_coach_docs(chunk_id, embedding) VALUES (:id, :emb)")
    for i, (piece, vec) in enumerate(zip(chunks, vectors, strict=False)):
        chunk = CoachDocumentChunk(document_id=doc.id, chunk_index=i, text=piece)
        db.add(chunk)
        db.flush()
        db.execute(ins_vec, {"id": chunk.id, "emb": json.dumps(vec)})
    db.commit()
    logger.info(
        "Coach RAG : document '%s' indexé (user=%d, %d chunks).", doc.filename, user_id, len(chunks)
    )
    return doc


# ================================================================= Récupération

# Projection commune au KNN (SQLite vec0 et pgvector) :
# chunk + document pour pouvoir filtrer sur `uploaded_by` dans le JOIN.
_SELECT = "c.id, c.document_id, c.text"
_JOIN = (
    "coach_document_chunks c ON c.id = v.chunk_id " "JOIN coach_documents d ON d.id = c.document_id"
)
# Un utilisateur ne doit JAMAIS récupérer des chunks d'un autre -> filtre WHERE
# appliqué DANS la requête (pas en post-filtre). `:uid` lié à l'exécution.
_SQL_KNN = knn_sql(_SELECT, "vec_coach_docs", "v", _JOIN, extra_where="d.uploaded_by = :uid")


def retrieve(
    db: Session, user_id: int, query: str, *, top_k: int = 3, max_distance: float = 28.0
) -> list[dict]:
    """Renvoie les `top_k` chunks LES PLUS proches de `query` parmi les documents
    de `user_id` UNIQUEMENT. `max_distance` élague le bruit lointain : au-delà,
    un chunk n'est plus considéré comme pertinent (évite d'injecter du bruit
    sémantique qui ferait divaguer le coach). Chaque résultat :
    {chunk_id, document_id, text, distance}."""
    q = (query or "").strip()
    if not q:
        return []

    try:
        vec = json.dumps(embed_text(q))
    except Exception as exc:
        logger.warning("RAG retrieve indisponible (embedding) : %s", exc)
        return []

    try:
        rows = db.execute(text(_SQL_KNN), {"q": vec, "k": top_k, "uid": user_id}).fetchall()
    except Exception as exc:
        logger.warning("RAG retrieve indisponible (SQL) : %s", exc)
        return []

    out: list[dict] = []
    for cid, did, chunk_text, distance in rows:
        dist = float(distance)
        if max_distance is not None and dist > max_distance:
            continue
        out.append(
            {"chunk_id": cid, "document_id": did, "text": chunk_text, "distance": round(dist, 4)}
        )
    return out


# ================================================================= Gestion UI


def list_documents(db: Session, user_id: int) -> list[dict]:
    """Mes documents, du plus récent au plus ancien (pour l'UI du Coach)."""
    rows = db.scalars(
        select(CoachDocument)
        .where(CoachDocument.uploaded_by == user_id)
        .order_by(CoachDocument.created_at.desc())
    ).all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "size_bytes": d.size_bytes,
            "chunk_count": d.chunk_count,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in rows
    ]


def delete_document(db: Session, user_id: int, doc_id: int) -> int:
    """Supprime UN document SI l'utilisateur en est propriétaire. Renvoie le nombre
    de chunks supprimés (>= 0), ou -1 si introuvable ou pas propriétaire. La
    suppression des vecteurs est faite explicitement (table vec0 non gérée par
    l'ORM) ; sous pgvector, la FK ON DELETE CASCADE suffit."""
    doc = db.get(CoachDocument, doc_id)
    if doc is None or doc.uploaded_by != user_id:
        return -1

    chunk_ids = [c.id for c in db.query(CoachDocumentChunk).filter_by(document_id=doc_id).all()]
    if settings.is_sqlite:
        for cid in chunk_ids:
            db.execute(text("DELETE FROM vec_coach_docs WHERE chunk_id = :id"), {"id": cid})
    db.delete(doc)  # cascade ORM : supprime les coach_document_chunks
    db.commit()
    logger.info(
        "Coach RAG : document id=%d supprimé (user=%d, %d chunks).", doc_id, user_id, len(chunk_ids)
    )
    return len(chunk_ids)
