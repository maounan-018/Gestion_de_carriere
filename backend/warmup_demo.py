#!/usr/bin/env python3
"""
warmup_demo.py — Pré-chauffe les sorties IA de la démo pour un chargement INSTANTANÉ.

Les appels IA (reco, analyse) passent par Ollama et prennent plusieurs secondes.
MAIS leurs résultats sont mis en cache ET persistés (reco : par signature dans la
table `recommandations` ; analyse RH : table `analyse_rh`). Ce script génère ces
sorties À L'AVANCE (une fois), de sorte que pendant la démo, l'écran les charge
depuis la base en < 100 ms — aucune attente Ollama devant le public.

À lancer AVANT la démo (après le seed / démarrage d'Ollama), depuis backend/ :
    conda run -n bmci-carrieres python warmup_demo.py

Idempotent : relancer ne fait que rafraîchir le cache.
"""
import time

from app.database.session import SessionLocal
from app.models.user import User
from app.services import recommendation_service, analyse_service
from sqlalchemy import select

# Comptes personas dont on pré-chauffe la reco (collaborateurs / managers).
_PERSONAS_RECO = [
    "youssef.elamrani@bmci.local",   # collaborateur (reco « ma reco »)
    "karim.naji@bmci.local",         # manager
]


def _chrono(label, fn):
    t0 = time.perf_counter()
    try:
        fn()
        print(f"  ✓ {label}  ({time.perf_counter() - t0:.1f}s)")
    except Exception as e:  # noqa: BLE001 — best effort, on continue
        print(f"  ✗ {label}  ÉCHEC : {e}")


def main() -> None:
    db = SessionLocal()
    try:
        print("Pré-chauffe des sorties IA de la démo…")
        for email in _PERSONAS_RECO:
            u = db.scalar(select(User).where(User.email == email))
            if not u:
                print(f"  · {email} : compte introuvable, ignoré")
                continue
            _chrono(f"reco {email}",
                    lambda uid=u.id: recommendation_service.recommander_pour_user(db, uid))
        # Analyse stratégique RH (dashboard HRBP) — persistée (scope global).
        _chrono("analyse RH", lambda: analyse_service.analyser(db))
        print("Terminé. Ces écrans se chargeront désormais instantanément (cache/persistance).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
