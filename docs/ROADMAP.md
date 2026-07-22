# Feuille de route — BMCI Gestion des Carrières

Liste **factuelle et exhaustive** des briques. Légende : ✅ fait · ⏳ en cours / partiel · ⬜ à faire · 🅿️ différé/hors scope.
**Mise à jour : 2026-07-21** — statuts réconciliés avec le code (`backend/app/…`) et la base
(`bmci_carrieres.db`). Preuves relevées : 164 fiches + 2 939 compétences persistées ;
tables `offres`/`candidatures`/`profils` créées via `create_all` (baseline Alembic = stamp vide) ;
guards RBAC branchés (`Depends` dans tous les controllers) mais `users=0`/`audit_logs=0` ;
SAML = placeholder documenté seulement.

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
- ⬜ Brancher les **modèles en réserve** : `llama3.1:8b` (normalisation), `qwen3:8b` (agent),
  `qwen3.6` (raisonnement lourd batch)
- ⬜ **Modelfiles spécialisés** (lc-extracteur, lc-conseiller…) — optimisation
- ⬜ **Orchestration agentique** (function calling) pour tâches multi-étapes
- ⬜ **Benchmark systématique** par tâche sur données réelles → affiner routing.yaml

## III. Modèle métier & données
- ✅ Entité **`Fiche`** (référence) + **`FicheCompetence`** (attendus typés + ancrés)
- ✅ Cartographie **33 départements → 164 métiers** (éditable)
- ✅ **Gabarit de fiche** éditable (`config/fiche_schema.yaml`)
- ✅ **Génération + persistance de 164 fiches** — **TERMINÉ** (164 fiches, 2 939 `fiche_competences` en base)
- ✅ Entité **`Collaborateur / Profil`** + **CRUD** (compétences détenues, aspirations) — controller/service branchés
- ⏳ Entité **`Offre`** — **modèle + table `offres`/`offre_competences` créés ; CRUD (controller/service/schémas) À FAIRE**
  (dérive d'une Fiche ; attendus *overridables* ; types offre/mission/projet/gig ; statut/dates ; poussée RH/manager)
- ⏳ Entité **`Candidature`** — **modèle + table `candidatures` créés ; CRUD (controller/service/schémas) À FAIRE**
  (profil ↔ offre → score + écarts + statut)
- ⬜ **Niveau de maîtrise & historique** sur les compétences de profil (aujourd'hui présence binaire) — cf. I
- ⬜ **Persistance des résultats** de matching/reco (traçabilité)

## IV. Fonctionnalités métier (IA + graphe)
- ✅ **Extraction de compétences** d'un descriptif de poste (hermes3)
- ✅ **Extraction de fiche de poste structurée** (gabarit BMCI, compétences typées)
- ✅ **Matching profil ↔ poste** (score + écarts, reranker)
- ✅ **Recommandations formation & parcours** (mistral-nemo, ancré)
- ✅ **Génération de fiches de poste** (compétences inférées)
- ⬜ **Extraction de compétences d'un CV / profil** (symétrique du poste)
- ⬜ **Matching candidat ↔ offre** (sur entités persistées) + pondération essentiel/souhaité
  + prise en compte du **niveau** + logique « < 100 % peut être retenu »
- ⬜ **Recommandation de candidats internes** pour une offre (sens inverse du matching)
- ⬜ **Succession planning / hauts potentiels** (viviers, cartographie RH)
- ⬜ **Passerelles de mobilité** intégrées au profil (déjà ébauché via vec_occupations)
- ⬜ Extraction depuis **évaluations de mission (managers)** et **évaluations de performance**
- ⬜ **Dashboards RH — cartographie des compétences EN DIRECT + PONCTUELLE** (vue globale des
  compétences de la banque, couverture, tensions, hauts potentiels) — demandé explicitement
- 🅿️ **Mini-jeux** de détection de compétences par thème (plus tard, recherches approfondies)

## V. Authentification, identité & sécurité (priorité centrale)
- ⏳ **Auth locale** + sessions — **code posé** (`auth_service`, `core/security`, tables `users`/`user_sessions`) ;
  reste : **seed des comptes/personas, tests, durcissement** (`users=0` aujourd'hui)
- ⏳ **RBAC** (COLLAB / MANAGER / RH / ADMIN / SERVICE) — **guards branchés** sur les routes
  (`Depends` présents dans tous les controllers) ; reste : **valider la couverture route par route + tests**
- ⏳ **Audit trail** — **code posé** (`audit_service`, table `audit_logs`) ; reste : **brancher sur toutes les
  actions sensibles + vérifier** (`audit_logs=0` aujourd'hui)
- ⬜ **CSRF** — à confirmer branché de bout en bout (cookies HttpOnly/Secure/SameSite)
- ⬜ **SSO SAML 2.0** (ADFS / Entra ID) + JIT provisioning + mode simulation (dev) — **placeholder documenté seulement**
- ⬜ **Répertoire des comptes** : réels (JIT) · service (connecteurs) · synthétiques (personas démo) — non seedé
- ⬜ **Sécurité applicative** : rate-limit IA, taille requête, en-têtes sécu, CORS strict,
  PBKDF2, anti-brute-force — à auditer/compléter (primitives partielles dans `core/security.py`)
- ⬜ **RGPD / CNDP** : consentement, minimisation, droit de regard du collaborateur
- ⬜ **Édition gabarit + cartographie via UI protégée RBAC** (aujourd'hui = fichiers YAML)

## VI. Intégrations
- 🅿️ Connecteurs **SIRH HCM** (Workday / SAP…) : différés — **prévoir un point d'intégration/
  adaptateur propre** pour faciliter le branchement futur, mais **ne pas construire les connecteurs**
- ⬜ **Catalogue de cours SYNTHÉTIQUE** (à la place du LMS réel) : recherche internet de cours par
  métier → **génération de propositions/maquettes de cours** pour démontrer la reco. Suivi/avancement
  des cours = **optionnel** (les LMS le gèrent en interne — à trancher)
- ⬜ **Import Excel** (fiches, profils réels traités localement) — pattern smart-objective
- 🅿️ Comptes de **service** + tokens : différés (partent avec les connecteurs)

## VII. Frontend (Vue 3, haut de gamme)
- ⬜ **Scaffolding** Vue 3 / Vite / Tailwind / Pinia / vue-router (depuis la maquette)
- ⬜ Implémentation des **34 écrans**, 3 rôles (Collaborateur / Manager / RH) + Accès/transversal
- ⬜ **Câblage aux API** (apiService, authService, guards RBAC)
- ⬜ Composants transversaux : **modale, toast, états vides, fil d'ariane**
- ⬜ **Dashboards analytiques** RH (cartographie compétences, couverture, hauts potentiels)
- ⬜ Écran **édition gabarit / cartographie** (accès autorisé)
- ⬜ **Mentions légales & crédits** (attributions ESCO/O*NET/SFIA — obligation légale)
- ⬜ **Photos réelles** (4 portraits déjà intégrés dans la maquette) + **blanc/vert, jamais de sombre**

> Note : les **3 maquettes HTML par rôle** (collab / manager / RH) existent dans `design/` — base de l'implémentation.

## VIII. Qualité, tests & lancement
- ⏳ Suite **pytest** — **échafaudage posé** (`app/tests/conftest.py`, `test_profil.py`) ;
  reste : **couvrir sécurité, RBAC, matching, extraction** (appli sensible)
- ⏳ Migrations **Alembic** — **baseline `895f8467eae9` = stamp vide** du `create_all` ;
  reste : **éprouver le workflow de migration incrémentale** (faire évoluer Offre/Candidature/niveau
  **sans recréer la base ni perdre les 164 fiches**)
- ⬜ **Scripts de lancement** dev (`LANCER_APP.bat` / `start_app.sh` / `VERIFIER.*`)
- 🅿️ **CI** (GitHub Actions) · **PostgreSQL + pgvector** · **Docker** — optionnels (surtout prod → hors scope)
- 🅿️ **Mise en production banque** (HTTPS, multi-worker, supervision, DSI) — **pas nous**
- ⬜ Confirmer la **licence SFIA** si un jour usage production (info à garder)

## IX. En attente / hors scope immédiat (rappels)
- ⬜ Passage **MSI Extreme Performance** (rechiffrer les perfs) — quand tu veux
