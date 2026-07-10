# Architecture — BMCI Carrière « La Courbe »

> Document vivant. Objectif : une plateforme de **talent intelligence** de niveau
> Eightfold / Gloat, mais **100 % locale, open source, déployable sur un seul PC**
> (puis sur serveur interne banque). Rien ne sort de l'infrastructure.

---

## 1. Ce que la plateforme doit savoir faire

Dérivé des cas d'usage du secteur (Eightfold, Gloat) et du cahier des charges BMCI :

| Capacité | Description | Brique IA principale |
|---|---|---|
| **Normalisation sémantique** | Nettoyer/normaliser intitulés de poste, compétences, formations (synonymes, langues) | Embeddings + LLM normaliseur |
| **Extraction de compétences** | Découper un rôle en tâches → **inférer les compétences** (référentiel ESCO/SFIA) | LLM extracteur + matching bi-encodeur |
| **Cartographie des compétences** | Graphe vivant reliant collaborateurs ↔ compétences ↔ rôles ↔ aspirations | Skill graph + embeddings |
| **Matching talents ↔ opportunités** | Score de correspondance profil ↔ offre / poste / mission, **interprétable** | Embeddings + reranker + features |
| **Recommandation personnalisée** | Mobilités, mentors, projets, **formations d'upskilling** | LLM conseiller (RAG sur le graphe) |
| **Planification des talents** | Vision RH : viviers, hauts potentiels, **succession** | Agent (multi-étapes) + LLM lourd |
| **Réduction des délais de recrutement** | Prioriser les candidats internes avant l'externe | Matching + reranker |

Chaque capacité est servie par **le modèle local le mieux adapté** — pas un seul
gros modèle générique (voir [`IA-MODELES-LOCAUX.md`](IA-MODELES-LOCAUX.md)).

---

## 2. Schéma d'ensemble

```
┌──────────────────────────┐     ┌───────────────────────────────┐     ┌──────────────────────────┐
│  Frontend Vue 3           │────▶│  Backend FastAPI (MVC)         │────▶│  Couche IA locale         │
│  Vite · Tailwind · Pinia  │ /api│  SQLAlchemy · Pydantic v2      │     │  Ollama :11434 (privé)    │
│  :3000                    │◀────│  :5001  (SOURCE DE VÉRITÉ)     │     │  + services embeddings/   │
└──────────────────────────┘     │  RBAC · audit · SAML           │     │    reranker (Python)      │
                                  └───────────────┬───────────────┘     └───────────┬──────────────┘
                                                  │                                 │
                                   ┌──────────────┴───────────────┐   ┌─────────────┴──────────────┐
                                   │  Données (source de vérité)   │   │  Graphe de compétences      │
                                   │  PostgreSQL + pgvector        │   │  ESCO ⊕ O*NET ⊕ SFIA (FR/EN)│
                                   │  (SQLite + sqlite-vec en dev) │   │  + embeddings vectoriels    │
                                   └───────────────────────────────┘   └─────────────────────────────┘
```

**Règle d'or** : le frontend ne parle jamais directement à Ollama, à la base, ni
au graphe. Tout transite par les endpoints `/api/*` du backend, qui applique
l'authentification, le RBAC et l'audit avant tout appel IA ou toute lecture de données.

---

## 3. Les couches

### 3.1 Frontend (`frontend/`) — Vue 3
Réimplémentation **fidèle et enrichie** de la maquette `design/` (34 écrans, 3 rôles).
Vite + Tailwind + Pinia (état) + vue-router (+ guards RBAC) + Chart.js (KPIs) +
lucide (icônes). Objectif graphique : **nettement au-dessus** du mockup — mais on
part du mockup comme référence d'ergonomie et de parcours.

### 3.2 Backend (`backend/app/`) — FastAPI, MVC + SQLAlchemy
Structure **identique à smart-objective** (patron éprouvé) :

