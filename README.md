# 🌿 BMCI Carrière — « La Courbe »

Plateforme RH de **gestion de carrière et de mobilité interne** propulsée par une
**IA 100 % locale et open source**, pour la BMCI (Groupe BNP Paribas). Elle aide
collaborateurs, managers et RH à **cartographier les compétences, matcher les
talents aux opportunités, planifier les évolutions et la succession** — sans
jamais faire sortir une seule donnée de l'infrastructure de la banque.

> Version **0.1 (fondation)** — Frontend **Vue 3 / Vite / Tailwind**, backend
> **Python FastAPI** en architecture **MVC + SQLAlchemy**, **multi-modèles IA
> Ollama locaux** (un modèle spécialisé par tâche), référentiels de compétences
> **ESCO + O*NET + SFIA** (FR/EN), **SSO SAML 2.0**. Le backend reste l'unique
> source de vérité. Aucune donnée ne quitte la machine.

Ce projet **réplique les bonnes pratiques** du projet frère *ObjectifSMART-AI*
(`bmci-smartobjective`) et **élève le niveau graphique** par rapport à la
maquette UI/UX initiale (voir `design/`).

---

## Où en est-on ?

| Volet | État |
|---|---|
| Cartographie des parcours & maquette UI/UX (34 écrans, 3 rôles) | ✅ fait — dans `design/` |
| Fondation du dépôt (structure, docs d'architecture) | ✅ en cours (ce commit) |
| Recherche modèles IA locaux + référentiels | ✅ documentée (`docs/`) |
| Ingestion des référentiels (ESCO/O*NET/SFIA) | ⏳ à construire |
| Backend FastAPI (auth, RBAC, services IA) | ⏳ à construire |
| Frontend Vue (implémentation des écrans maquettés) | ⏳ à construire |
| SSO SAML + provisioning | ⏳ à porter depuis smart-objective |

---

## Documentation d'architecture (`docs/`)

| Document | Contenu |
|---|---|
| [`ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Vue d'ensemble, couches, flux de données, **briques techniques**, adéquation matériel |
| [`IA-MODELES-LOCAUX.md`](docs/IA-MODELES-LOCAUX.md) | **Un modèle par tâche** : embeddings, reranking, extraction, génération, agent — VRAM, install, sources |
| [`REFERENTIELS-COMPETENCES.md`](docs/REFERENTIELS-COMPETENCES.md) | **ESCO / O*NET / SFIA** bilingues : licences, formats, ingestion, crosswalk |
| [`SSO-SAML-ET-IDENTITE.md`](docs/SSO-SAML-ET-IDENTITE.md) | SAML 2.0, JIT provisioning, **répertoire des comptes** (réels, service, synthétiques) |

---

## Structure du dépôt

```
bmci-lacourbe/
├── README.md
├── docs/                     # Architecture & décisions techniques (ci-dessus)
├── design/                   # 🎨 Travail UI/UX déplacé ici
│   ├── maquette/             #   prototype HTML (34 écrans) + pipeline d'assemblage
│   └── assets/               #   portraits (personas) et ressources
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
