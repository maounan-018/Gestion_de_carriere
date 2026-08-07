# 🌿 BMCI — Gestion des Carrières

> *(nom de code de la maquette : « La Courbe »)*

Plateforme RH de **gestion de carrière et de mobilité interne** propulsée par une
**IA 100 % locale et open source**, pour la BMCI (Groupe BNP Paribas). Elle aide
collaborateurs, managers et RH à **cartographier les compétences, matcher les
talents aux opportunités, planifier les évolutions et la succession** — sans
jamais faire sortir une seule donnée de l'infrastructure de la banque.

> Version **0.1 (fondation)** — Frontend **Vue 3 / Vite / Tailwind**, backend
> **Python FastAPI** en architecture **MVC + SQLAlchemy**, **panoplie de modèles
> IA locaux** (Ollama : Qwen3, Mistral, Hermes, BGE… — le meilleur par tâche),
> référentiels de compétences **ESCO + O*NET + SFIA** (FR/EN, gratuits),
> **SSO SAML 2.0**. Le backend reste l'unique
> source de vérité. Aucune donnée ne quitte la machine.

Ce projet **réplique les bonnes pratiques** du projet frère *ObjectifSMART-AI*
(`bmci-smartobjective`) et **élève le niveau graphique** par rapport à la
maquette UI/UX initiale.

---

## 🚀 Démarrage rapide (Windows)

Double-cliquez sur **`Lancer-BMCI.bat`** (à la racine) : il démarre toute la stack
locale — **Ollama** (IA, `:11434`), **backend FastAPI** (`:5001`, env conda
`bmci-carrieres`), **frontend Vite** (`:3001`, en mode **live** vers le backend) —
puis ouvre le navigateur sur l'application. Chaque service tourne dans sa fenêtre
(fermer la fenêtre = arrêter le service).

*Prérequis (une fois)* : conda + env `bmci-carrieres`, Node.js/npm, Ollama +
modèles (`scripts/pull_models.sh`), et la base `backend/bmci_carrieres.db`
(migrations `alembic upgrade head` + seed). Pour la maquette **sans** backend :
`VITE_API_MODE=mock` dans `frontend/.env.local`.

---

## Où en est-on ? *(màj 2026-07-21)*

| Volet | État |
|---|---|
| Cartographie des parcours & maquette UI/UX (34 écrans, 3 rôles) | ✅ fait |
| Fondation du dépôt (structure, docs d'architecture) | ✅ fait |
| Recherche modèles IA locaux + référentiels | ✅ documentée (`docs/`) |
| Ingestion des référentiels (ESCO/O*NET/SFIA) | ✅ fait — 14 173 compétences, 4 059 métiers vectorisés + crosswalk |
| Moteur IA (ai_router, embeddings bge-m3, reranker) | ✅ fait |
| Fonctions métier IA (extraction, matching, reco, génération de fiches) | ✅ 5 fonctions livrées |
| Modèle métier (Fiche + 164 fiches persistées, Profil CRUD) | ✅ fait — Offre/Candidature : modèles posés, **CRUD à faire** |
| Sécurité (auth locale, sessions, RBAC, audit) | ⏳ code posé & guards branchés — à seeder / tester / durcir |
| Backend FastAPI — reste | ⏳ CRUD Offre/Candidature, matching sur entités, dashboards RH |
| Frontend Vue (implémentation des écrans maquettés) | ⬜ à construire |
| SSO SAML + provisioning | ⬜ placeholder documenté — à porter depuis smart-objective |

---

## Documentation d'architecture (`docs/`)

| Document | Contenu |
|---|---|
| [`REFERENTIELS-COMPETENCES.md`](docs/REFERENTIELS-COMPETENCES.md) | **ESCO / O*NET / SFIA** bilingues : licences, formats, ingestion, crosswalk |
| [`DEPLOIEMENT-VERCEL.md`](docs/DEPLOIEMENT-VERCEL.md) | Déploiement du front sur Vercel + backend local (cross-origin, auth Bearer) |

---

## Structure du dépôt

```
bmci-gestion-carrieres/
├── README.md
├── docs/                     # Architecture & décisions techniques (ci-dessus)
├── backend/                  # ⏳ FastAPI (MVC + SQLAlchemy) — miroir smart-objective
│   └── app/{auth,controllers,core,database,middlewares,models,repositories,schemas,services,utils,tests}
├── frontend/                 # ⏳ Vue 3 (Vite, Tailwind, Pinia)
│   └── src/{components,guards,layouts,router,services,stores,utils,views}
├── ia/                       # 🧠 Brique IA locale
│   ├── modelfiles/           #   Modelfiles Ollama (un par tâche)
│   ├── referentiels/         #   ESCO/O*NET/SFIA ingérés + graphe de compétences
│   └── pipelines/            #   extraction, matching, reranking, agents
└── scripts/                  # Lancement, vérification, ingestion
```

---

## Principe directeur (hérité de smart-objective)

1. **Le frontend ne connaît ni l'IA ni la base** : tout passe par `/api/*`.
2. **Le backend est l'unique source de vérité** : auth, RBAC, appels IA, persistance.
3. **L'IA tourne en local** (Ollama `:11434`, jamais exposé) : **aucune donnée ne sort**.
4. **Confidentialité bancaire par conception** : RBAC strict, audit trail, cloisonnement des données par rôle.

---

*École Centrale Casablanca × BMCI — 2026*
