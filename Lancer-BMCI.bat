@echo off
setlocal
chcp 65001 >nul
title BMCI Gestion des Carrieres - Lanceur

REM ============================================================================
REM  Lancer-BMCI.bat - Demarre TOUTE la stack locale en un clic :
REM    1) Ollama (IA locale, :11434)   - demarre seulement s'il ne tourne pas
REM    2) Backend FastAPI (:5001)      - conda env "bmci-carrieres" + uvicorn
REM    3) Frontend Vite (:3001)        - npm run dev, force en mode LIVE
REM  Puis ouvre le navigateur sur l'application.
REM
REM  Prerequis (installes une seule fois) : Anaconda/conda avec l'env
REM  "bmci-carrieres", Node.js/npm, Ollama + modeles (scripts\pull_models.sh).
REM  Chaque service s'ouvre dans SA fenetre ; fermer la fenetre = arreter le service.
REM ============================================================================

set "ROOT=%~dp0"
echo ============================================================
echo   BMCI - Gestion des Carrieres  ^|  demarrage de la stack
echo ============================================================
echo.

REM --- Verifications rapides ------------------------------------------------
where conda >nul 2>&1 || (echo [ERREUR] "conda" introuvable dans le PATH. & goto :fin)
where npm   >nul 2>&1 || (echo [ERREUR] "npm" introuvable dans le PATH. & goto :fin)
if not exist "%ROOT%backend\bmci_carrieres.db" (
  echo [ATTENTION] Base "backend\bmci_carrieres.db" absente.
  echo             1er lancement ? Preparez-la d'abord depuis backend\ ^(env conda^) :
  echo               conda run -n bmci-carrieres alembic upgrade head
  echo               conda run -n bmci-carrieres python -m app.database.seed
  echo             Reco/matching : ingestion des referentiels requise en amont ^(voir README^).
  echo.
)

REM --- 1) Ollama : demarrer seulement s'il ne repond pas -------------------
echo [1/3] Ollama (IA locale, :11434)...
curl -s -f -o nul http://localhost:11434/api/tags
if errorlevel 1 (
  echo       non detecte -^> demarrage d'Ollama
  start "Ollama" cmd /k "ollama serve"
) else (
  echo       deja actif, on le reutilise.
)

REM --- 2) Backend FastAPI (:5001) ------------------------------------------
echo [2/3] Backend FastAPI (:5001)  [conda env bmci-carrieres]...
start "BMCI Backend :5001" cmd /k "cd /d "%ROOT%backend" && conda run -n bmci-carrieres --no-capture-output python -m uvicorn app.main:app --host 127.0.0.1 --port 5001"

REM --- 3) Frontend Vite (:3001), force en LIVE (surcharge .env.local) ------
echo [3/3] Frontend Vite (:3001)  [mode LIVE -^> backend :5001]...
start "BMCI Frontend :3001" cmd /k "cd /d "%ROOT%frontend" && set "VITE_API_MODE=live" && npm run dev"

REM --- Ouverture du navigateur (laisse le temps a Vite de compiler) --------
echo.
echo   Demarrage en cours... ouverture du navigateur dans ~12s.
echo   (Astuce : mode maquette hors backend = mettre VITE_API_MODE=mock dans frontend\.env.local)
echo   (Rafraichir donnees demo + cartographie 33 departements, depuis backend\ :)
echo      conda run -n bmci-carrieres python -m app.database.seed   [idempotent]
timeout /t 12 /nobreak >nul
start "" http://localhost:3001

echo.
echo   Stack lancee. Fermez les fenetres "Ollama / Backend / Frontend" pour arreter.
:fin
endlocal
