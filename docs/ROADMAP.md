# Feuille de route — BMCI Gestion des Carrières

Liste **factuelle et exhaustive** des briques. Légende : ✅ fait · ⏳ en cours / partiel · ⬜ à faire · 🅿️ différé/hors scope.
**Mise à jour : 2026-07-29** — moteur IA complété. Depuis le 2026-07-27 :
**Coach Carrière agentique** (function-calling sur données réelles) + **streaming SSE** (`/api/coach`, `/stream`) ;
**reco non bloquante** (cache + job async `/ma-reco/async` + polling) ; **3 tâches IA « dormantes » activées** —
`normalisation` (llama3.1 → `POST /competences/normaliser`), `redaction` (mistral-nemo → `POST /redaction`),
`raisonnement_batch` (qwen3.6 → **plan de succession** `POST /rh/succession`, e2e vérifié 162 s) ; **matching inverse**
(candidats d'une offre `GET /offres/{id}/candidats`) ; **pytest 79 verts** ; **~57 routes** déclarées.
Socle (≤ 2026-07-27) : CRUD Offre/Candidature, auth locale + RBAC + audit + CSRF, 5 migrations Alembic,
frontend Vue mock-first complet. Base : **164 fiches / 2 939 compétences** (préservées à chaque migration/seed).

> ### 🎯 Cadrage retenu (décisions utilisateur)
> - **🔒 La SÉCURITÉ est la priorité CENTRALE** — à traiter tôt, en première classe.
> - **Dashboards RH de cartographie des compétences (direct + ponctuelle)** = à faire (ne pas oublier).
> - **Connecteurs SIRH HCM** (Workday/SAP) : 🅿️ différés — juste **faciliter le branchement futur**.
> - **LMS** : pas d'accès au catalogue → **rechercher des cours par métier + générer des maquettes
>   de cours SYNTHÉTIQUES** pour démontrer la reco. Suivi de cours = optionnel.
> - **Comptes de service** : 🅿️ différés (partent avec les connecteurs).
> - **Mise en production banque** : 🅿️ hors scope (pas nous) → Postgres/Docker/CI optionnels ; SQLite suffit.
> - **Alembic RETENU** (migrations) + **tests pytest** gardés. **MàJ référentiels** : 🅿️ côté BMCI.
> - **Mini-jeux** : plus tard. · **Jamais de mode sombre.** · **34 écrans + d'autres si les workflows l'exigent.**

---

## I. Socle de connaissance — graphe de compétences
- ✅ Ingestion **ESCO** (pivot, 13 939 compétences, 3 039 métiers) — bilingue FR/EN
- ✅ Ingestion **O*NET** (66 compétences, 1 016 métiers) + attribution
- ✅ Ingestion **SFIA 9** (147 compétences, niveaux 1-7) — FR+EN
- ✅ Vectorisation complète (`vec_skills` 14 173, `vec_occupations` 4 059)
- ✅ **Crosswalk** O*NET/SFIA → ESCO (188 alignements) + dédoublonnage dans la recherche
- ✅ Mentions d'**attribution** obligatoires stockées (ESCO/O*NET/SFIA)
- ⬜ **Traduction FR des libellés O*NET** (graphe 100 % francophone)
- ⬜ **Référentiel interne BMCI** (compétences maison hors ESCO/SFIA : Bâle III, produits BMCI…)
- ⬜ **Modélisation du NIVEAU de maîtrise** (1-5 / niveaux SFIA) — aujourd'hui présence binaire
- 🅿️ **MàJ des référentiels** (ré-ingérer nouvelles versions) — **hors scope, côté BMCI**

## II. Moteur IA (routage multi-modèles)
- ✅ `ai_router` + `ia/routing.yaml` (le bon modèle par tâche, éditable en 1 ligne)
- ✅ Embeddings **bge-m3** par lots (`/api/embed`) + garde-fou bissection
- ✅ Reranker **bge-reranker-v2-m3** (CPU, offline)
- ✅ Optimisation **num_ctx** (indispensable 8 Go VRAM)
- ✅ Résilience : repli automatique sur modèle fallback en cas d'erreur d'infra ; batch résilient par fiche
- ✅ Brancher les **modèles en réserve** : `llama3.1:8b` (normalisation → `POST /competences/normaliser`),
  `qwen3:8b` (agent → Coach), `qwen3.6` (raisonnement batch → plan de succession) — les 3 tâches « dormantes » activées
- ✅ **Orchestration agentique** (function calling) — Coach Carrière : boucle outil → observation → réponse,
  outils déterministes (offres compatibles, formations), + **streaming SSE**, repli mono-coup si Ollama down
- ✅ **Utilitaire de rédaction** IA (`mistral-nemo`) : résumé / reformulation ancrés (`POST /redaction`)
- ⬜ **Modelfiles spécialisés** (lc-extracteur, lc-conseiller…) — optimisation
- ⏳ **Benchmark systématique** par tâche sur données réelles → affiner routing.yaml
  (mesures ad hoc faites : reco cache, latence Coach, succession qwen3.6)

## III. Modèle métier & données
- ✅ Entité **`Fiche`** (référence) + **`FicheCompetence`** (attendus typés + ancrés)
- ✅ Cartographie **33 départements → 164 métiers** (éditable)
- ✅ **Gabarit de fiche** éditable (`config/fiche_schema.yaml`)
- ✅ **Génération + persistance de 164 fiches** — **TERMINÉ** (164 fiches, 2 939 `fiche_competences` en base)
- ✅ Entité **`Collaborateur / Profil`** + **CRUD** (compétences détenues, aspirations) — controller/service branchés
- ✅ Entité **`Offre`** + **CRUD complet** (`/api/offres`) — dérive d'une Fiche, attendus *overridables*,
  types offre/mission/projet/gig, statut/dates auto, poussée RH/manager
- ✅ Entité **`Candidature`** + **CRUD** (`/api/candidatures`) — profil ↔ offre → score `entites_v1`
  + snapshot des écarts persisté + **décision humaine** (< 100 % retenable) + réévaluation tracée (`reevaluated_at`)
- ✅ Entités applicatives : **`Notification`**, **`Souhait`** (+ `/recus`), **`Formation`** (catalogue),
  **`ProfilStation`/`PeerReview`** (carrière), **`Entretien`** (veille) — endpoints livrés (cf. IV bis)
- ⏳ **Niveau de maîtrise** (1-5) présent (profils/attendus/évaluation) ; **historique dans le temps** ⬜
- ✅ **Persistance des résultats** : la candidature persiste son snapshot ; endpoints matching/reco autonomes livrés
  (`/matching`, `/offres/compatibles`, `/ma-reco` + `/ma-reco/async` non bloquant + polling)

## IV. Fonctionnalités métier (IA + graphe)
- ✅ **Extraction de compétences** d'un descriptif de poste (hermes3)
- ✅ **Extraction de fiche de poste structurée** (gabarit BMCI, compétences typées)
- ✅ **Matching profil ↔ poste** (score + écarts, reranker)
- ✅ **Recommandations formation & parcours** (mistral-nemo, ancré)
- ✅ **Génération de fiches de poste** (compétences inférées)
- ✅ **Extraction de compétences d'un CV / profil** (symétrique du poste) — `POST /api/profils/{id}/extraction-cv`
  (`cv_extraction_service`) : extraction IA (hermes3, CV fencé) + ancrage graphe, persiste les compétences
  DÉTENUES (`source=cv`, niveau estimé, idempotent via remplacement) ; ownership propriétaire / RH-ADMIN, rate-limité
- ✅ **Matching candidat ↔ offre** (sur entités persistées) — `candidature_service.evaluer` : **pondération**
  essentiel(1.0)/souhaité(0.5), prise en compte du **niveau** (`niveau_insuffisant`), logique « < 100 % peut être
  retenu » (décision humaine `PATCH /decision`). `skill_matching_service` pondère aussi (matching profil↔texte).
- ✅ **Recommandation de candidats internes** pour une offre (sens inverse du matching) — `GET /api/offres/{id}/candidats`
- ✅ **Succession / hauts potentiels** — `/api/dashboards/hauts-potentiels` (proxy = niveau moyen) + **plan de
  succession raisonné dédié** `POST /api/rh/succession` (qwen3.6, cartographie réelle fencée) ; viviers formalisés ⬜
- ✅ **Passerelles de mobilité** intégrées au profil — `GET /api/profils/{id}/mobilite`
  (`occupation_service.suggest_occupations`, pondéré par rareté type-IDF, pur graphe sans LLM) : métiers ESCO/O*NET
  mobilisant le plus les compétences détenues ancrées, hors poste actuel ; ownership propriétaire / manager / RH-ADMIN
- ✅ Extraction depuis **évaluations de mission (managers)** et **évaluations de performance** —
  `POST /api/profils/{id}/extraction-evaluation` (`cv_extraction_service.extraire_evaluation`) : compétences
  DÉMONTRÉES ancrées, `source=evaluation_mission|evaluation_performance` (idempotent par type) ;
  ownership RH/ADMIN **ou manager du profil** (jamais l'auto-déclaration), rate-limité
- ✅ **Dashboards RH — cartographie des compétences** (`/api/dashboards/cartographie` : effectif, niveau
  moyen, compétences phares par département) + **KPIs** RH/manager + **veille entretiens** + **alertes RH**
  dérivées de signaux réels — endpoints livrés
- ✅ Enrichir la cartographie — **vue par FAMILLE de compétences** (`GET /api/dashboards/familles`, RH/ADMIN) :
  offre interne détenue (profils / compétences / niveau moyen) confrontée à la DEMANDE des offres ouvertes
  → **signal de tension** par famille (indicatif), au-delà de l'agrégation par département.
  **Surfacé** : panneau « Tensions par famille » sous la heatmap dans `rh/CartographieView.vue`
- 🅿️ **Mini-jeux** de détection de compétences par thème (plus tard, recherches approfondies)

## IV bis. API applicative (endpoints alimentant le front) — ~62 routes déclarées
- ✅ **Notifications** : `GET /api/notifications`, `PATCH /{id}/lu`, `POST /lues` (filtré par utilisateur)
- ✅ **Souhaits d'évolution** : `GET/POST/PATCH /api/souhaits` (ownership) + `GET /api/souhaits/recus` (manager)
- ✅ **Formations** : `GET /api/formations` (catalogue synthétique filtrable domaine/texte)
- ✅ **Dashboards** : `GET /api/dashboards/{kpis?scope=rh|manager, cartographie, hauts-potentiels}`
- ✅ **RH analytics** : `GET /api/rh/veille`, `GET /api/rh/alertes`
- ✅ **Profil carrière** : `GET /api/profils/{id}/carriere` (stations + avis pairs + compétences) + filtre `manager_id` (équipe)
- ✅ **Coach Carrière** : `POST /api/coach` (agentique) + `POST /api/coach/stream` (SSE token par token)
- ✅ **Reco perso** : `GET /api/ma-reco` + `POST /api/ma-reco/async` + `GET /api/ma-reco/jobs/{id}` (non bloquant)
- ✅ **IA utilitaires** : `POST /api/competences/normaliser`, `POST /api/redaction`, `POST /api/rh/succession`
- ✅ **Notifications événementielles** (`services/notification_events.py`) — émises sur évènements RÉELS,
  atomiques avec la mutation : décision de candidature → candidat ; souhait poussé → manager ; souhait
  décidé (accordé/refusé) → collaborateur (3 tests e2e). Reste ⬜ : reco/formations reliées au matching,
  autres évènements (nouvelle offre compatible…)

## V. Authentification, identité & sécurité (priorité centrale)
- ✅ **Auth locale** + sessions — **opérationnelle** : `seed.py` provisionne 4 comptes (ADMIN/RH/MANAGER/COLLAB)
  + personas ; login/logout/me (`/api/auth/*`), sessions hachées, anti-brute-force ; **couverte par pytest**
- ✅ **RBAC** (COLLAB / MANAGER / RH / ADMIN) — **guards `require_roles` sur toutes les routes métier** +
  **ownership** (souhaits/notifications filtrés par utilisateur) ; **testé** (403/401 vérifiés)
- ✅ **Audit trail** — écrit (créations de comptes, accès refusés) ; **émis après commit** (verrou SQLite un seul writer)
- ✅ **CSRF** double-submit (cookie non-HttpOnly ↔ en-tête `X-CSRF-Token`) branché sur les méthodes mutantes
- ✅ **B2 — row-level ownership généralisé** (`auth/ownership.py`) : COLLAB à SON profil / SES candidatures,
  MANAGER à SON équipe (`manager_id`), RH/ADMIN global — appliqué aux souhaits/notifications ET désormais aux
  **profils** (liste bornée + lecture unitaire) et **candidatures** (dépôt + liste + lecture) ; 5 tests e2e.
  Reste ⬜ : périmètre par **OFFRE** sur decision/réévaluation (nécessite un ownership d'offre)
- 🅿️ **SSO SAML 2.0** (ADFS / Entra ID) + JIT provisioning — **ABANDONNÉ (décision utilisateur, hors scope)** :
  l'auth locale + RBAC + sessions + audit couvre le besoin de la maquette ; aucun IdP à brancher
- ⬜ **Répertoire des comptes** : réels (JIT) · service (connecteurs) · synthétiques (personas démo) — non seedé
- ✅ **Sécurité applicative** : **rate-limit des endpoints IA** (débit + concurrence, 429 + `Retry-After`,
  audité — `core/rate_limit.py`, 12 routes IA) ; **durcissement HTTP** (`core/http_hardening.py`, middleware
  ASGI pur, SSE-safe) : en-têtes sécu (nosniff, X-Frame-Options DENY, Referrer-Policy, Permissions-Policy,
  CSP stricte pour l'API + HSTS en prod) + **plafond de taille de requête** (413) ; **CORS** non-"*" ;
  **PBKDF2** (sel + itérations + comparaison temps constant) & **anti-brute-force** (verrouillage 429 après
  N échecs sur fenêtre glissante) — vérifiés & testés
- ⬜ **RGPD / CNDP** : consentement, minimisation, droit de regard du collaborateur
- ⏳ **Édition gabarit + cartographie** — **API RBAC livrée** (`PUT /api/fiches/gabarit`,
  `GET/PUT /api/fiches/cartographie`, RH/ADMIN) : validation AVANT écriture (400 si cassé, fichier intact),
  persistance atomique, rechargement à chaud, audité (`CONFIG_CHANGED`) ; **écran d'édition RH livré** ✅
  (`rh/ReferentielView.vue` : édition des sections du gabarit + des départements/métiers, validation, retour d'erreur)

## VI. Intégrations
- 🅿️ Connecteurs **SIRH HCM** (Workday / SAP…) : différés — **prévoir un point d'intégration/
  adaptateur propre** pour faciliter le branchement futur, mais **ne pas construire les connecteurs**
- ✅ **Catalogue de cours SYNTHÉTIQUE** (à la place du LMS réel) : table `Formation` + `GET /api/formations`
  + 10 seedées ; **génération IA** d'une formation ciblant une compétence — `POST /api/formations/generer`
  (RH/ADMIN, `formation_generation_service`, mistral-nemo, compétence ancrée au référentiel, option `persister`
  au catalogue, contenu `synthetique=True`). Suivi/avancement = optionnel. (« recherche internet » sans objet : 100 % local.)
- ✅ **Import Excel** de **profils** (openpyxl, 100 % local) — `POST /api/profils/import-excel` (RH/ADMIN) :
  en-têtes tolérants (nom obligatoire + prenom/matricule/poste/departement/competences), compétences → détenues,
  savepoint par ligne (une ligne fautive n'arrête pas l'import), fichier illisible → 400, bilan {importes, ignorees, erreurs}.
  (Import de fiches : même socle réutilisable si besoin.)
- 🅿️ Comptes de **service** + tokens : différés (partent avec les connecteurs)

## VII. Frontend (Vue 3, haut de gamme)
- ✅ **Scaffolding** Vue 3 / Vite / TS / Tailwind / Pinia / vue-router — app **mock-first complète** (`frontend/`)
- ✅ Implémentation des écrans, **3 rôles** (Collaborateur / Manager / RH) + Accès/transversal (mock-first)
- ⏳ **Câblage aux API** — `authService` **réel branché** (login/CSRF/guards) ✅ ; `apiService` encore **mock**
  → reste : **mappers** (`mapOffre/mapProfil/mapCandidature…`) + bascule **mock→live** domaine par domaine
  (tous les endpoints back existent désormais, cf. IV bis)
- ⏳ Composants transversaux : présents en mock ; **gestion d'erreurs HTTP** (401→connexion, 403→accès refusé, 429→lockout) à finaliser
- ✅ **Dashboards analytiques** RH branchés sur `/api/dashboards/*` + `/api/rh/*` ; **étoffés** : synthèse
  consolidée `GET /api/dashboards/synthese` (effectifs par pôle, pipeline candidatures, familles en tension)
  surfacée sur `rh/DashboardView.vue` ; panneau tensions par famille sur la Cartographie
- ✅ Écran **édition gabarit / cartographie** (RH) — `rh/ReferentielView.vue` : éditeur live (GET/PUT), catégorie
  conditionnelle au kind, métiers par ligne, toast + affichage d'erreur de validation. Vérifié dans le preview.
- ⬜ **Mentions légales & crédits** (attributions ESCO/O*NET/SFIA — obligation légale)
- ⬜ **Photos réelles** (4 portraits déjà intégrés dans la maquette) + **blanc/vert, jamais de sombre**

> Note : les **3 maquettes HTML par rôle** (collab / manager / RH) existent dans `design/` — base de l'implémentation.

## VIII. Qualité, tests & lancement
- ⏳ Suite **pytest** — **79 tests verts** (auth, RBAC, ownership, notifications, souhaits, formations,
  dashboards, cartographie, hauts-potentiels, carrière, veille, alertes, **Coach agentique + streaming**,
  **normalisation, rédaction, plan de succession**) ; reste ⬜ : matching/extraction CV, ownership B2
- ✅ Migrations **Alembic** — **workflow incrémental éprouvé** (chaque migration validée sur COPIE avant la
  vraie base). Révisions : `66913f77409f` (reevaluated_at) → `13cd08085178` (notifications/souhaits/formations)
  → `6e077337b0c7` (profil_stations/peer_reviews) → `3871a47d3323` (entretiens). **164 fiches préservées** partout.
  Point ouvert : baseline `895f8467eae9` à `upgrade()` vide → sur base NEUVE, bootstrap = `create_all`
- ⬜ **Scripts de lancement** dev (`LANCER_APP.bat` / `start_app.sh` / `VERIFIER.*`)
- 🅿️ **CI** (GitHub Actions) · **PostgreSQL + pgvector** · **Docker** — optionnels (surtout prod → hors scope)
- 🅿️ **Mise en production banque** (HTTPS, multi-worker, supervision, DSI) — **pas nous**
- ⬜ Confirmer la **licence SFIA** si un jour usage production (info à garder)

## IX. En attente / hors scope immédiat (rappels)
- ⬜ Passage **MSI Extreme Performance** (rechiffrer les perfs) — quand tu veux
