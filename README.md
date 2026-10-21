# 🌿 Gestion des Carrières — Plateforme RH assistée par IA locale

[![CI](https://github.com/maounan-018/Gestion_de_carriere/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/maounan-018/Gestion_de_carriere/actions/workflows/ci.yml)

Plateforme web de **gestion de carrière et de mobilité interne** pour un grand
groupe bancaire, propulsée par une **IA 100 % locale et open source** (aucune
donnée ne quitte l'infrastructure). Trois espaces (**Collaborateur**, **Manager**,
**HRBP**) sur un parcours cohérent : cartographie des compétences, matching
offres ↔ profils, Coach Carrière conversationnel, préparation d'entretiens
annuels, planification de la succession.

> **Stack** · Vue 3 / Vite / Tailwind — FastAPI (MVC, SQLAlchemy 2.0) — Ollama
> local (Qwen3, Mistral, Hermes, BGE-M3) — ESCO / O\*NET / SFIA bilingues —
> SQLite + sqlite-vec en dev, PostgreSQL + pgvector en prod — Vercel pour le
> front, serveur applicatif FastAPI pour le backend.

---

## ✨ Points forts

- **IA entièrement locale** — modèles Ollama auto-hébergés, embeddings `bge-m3`
  et reranker cross-encoder. Aucune API externe, aucune donnée exfiltrée.
- **Référentiels métiers industriels** — graphe unifié ESCO + O\*NET + SFIA
  (14 173 compétences canonicalisées, 4 059 métiers vectorisés, crosswalk
  inter-référentiels) qui ancre toutes les analyses.
- **Coach Carrière agentique** — LLM avec tool-calling + streaming SSE, qui
  interroge les offres compatibles, les passerelles de mobilité et le
  référentiel ; chaque utilisateur peut **téléverser ses documents** (CV, notes,
  fiches) et le Coach s'en sert via un **RAG personnel isolé** (chunks + KNN
  filtré par propriétaire).
- **Simulation d'entretien annuel** — copilote guidé (collaborateur) et role-play
  (RH/manager) ancrés sur le profil réel.
- **Sécurité bancaire par conception** — PBKDF2, tokens de session hachés en base,
  CSRF double-submit, cookies HttpOnly, CSP stricte, HSTS en prod, ownership
  ligne-à-ligne (RBAC + périmètre), audit trail, rate-limit IA par utilisateur.
- **Architecture dialecte-agnostique** — même code, deux cibles : SQLite + vec0
  (dev, zéro infra) ou PostgreSQL + pgvector (prod, HNSW cosinus). Bascule par
  simple `DATABASE_URL`.
- **Industrialisation** — pre-commit (ruff, vue-tsc, gitleaks), CI GitHub Actions
  (lint, 195 tests backend, 60 tests frontend, scan secrets, audit deps), config
  gunicorn multi-worker pour la prod.

---

## 🏛️ Architecture

```
┌──────────────────────┐          ┌───────────────────────┐          ┌──────────────────┐
│  Frontend Vue 3      │ ───────▶ │  Backend FastAPI      │ ───────▶ │  Ollama (local)  │
│  Vite · Tailwind     │  /api/*  │  MVC · SQLAlchemy 2.0 │ generate │  LLM + embeddings│
│  Pinia · Vue Router  │          │  JSON / SSE           │  embed   │  Jamais exposé   │
└──────────────────────┘          └───────────┬───────────┘          └──────────────────┘
                                              │
                             ┌────────────────┴─────────────────┐
                             ▼                                  ▼
                 ┌──────────────────────┐          ┌──────────────────────────┐
                 │  SQLite + sqlite-vec │          │  PostgreSQL + pgvector   │
                 │  (dev local)         │   OR     │  HNSW cosine (prod)      │
                 └──────────────────────┘          └──────────────────────────┘
```

**Principes directeurs** :

1. Le frontend ne connaît ni l'IA ni la base — tout passe par `/api/*`.
2. Le backend est l'unique source de vérité : auth, RBAC, orchestration IA,
   persistance.
3. L'IA tourne en local (`:11434` jamais exposé). Aucune donnée ne quitte la
   machine.
4. Confidentialité par conception : cloisonnement par rôle, périmètre par
   équipe/offre, documents RAG isolés par propriétaire.

---

## 🚀 Démarrage rapide (Windows)

Double-cliquez sur **`Lancer-BMCI.bat`** à la racine. Il démarre toute la stack
locale — Ollama (`:11434`), backend FastAPI (`:5001`), frontend Vite (`:3001`) —
et ouvre le navigateur sur l'application. Chaque service a sa fenêtre console
(fermer = arrêter).

**Prérequis (une fois)** :

- `conda` + env `bmci-carrieres` (`conda create -n bmci-carrieres python=3.11 && pip install -r backend/requirements.txt`)
- Node.js 20+
- [Ollama](https://ollama.com/) + modèles : `qwen3:8b`, `mistral-nemo`, `hermes3:8b`, `bge-m3`

Puis au premier lancement, le script seed la base (`backend/bmci_carrieres.db`)
avec une population synthétique de démonstration (profils, offres, parcours).

**Mode UI-only** (sans backend, pour visualiser les écrans) : poser
`VITE_API_MODE=mock` dans `frontend/.env.local`.

---

## 🤖 Pile IA — modèle par tâche

Le routage est **déclaratif** (`ia/routing.yaml`) : changer le modèle d'une
fonctionnalité, c'est éditer une ligne, pas le code.

| Tâche | Modèle | Rôle |
|---|---|---|
| Extraction de compétences | `hermes3:8b` (format JSON strict) | Lire un descriptif → compétences normalisées |
| Analyse d'une fiche de poste | `qwen3:8b` | Décomposer un poste en missions / compétences |
| Coach Carrière agentique | `qwen3:8b` + tool-calling | Dialogue avec outils (offres, mobilité, référentiel) |
| Coach — réponse rédigée | `mistral-nemo:12b` | Qualité FR, format long, streaming |
| Entretien annuel (role-play) | `mistral-nemo:12b` | Copilote guidé + simulation |
| Embeddings | `bge-m3` (1024 dim) | Compétences, métiers, documents RAG |
| Reranking | `BAAI/bge-reranker-v2-m3` (FlagEmbedding) | Cross-encoder, correction fine du rappel |

---

## 📊 Base de données — SQLite ↔ Postgres

Même code, deux cibles :

- **Dev** : SQLite `bmci_carrieres.db` + extension `sqlite-vec` (tables virtuelles
  vec0 pour les embeddings). Zéro infra à monter.
- **Prod** : PostgreSQL + `pgvector` (`vector(1024)` + index HNSW cosinus).
- **Bascule** : poser `DATABASE_URL=postgresql://…` dans `backend/.env.local`.
  Absent → repli automatique sur SQLite.

Les requêtes KNN sont générées pour l'un ou l'autre backend par
`database/vector_search.knn_sql` — **la couche métier ne connaît pas le
dialecte**.

---

## 🔐 Sécurité & secrets

Rien de sensible n'est versionné :

- `backend/.env` : config de dev (ports, CORS, flags) — **sans aucun secret**.
- `backend/.env.local`, `frontend/.env.local` : **gitignored**, hébergent
  `DATABASE_URL`, `SEED_DEMO_PASSWORD`, `VITE_DEMO_PASSWORD`.
- Les comptes de démonstration (emails `@bmci.local`) existent uniquement en
  base de dev seedée ; leur mot de passe est injecté par variable d'environnement,
  jamais commité dans le bundle JS.
- Historique git scanné en continu par `gitleaks` (hook pre-commit + job CI).

Côté auth : PBKDF2 (200 000 itérations), token de session SHA-256 en base,
cookie HttpOnly + CSRF double-submit (same-origin) ou Bearer en `sessionStorage`
(cross-origin), rate-limit IA par utilisateur avec audit des dépassements.

---

## ⚙️ Qualité & process dev

| Outil | Commande | Rôle |
|---|---|---|
| **pre-commit** | `pre-commit install` | Hooks locaux : ruff, vue-tsc, gitleaks |
| **ruff** | `cd backend && ruff check . && ruff format .` | Lint + format Python (black-compatible) |
| **pytest** | `cd backend && pytest` | **195 tests** (sécurité, RBAC, auth, RAG, matching) |
| **vue-tsc** | `cd frontend && npx vue-tsc --noEmit` | Type-check TypeScript/Vue |
| **vitest** | `cd frontend && npm test` | **60 tests** unitaires frontend |
| **CI** | GitHub Actions sur chaque push/PR `master` | 3 jobs parallèles : backend, frontend, security |

---

## 🏭 Mise en production (backend)

En dev : `uvicorn app.main:app --reload`.

En prod : `gunicorn -c gunicorn.conf.py app.main:app` — plusieurs `UvicornWorker`
(formule `CPU*2+1`, override `WEB_CONCURRENCY`), timeouts adaptés aux appels IA
longs, recyclage préventif des workers, access log structuré.

**Attention GPU** : le sémaphore `ai_router._GPU_LOCK` sérialise les appels Ollama
intra-process. Sur un serveur mono-GPU, soit limiter à `WEB_CONCURRENCY=2`, soit
déplacer le lock vers un sémaphore inter-process (`filelock`).

---

## 🗂️ Structure du dépôt

```
.
├── .pre-commit-config.yaml       # Hooks locaux (ruff, vue-tsc, gitleaks)
├── .github/workflows/ci.yml      # CI : lint + tests + scan sécurité
├── Lancer-BMCI.bat               # Démarrage tout-en-un (Windows)
├── docs/                         # Notes d'architecture & décisions
├── backend/                      # FastAPI (MVC + SQLAlchemy 2.0)
│   ├── pyproject.toml            #   Config ruff + pytest
│   ├── gunicorn.conf.py          #   Serveur de production
│   ├── requirements.txt
│   └── app/{auth,controllers,core,database,middlewares,
│           models,repositories,schemas,services,utils,tests}
├── frontend/                     # Vue 3 (Vite, Tailwind, Pinia, Vue Router)
│   ├── .env.example              #   Variables Vite documentées
│   └── src/{components,guards,layouts,router,services,stores,utils,views}
├── ia/                           # Brique IA (routing.yaml + référentiels)
└── scripts/                      # Lancement, vérification, ingestion
```

---

## 📜 Crédits & licences

Référentiels : **ESCO** (CC-BY 4.0, Commission Européenne), **O\*NET**
(domaine public, U.S. Department of Labor), **SFIA** (gratuit à usage
non-commercial). Modèles IA : licences respectives (Qwen 3 · Mistral · Hermes 3
· BGE-M3). Code applicatif : usage personnel / démonstration.
