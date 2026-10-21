# 🌿 BMCI — Gestion des Carrières

[![CI](https://github.com/maounan-018/Gestion_de_carriere/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/maounan-018/Gestion_de_carriere/actions/workflows/ci.yml)

> *(nom de code de la maquette : « La Courbe »)*

Plateforme RH de **gestion de carrière et de mobilité interne** propulsée par une
**IA 100 % locale et open source**, pour la BMCI (Groupe BNP Paribas). Elle aide
collaborateurs, managers et HRBP à **cartographier les compétences, matcher les
talents aux opportunités internes, préparer les entretiens annuels et planifier
la succession** — sans jamais faire sortir une seule donnée de l'infrastructure
de la banque.

> Frontend **Vue 3 / Vite / Tailwind**, backend **Python FastAPI** en architecture
> **MVC + SQLAlchemy 2.0**, **panoplie de modèles IA locaux** (Ollama : Qwen3,
> Mistral, Hermes, BGE-M3), référentiels de compétences **ESCO + O*NET + SFIA**
> (FR/EN). Base de données **SQLite** (dev local) **ou PostgreSQL/pgvector**
> (prod, Supabase). Front déployé sur **Vercel** ; backend volontairement **chez
> l'utilisateur** pour que les données ne quittent pas la machine.

---

## 🚀 Démarrage rapide (Windows)

Double-cliquez sur **`Lancer-BMCI.bat`** à la racine : il démarre toute la stack
locale — **Ollama** (IA, `:11434`), **backend FastAPI** (`:5001`, env conda
`bmci-carrieres`), **frontend Vite** (`:3001`, mode live vers le backend) — puis
ouvre le navigateur sur l'application. Chaque service tourne dans sa fenêtre
(fermer la fenêtre = arrêter le service).

**Prérequis (une fois)** :
- conda + env `bmci-carrieres` (voir `backend/requirements.txt`) ;
- Node.js 20+ et `npm` ;
- Ollama + modèles (`scripts/pull_models.sh` ou téléchargement manuel : `qwen3:8b`,
  `mistral-nemo`, `hermes3:8b`, `bge-m3`) ;
- base `backend/bmci_carrieres.db` (créée au premier lancement + seed depuis
  `python -m app.database.seed`).

Mode UI-only (sans backend, pour contempler les écrans) : poser `VITE_API_MODE=mock`
dans `frontend/.env.local`.

---

## 🧭 Où en est-on ?

| Volet | État |
|---|---|
| Cartographie des parcours & 34 écrans (3 rôles : COLLAB / MANAGER / HRBP) | ✅ livré |
| Référentiels ESCO/O*NET/SFIA ingérés (14 173 compétences + 4 059 métiers vectorisés) | ✅ livré |
| Moteur IA (ai_router, bge-m3, reranker FlagEmbedding, routage YAML par tâche) | ✅ livré |
| Extraction compétences · matching · recommandations · succession · génération fiches | ✅ 5 fonctions livrées |
| Coach Carrière agentique (tool-calling : offres, mobilité, référentiel) + streaming SSE | ✅ livré |
| **Coach : RAG personnel** (upload PDF/Word/Excel/texte, isolement par utilisateur) | ✅ livré |
| Simulation d'entretien annuel (copilote collab, role-play RH/manager) | ✅ livré |
| Sécurité (auth locale PBKDF2, sessions hashées, RBAC + ownership row-level, audit) | ✅ livré |
| Base PostgreSQL + pgvector (Supabase) · bascule SQLite ↔ Postgres via `DATABASE_URL` | ✅ livré |
| Déploiement front **Vercel** · backend local (cross-origin, Bearer en sessionStorage) | ✅ livré |
| CI GitHub Actions · pre-commit · ruff · vue-tsc · gunicorn prod multi-worker | ✅ livré |
| SSO SAML + provisioning JIT | ⬜ placeholder — à porter depuis smart-objective |

---

## 📚 Documentation d'architecture (`docs/`)

| Document | Contenu |
|---|---|
| [`REFERENTIELS-COMPETENCES.md`](docs/REFERENTIELS-COMPETENCES.md) | **ESCO / O*NET / SFIA** bilingues : licences, formats, ingestion, crosswalk |
| [`DEPLOIEMENT-VERCEL.md`](docs/DEPLOIEMENT-VERCEL.md) | Déploiement du front sur Vercel + backend local (cross-origin, auth Bearer) |

---

## 🗂️ Structure du dépôt

```
bmci-gestion-carrieres/
├── README.md
├── .pre-commit-config.yaml       # Hooks locaux (ruff, vue-tsc, gitleaks)
├── .github/workflows/ci.yml      # CI : lint + tests backend/front + scan sécu
├── Lancer-BMCI.bat               # Démarrage tout-en-un (Windows)
├── docs/                         # Architecture & décisions techniques (ci-dessus)
├── backend/                      # FastAPI (MVC + SQLAlchemy 2.0)
│   ├── pyproject.toml            #   Config ruff + pytest
│   ├── gunicorn.conf.py          #   Serveur de PRODUCTION (multi-worker)
│   ├── requirements.txt
│   └── app/{auth,controllers,core,database,middlewares,
│           models,repositories,schemas,services,utils,tests}
├── frontend/                     # Vue 3 (Vite, Tailwind, Pinia, Vue Router)
│   ├── .env.example              #   Variables Vite documentées
│   └── src/{components,guards,layouts,router,services,stores,utils,views}
├── ia/                           # Brique IA locale (ESCO/O*NET/SFIA + routing.yaml)
│   ├── modelfiles/
│   └── referentiels/             #   Dossier ignoré (gros téléchargements publics)
└── scripts/                      # Lancement, vérification, ingestion
```

---

## 🏛️ Principe directeur (hérité de `bmci-smartobjective`)

1. **Le frontend ne connaît ni l'IA ni la base** : tout passe par `/api/*`.
2. **Le backend est l'unique source de vérité** : auth, RBAC, appels IA, persistance.
3. **L'IA tourne en local** (Ollama `:11434`, jamais exposé) : **aucune donnée ne sort**.
4. **Confidentialité bancaire by design** : RBAC strict, audit trail, cloisonnement
   des données par rôle, documents RAG personnels **isolés par utilisateur**.

---

## 🔐 Secrets & variables d'environnement

Rien de sensible n'est versionné :
- `backend/.env` : **config de dev** (ports Ollama, CORS, flags) — **SANS secret**.
- `backend/.env.local` (**gitignored**) : `DATABASE_URL` Supabase + `SEED_DEMO_PASSWORD`.
- `frontend/.env.example` : documente les variables, dont `VITE_DEMO_PASSWORD`.
- `frontend/.env.local` (**gitignored**) : `VITE_DEMO_PASSWORD` miroir du backend.

**Compte de démo** : les emails `youssef.elamrani@bmci.local` (COLLAB),
`karim.naji@bmci.local` (MANAGER), `nadia.alami@bmci.local` (HRBP) sont publics
dans le code. Le mot de passe n'est jamais commité ; il est injecté localement
via `VITE_DEMO_PASSWORD`. En déploiement public (Vercel), la variable est
volontairement absente : les champs se pré-remplissent avec l'email seul, et
la connexion exige la saisie manuelle du mot de passe (impossible donc à récupérer
depuis le bundle JS).

---

## ⚙️ Process dev

| Outil | Commande | Objectif |
|---|---|---|
| **pre-commit** | `pip install pre-commit && pre-commit install` | Hooks locaux : ruff, vue-tsc, gitleaks, hygiène fichiers |
| **ruff** | `cd backend && ruff check . && ruff format .` | Lint + format Python (remplace flake8/black/isort) |
| **pytest** | `cd backend && pytest` | 195+ tests (sécurité, RBAC, auth, SSO SAML, RAG) |
| **vue-tsc** | `cd frontend && npx vue-tsc --noEmit` | Type-check TypeScript/Vue |
| **vitest** | `cd frontend && npm test` | 60+ tests unitaires frontend |
| **CI** | déclenchée à chaque push/PR sur `master` | 3 jobs : backend, frontend, security (gitleaks + pip-audit + npm audit) |

---

## 🏭 Mise en production (backend)

En dev : `uvicorn app.main:app --reload` (mono-process, hot-reload).

En prod : `gunicorn -c gunicorn.conf.py app.main:app`. La config fournie monte
automatiquement plusieurs **UvicornWorker** (formule `CPU*2+1` par défaut,
réglable via `WEB_CONCURRENCY`). Elle gère : timeouts longs (IA Coach peut
dépasser 60 s), recyclage préventif des workers (`max_requests=1000` + jitter),
format d'access log structuré.

**Attention GPU** : le sémaphore `ai_router._GPU_LOCK` sérialise les appels Ollama
**intra-process**. En multi-workers sur un GPU unique, il faut soit limiter à
`WEB_CONCURRENCY=2` (API + 1 worker IA concurrent), soit déplacer le lock vers
un sémaphore inter-process (`filelock`).

---

## 🤖 Pile IA — modèles & routage

| Tâche | Modèle | Rôle |
|---|---|---|
| Extraction de compétences | `hermes3:8b` (JSON strict) | Lire un descriptif → compétences normalisées |
| Analyse d'une fiche de poste | `qwen3:8b` | Décomposer un poste en missions / compétences |
| Coach Carrière agentique | `qwen3:8b` + tool-calling | Dialogue avec outils (offres, mobilité, référentiel) |
| Coach — réponse rédigée | `mistral-nemo:12b` | Qualité FR, format long |
| Entretien annuel (role-play) | `mistral-nemo:12b` | Préparation guidée + simulation |
| Embeddings | `bge-m3` (1024 dim) | Compétences, métiers, **documents RAG perso** |
| Reranking | `BAAI/bge-reranker-v2-m3` (FlagEmbedding) | Cross-encoder, correction fine du rappel |

Routage déclaratif dans `ia/routing.yaml` : **changer le modèle d'une fonctionnalité
= éditer 1 ligne** (jamais le code).

---

## 📊 Base de données — SQLite ↔ Postgres (bascule)

- **Dev** : SQLite `backend/bmci_carrieres.db` + extension `sqlite-vec` (vec0
  virtual tables pour les embeddings).
- **Prod** : PostgreSQL + `pgvector` (`vector(1024)` + index HNSW cosinus).
  Supabase utilisé en pratique.
- **Bascule** : poser `DATABASE_URL=postgresql://…` dans `backend/.env.local`.
  Absent → repli automatique sur SQLite. Le code est **dialecte-agnostique**
  (`database/vector_search.knn_sql`) : les requêtes KNN sont générées pour
  l'un ou l'autre backend sans changer d'une ligne la couche métier.

---

## 📜 Licence & crédits

Projet académique / portfolio. Référentiels : **ESCO** (CC-BY 4.0), **O*NET**
(domaine public), **SFIA** (gratuit non-commercial). Modèles IA : licences
respectives (Qwen3 / Mistral / Hermes / BGE-M3).

---

*École Centrale Casablanca × BMCI — 2026*