- `controllers/` — routes `/api/*` (auth, saml, collab, manager, rh, ia, referentiels…)
- `services/` — logique métier (matching, reco, cartographie, succession…)
- `repositories/` — **toutes** les requêtes (aucun SQL ailleurs)
- `models/` — ORM SQLAlchemy · `schemas/` — Pydantic v2 (I/O bornées)
- `auth/` — IdentityProvider (local + SAML) · `core/` — config + sécurité
- `middlewares/` — taille requête (anti-DoS), en-têtes sécu · `utils/` · `tests/` — pytest

### 3.3 Couche IA locale (`ia/`)
Le **routeur IA** (`services/ai_router`) aiguille chaque demande vers la bonne brique :
- **Ollama** (`:11434`) pour les LLM (extraction, normalisation, conseil, agents) et
  l'embedding `bge-m3` ;
- un **service Python** (FlagEmbedding / Text-Embeddings-Inference) pour le
  **reranker** `bge-reranker-v2-m3` (Ollama ne rerank pas bien).

Détail complet des modèles → [`IA-MODELES-LOCAUX.md`](IA-MODELES-LOCAUX.md).

### 3.4 Données
- **Source de vérité métier** : PostgreSQL (prod) / SQLite (dev) via SQLAlchemy.
- **Vecteurs** : `pgvector` (prod) / `sqlite-vec` (dev — déjà utilisé dans smart-objective).
- **Graphe de compétences** : tables relationnelles (compétences, relations
  hiérarchiques/transversales, mappings inter-référentiels) + colonnes vectorielles.
  Neo4j reste une option si les requêtes de graphe deviennent lourdes (succession).

---

## 4. Le cœur : moteur de compétences & de matching

C'est l'équivalent local du « Context Engine » de Gloat / du matching d'Eightfold.

```
Descriptif de poste / CV / profil
        │
        ▼
[1] Normalisation ── LLM normaliseur (lc-normaliseur) : nettoie, dé-duplique, FR/EN
        │
        ▼
[2] Extraction ───── LLM extracteur (lc-extracteur) : rôle → tâches → compétences (JSON)
        │
        ▼
[3] Ancrage ──────── embeddings bge-m3 → recherche des k compétences ESCO/SFIA proches
        │                                   (dans le graphe vectoriel)
        ▼
[4] Reranking ────── bge-reranker-v2-m3 : reclasse les candidats (query, compétence)
        │
        ▼
[5] Harmonisation ── mapping vers le référentiel unifié (ESCO ⊕ O*NET ⊕ SFIA)
        │
        ▼
Compétences normalisées + scores interprétables  →  stockées dans le graphe
```

Le **matching profil ↔ opportunité** réutilise les étapes [3]–[4] : on embed le
profil et l'offre, on récupère les plus proches, on rerank, et on expose un
**score décomposé** (compétences couvertes / manquantes, proximité de rôle,
séniorité SFIA) — jamais une boîte noire.

---

## 5. Orchestration multi-modèles

Un **routeur** choisit le modèle selon la tâche, la latence acceptable et la
charge VRAM. Principe : petits modèles spécialisés (JSON strict, `temperature 0`)
pour les tâches structurées ; modèle lourd **uniquement** pour le raisonnement
batch hors-ligne (succession, planification).

| Tâche | Modèle | Où | Latence |
|---|---|---|---|
| Embeddings | `bge-m3` | Ollama/GPU ou CPU | ms |
| Reranking | `bge-reranker-v2-m3` | service Python/GPU | ms |
| Extraction compétences | `lc-extracteur` (Qwen3-8B) | Ollama/GPU | ~s |
| Normalisation | `lc-normaliseur` (Qwen3-8B) | Ollama/GPU | ~s |
| Recommandation / conseil | `lc-conseiller` (Qwen3-8B) | Ollama/GPU | ~s |
| Planification / succession (batch) | `qwen3.6` (23 Go) | CPU+RAM | offline |
| Agent multi-étapes | Qwen3-8B (function calling) | Ollama/GPU | ~s×n |

