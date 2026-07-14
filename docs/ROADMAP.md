# Feuille de route — BMCI Gestion des Carrières

Liste **factuelle et exhaustive** des briques. Légende : ✅ fait · ⏳ en cours · ⬜ à faire · 🅿️ différé/hors scope.
Mise à jour : session de développement en cours.

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
- ⬜ Brancher les **modèles en réserve** : `llama3.1:8b` (normalisation), `qwen3:8b` (agent),
  `qwen3.6` (raisonnement lourd batch)
- ⬜ **Modelfiles spécialisés** (lc-extracteur, lc-conseiller…) — optimisation
- ⬜ **Orchestration agentique** (function calling) pour tâches multi-étapes
- ⬜ **Benchmark systématique** par tâche sur données réelles → affiner routing.yaml

## III. Modèle métier & données
- ✅ Entité **`Fiche`** (référence) + **`FicheCompetence`** (attendus typés + ancrés)
- ✅ Cartographie **33 départements → 164 métiers** (éditable)
- ✅ **Gabarit de fiche** éditable (`config/fiche_schema.yaml`)
- ⏳ **Génération + persistance de ~164 fiches** (batch mistral-nemo en cours)
- ⬜ Entité **`Offre`** (dérive d'une Fiche ; attendus *overridables* au niveau offre ;
  types offre/mission/projet/gig ; statut/dates ; poussée par RH/manager) + CRUD
- ⬜ Entité **`Candidature`** (profil ↔ offre → score + écarts + statut) + CRUD
- ⬜ Entité **`Collaborateur / Profil`** (compétences détenues, niveau, historique, aspirations)
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

## V. Authentification, identité & sécurité (à porter de smart-objective)
- ⬜ **SSO SAML 2.0** (ADFS / Entra ID) + JIT provisioning + mode simulation (dev)
- ⬜ **Auth locale** de secours + sessions (cookies HttpOnly/Secure/SameSite + CSRF)
- ⬜ **RBAC** (COLLAB / MANAGER / RH / ADMIN / SERVICE) + guards sur toutes les routes
- ⬜ **Répertoire des comptes** : réels (JIT) · service (connecteurs) · synthétiques (personas démo)
- ⬜ **Audit trail** (accès profils, matching, exports, éditions gabarit)
- ⬜ **Sécurité applicative** : rate-limit IA, taille requête, en-têtes sécu, CORS strict,
  PBKDF2, anti-brute-force
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

## VIII. Qualité, tests & lancement
- ⬜ Suite **pytest** (sécurité, RBAC, matching, extraction) — **gardé** (appli sensible)
- ⬜ Migrations **Alembic** — **RETENU** : faire évoluer le schéma (Offre/Candidature/Profil)
  **sans recréer la base ni perdre les fiches persistées** (à mettre en place bientôt)
- ⬜ **Scripts de lancement** dev (`LANCER_APP.bat` / `start_app.sh` / `VERIFIER.*`)
- 🅿️ **CI** (GitHub Actions) · **PostgreSQL + pgvector** · **Docker** — optionnels (surtout prod → hors scope)
- 🅿️ **Mise en production banque** (HTTPS, multi-worker, supervision, DSI) — **pas nous**
- ⬜ Confirmer la **licence SFIA** si un jour usage production (info à garder)

## IX. En attente / hors scope immédiat (rappels)
- ⬜ Passage **MSI Extreme Performance** (rechiffrer les perfs) — quand tu veux
