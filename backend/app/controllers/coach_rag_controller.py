#!/usr/bin/env python3
"""
controllers/coach_rag_controller.py — Documents personnels du Coach Carrière.

RÔLE
    Expose les routes CRUD de la base de connaissances PERSONNELLE du Coach :
    chaque utilisateur téléverse, liste, supprime SES documents (CV, fiches,
    notes…). Isolation stricte : tous les endpoints sont scopés sur l'utilisateur
    authentifié — le périmètre est posé par `uploaded_by = current_user.id` au
    niveau service, jamais pris du client.

SÉCURITÉ
    - Authentification obligatoire (`get_current_user` + CSRF sur mutations) ;
    - Taille et format bornés AVANT extraction (anti-DoS : on ne lit pas 100 Mo
      avant de dire non) ;
    - Erreurs d'extraction (format non supporté, PDF illisible) remontées en 400
      avec un message compréhensible côté UI.

EMPLACEMENT MVC
    Couche "controllers" : routage HTTP, délègue au service.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.auth.dependencies import CurrentUser, DbSession
from app.services import coach_rag_service
from app.services.document_extractor_service import (
    SUPPORTED_EXTENSIONS,
    extract_text,
    file_extension,
)

router = APIRouter(prefix="/api/coach/documents", tags=["Coach"])

# Taille max absolue d'un document téléversé (le middleware HTTP borne la requête
# globale à MAX_REQUEST_SIZE_MB ; on duplique ici une borne un peu plus serrée
# pour une erreur métier claire plutôt qu'un 413 générique).
_MAX_DOC_BYTES = 20 * 1024 * 1024  # 20 Mo


@router.get("", summary="Lister mes documents du Coach")
def list_my_documents(user: CurrentUser, db: DbSession) -> list[dict]:
    return coach_rag_service.list_documents(db, user.id)


@router.post("", summary="Téléverser un document pour mon Coach (PDF/Word/Excel/texte)")
async def upload_document(user: CurrentUser, db: DbSession, file: UploadFile = File(...)) -> dict:
    filename = (file.filename or "").strip() or "document"
    ext = file_extension(filename)
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Format '{ext or '?'}' non supporté. Formats acceptés : "
            f"{', '.join(SUPPORTED_EXTENSIONS)}.",
        )

    content = await file.read()
    size = len(content)
    if size == 0:
        raise HTTPException(status_code=400, detail="Fichier vide.")
    if size > _MAX_DOC_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Document trop volumineux (max {_MAX_DOC_BYTES // (1024*1024)} Mo).",
        )

    try:
        text = extract_text(filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        doc = coach_rag_service.ingest(db, user.id, filename, text, size_bytes=size)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "id": doc.id,
        "filename": doc.filename,
        "size_bytes": doc.size_bytes,
        "chunk_count": doc.chunk_count,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.delete("/{doc_id}", summary="Supprimer un de MES documents du Coach")
def delete_document(doc_id: int, user: CurrentUser, db: DbSession) -> dict:
    removed = coach_rag_service.delete_document(db, user.id, doc_id)
    if removed < 0:  # introuvable OU pas propriétaire → 404 (ne révèle pas)
        raise HTTPException(status_code=404, detail="Document introuvable.")
    return {"deleted": True, "document_id": doc_id, "chunks_removed": removed}