---

## 6. Briques techniques (inventaire)

| Domaine | Brique | Choix |
|---|---|---|
| Web API | Framework | **FastAPI** + Uvicorn |
| ORM | Persistance | **SQLAlchemy 2.0** + Alembic (migrations) |
| Base | Métier | **PostgreSQL** (prod) / **SQLite** (dev) |
| Vecteurs | Recherche sémantique | **pgvector** / **sqlite-vec** |
| Validation | I/O | **Pydantic v2** |
| IA — LLM | Inférence locale | **Ollama** (Qwen3, modelfiles spécialisés) |
| IA — embeddings | Vectorisation | **BGE-M3** (multilingue) |
| IA — reranker | Précision top-k | **bge-reranker-v2-m3** (FlagEmbedding / TEI) |
| Référentiels | Compétences | **ESCO** + **O*NET** + **SFIA** (voir doc dédiée) |
| Orchestration | Multi-étapes | Orchestrateur maison léger (agents Qwen3 function-calling) |
| Auth | SSO | **python3-saml** (SAML 2.0, ADFS / Entra ID) + local |
| Sécurité | Transport/session | cookies HttpOnly/Secure/SameSite + CSRF + PBKDF2 |
| Sécurité | Périmètre | RBAC strict, audit trail, rate-limit, en-têtes sécu, anti-DoS |
| Frontend | SPA | **Vue 3** + Vite + Tailwind + Pinia + vue-router + Chart.js |
| Conteneurs | Repro / prod | **Docker** (Ollama + Postgres + backend + frontend) |
| CI | Qualité | GitHub Actions (lint, tests pytest, build front) |
| Lancement | DX | `LANCER_APP.bat` / `start_app.sh` + `VERIFIER.*` (préflight) |

---

## 7. Adéquation matériel (ton PC)

**Ryzen 9 7945HX (16C/32T) · 32 Go RAM · RTX 5060 Laptop 8 Go VRAM · 540 Go libres · Ollama/Docker/conda/git présents.**

Contrainte réelle : **8 Go de VRAM** ne permettent pas de charger *simultanément*
un LLM 8B + embeddings + reranker sur le GPU. Stratégie :

- **LLM (Qwen3-8B Q4 ≈ 5,2 Go)** sur le **GPU**.
- **Embeddings `bge-m3` (1,2 Go)** et **reranker (~0,6 Go)** sur le **CPU**
  (ONNX/llama.cpp) — largement assez rapide sur un Ryzen 9, et libère la VRAM.
- **`qwen3.6` (23 Go)** → **CPU + 32 Go RAM**, réservé aux **traitements batch
  hors-ligne** (succession, planification) où la latence n'importe pas.
- Ollama gère le **chargement/déchargement à la demande** : un seul LLM chaud à la fois.

➡️ Le PC est **largement suffisant** pour le dev et une démo complète. La
production banque tournera sur serveur (GPU dédié ou parc CPU) sans changer le code.

---

## 8. Sécurité & confidentialité (par conception)

- **Aucune sortie de données** : Ollama et le graphe restent locaux ; `:11434` n'est jamais exposé.
- **RBAC strict** : COLLAB / MANAGER / RH / ADMIN, cloisonnement des données par périmètre.
- **Audit trail** : journalisation des évènements sensibles (accès profils, matching, exports).
- **Traçabilité IA** : chaque score de matching est **explicable** (compétences couvertes/manquantes).
- **RGPD / éthique** : la cartographie des compétences touche des données sensibles →
  consentement, minimisation, droit de regard du collaborateur (déjà prévu dans la maquette :
  écran « Confidentialité »).

> Détails identité/SSO → [`SSO-SAML-ET-IDENTITE.md`](SSO-SAML-ET-IDENTITE.md).
