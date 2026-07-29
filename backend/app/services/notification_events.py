#!/usr/bin/env python3
"""
services/notification_events.py — Émission de notifications sur ÉVÈNEMENTS métier.

RÔLE
    Traduit un évènement métier (décision de candidature, souhait poussé / décidé)
    en une notification destinée au BON utilisateur. Centralise le libellé et le
    choix du destinataire (sinon dispersés dans chaque service).

    ÉMISSION ATOMIQUE : `commit=False` -> la notification rejoint la même
    transaction que la mutation métier (décidée en même temps qu'elle, ou pas du
    tout). Best-effort sur le destinataire : un persona synthétique (sans compte)
    ou un collaborateur sans manager n'émet simplement rien.

EMPLACEMENT MVC
    Couche "services" : orchestration métier, sans route HTTP. Reçoit `db`.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.candidature import Candidature, CandidatureStatut
from app.models.offre import Offre
from app.models.profil import Profil
from app.models.souhait import Souhait, SouhaitStatut
from app.models.notification import NotificationType
from app.services import notification_service

# Décisions de candidature qui méritent une notification au candidat.
_CANDIDATURE_LABEL = {CandidatureStatut.RETENUE: "retenue",
                      CandidatureStatut.REJETEE: "refusée"}
# Décisions de souhait qui méritent une notification au collaborateur.
_SOUHAIT_VERDICT = {SouhaitStatut.ACCORDE: "accordé", SouhaitStatut.REFUSE: "refusé"}


def on_candidature_decidee(db: Session, cand: Candidature) -> None:
    """Notifie le CANDIDAT (propriétaire du profil) d'une décision retenue/refusée."""
    label = _CANDIDATURE_LABEL.get(cand.statut)
    if label is None:
        return                                   # statut non notifiable (en_evaluation, retiree…)
    profil = db.get(Profil, cand.profil_id)
    if profil is None or profil.user_id is None:
        return                                   # persona synthétique : personne à notifier
    offre = db.get(Offre, cand.offre_id)
    titre_offre = offre.titre if offre else "une offre"
    notification_service.create_notification(
        db, user_id=profil.user_id, type=NotificationType.ACTION,
        titre="Décision sur votre candidature",
        texte=f"Votre candidature à « {titre_offre} » a été {label}.",
        to_route="candidatures", commit=False)


def on_souhait_pousse(db: Session, souhait: Souhait, profil: Profil,
                      manager_user_id: int | None) -> None:
    """Notifie le MANAGER qu'un souhait de son équipe lui a été poussé."""
    if not manager_user_id:
        return                                   # pas de manager rattaché
    nom = f"{(profil.prenom or '').strip()} {profil.nom}".strip()
    notification_service.create_notification(
        db, user_id=manager_user_id, type=NotificationType.SOUHAIT,
        titre="Nouveau souhait d'évolution",
        texte=f"{nom} vous a poussé un souhait : « {souhait.titre} ».",
        to_route="souhaits-recus", commit=False)


def on_souhait_decide(db: Session, souhait: Souhait, profil: Profil) -> None:
    """Notifie le COLLABORATEUR (propriétaire) d'une décision accordé/refusé."""
    verdict = _SOUHAIT_VERDICT.get(souhait.statut)
    if verdict is None or profil.user_id is None:
        return
    notification_service.create_notification(
        db, user_id=profil.user_id, type=NotificationType.SOUHAIT,
        titre="Réponse à votre souhait",
        texte=f"Votre souhait « {souhait.titre} » a été {verdict}.",
        to_route="souhaits", commit=False)
