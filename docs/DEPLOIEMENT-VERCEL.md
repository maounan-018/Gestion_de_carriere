# Déploiement — Front sur Vercel, backend local (Ollama)

> **Déploiement actuel**
> - Front (production) : <https://gestion-de-carriere-steel.vercel.app>
> - Repo GitHub : `maounan-018/Gestion_de_carriere` — branche `master`
> - Projet Vercel : `gestion-de-carriere` (team *MAOUNAN DAVID*, Hobby) — Root Directory `frontend`
> - Redéploiement : **automatique** à chaque `git push` sur `master`.

## Architecture retenue

```
Navigateur ─▶ Front (Vercel, https://gestion-de-carriere-steel.vercel.app)  ← statique, Vite
                   │  appels API en CROSS-ORIGIN (auth Bearer)
                   ▼
             FastAPI  (http://localhost:5001, SUR LA MACHINE de l'utilisateur)
                   ├─▶ Ollama local (:11434)          ← IA 100 % locale
                   └─▶ Supabase Postgres / pgvector   ← persistance cloud
```

Le front déployé n'appelle **pas** un backend hébergé : il appelle le FastAPI qui
tourne **en local chez l'utilisateur** (`VITE_API_BASE=http://localhost:5001`, cf.
`frontend/.env.production`). Conséquence assumée : le site n'est **fonctionnel que
si l'utilisateur lance le backend** (+ Ollama) sur sa propre machine. Supabase
n'apporte que la base de données ; il ne fait pas tourner le Python.

## Pourquoi Bearer (et pas les cookies)

En cross-origin (site public HTTPS → `localhost`), les cookies same-site ne sont
pas transmis. L'auth passe donc par l'en-tête `Authorization: Bearer <token>` :
- le `/auth/login` renvoie le jeton dans le corps (`token`), mémorisé côté front
  (sessionStorage — isolé par onglet, effacé à sa fermeture : surface XSS plus
  courte que localStorage) et rejoué sur chaque requête ;
- le backend accepte déjà le Bearer (`extract_token`) ;
- le CSRF double-submit est **sauté** quand l'auth est Bearer (aucun cookie → aucun
  vecteur CSRF ; cf. `_check_csrf`).

En dév local (`VITE_API_BASE` vide), **rien ne change** : proxy Vite `/api → :5001`,
cookies HttpOnly + CSRF comme avant.

---

## 1. Repo GitHub — fait

Le code est sur `maounan-018/Gestion_de_carriere` (privé). Les secrets sont couverts
par `.gitignore` (`*.db`, `MDP.txt`, `.env.local`, `backend/data/cv_profil/`) ;
`backend/.env` est la config de **dév sans secret**. Pour les mises à jour :

```bash
git push origin master
```

Vérifier au besoin qu'aucun secret n'est suivi :

```bash
git status --ignored --short
```

## 2. Projet Vercel — fait

Import GitHub → projet `gestion-de-carriere`, avec :

- **Root Directory** : `frontend`  ← indispensable (le `vercel.json` y est).
- Framework **Vite**, build `npm run build`, output `dist` (déjà dans `vercel.json`).
- **Aucune** variable d'env à ajouter : `VITE_API_BASE` vient de `frontend/.env.production`.

> ⚠️ `vercel.json` est validé strictement : **pas de clé de commentaire** (`"//"`)
> dans un objet `rewrites` (seuls `source`/`destination`/… sont permis), sinon
> l'import échoue.

## 3. Autoriser l'origine Vercel côté backend (CORS) — fait

Configuré dans `backend/.env.local` (ignoré par git) via un **motif** qui couvre la
prod ET les preview deployments (URLs aléatoires), sans rien lister à la main :

```
ALLOWED_ORIGIN_REGEX=https://.*\.vercel\.app$
```

Ce motif s'ajoute à `ALLOWED_ORIGINS` (localhost, dans `backend/.env`) sans le
remplacer. Alternative explicite si l'on préfère une origine unique :

```
ALLOWED_ORIGINS=http://localhost:3001,https://gestion-de-carriere-steel.vercel.app
```

Redémarrer le backend après toute modification.

## 4. Lancer le backend en local (chaque utilisateur)

Prérequis : Ollama démarré (modèles tirés) + `DATABASE_URL` Supabase dans
`backend/.env.local`. Puis :

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 5001
```

Ouvrir <https://gestion-de-carriere-steel.vercel.app> puis se connecter. Au premier
appel, **Chrome affiche un préflight Private Network Access** (site public → réseau
local) : le backend répond `Access-Control-Allow-Private-Network: true`, et
l'utilisateur doit **autoriser** l'accès au réseau local si le navigateur le demande.

---

## Limites à connaître

- **Le site ne marche que si le backend local tourne.** Un visiteur sans backend
  voit l'UI mais les appels échouent (c'est le choix « backend chez l'utilisateur »).
- **Navigateurs** : Chrome/Edge gèrent le mieux l'accès public → `localhost`.
  Firefox/Safari appliquent des règles différentes (Private/Local Network Access).
- **Coach (SSE)** : le flux passe en direct depuis le backend local (pas de proxy
  Vercel), donc l'effet « frappe en direct » est préservé.
- **HTTPS → http://localhost** : autorisé (localhost est « potentially trustworthy »,
  pas de blocage mixed-content).
