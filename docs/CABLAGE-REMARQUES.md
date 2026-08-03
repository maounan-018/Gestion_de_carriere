# Câblage frontend ↔ backend — registre des remarques & blocages

> Journal vivant de tout ce qui bloque, manque, ou a été contourné pendant le
> branchement du frontend Vue sur l'API FastAPI. Tenu à jour au fil des chantiers.
> Sévérité : 🔴 bloquant · 🟠 à traiter · 🟡 dette/finition · ✅ fait.
>
> Dernière mise à jour : 2026-08-03.

---

## 0. Chantier A→D + finitions (2026-08-03) — suite de l'audit plateforme

Points de l'audit du 2026-08-02 traités :

- **A · Cartographie sur l'organigramme RÉEL.** `_seed_carto` (backend `database/seed.py`) réécrit
  sur le référentiel `config/departements_metiers.yaml` : **67 profils synthétiques répartis sur les
  33 départements / 6 pôles macro réels** (au lieu de 6 clés inventées). `dashboard_service.cartographie()`
  libelle chaque ligne via le référentiel (`nom` + `pole`) et **regroupe la heatmap par pôle** (schéma
  `CartoLigne.pole`, mapper + type front + `Heatmap.vue` intertitres). Mock front (`data/rh.ts`) réaligné
  sur les 6 familles réelles + départements réels groupés par pôle. **Live vérifié : 33 lignes riches.**
- **B · Souhaits création/édition câblés** : `apiService.createSouhait` (`POST /souhaits`) +
  `updateSouhait` (`PATCH /souhaits/{id}`) ; `SouhaitsView` a un vrai formulaire (BaseModal). Fin des toasts « à venir ».
- **C · Retrait de candidature** ajouté : `PATCH /candidatures/{id}/retrait` (ownership : candidat ou RH/ADMIN)
  → statut `retiree` ; front `apiService.retirerCandidature` + bouton « Retirer » (MesCandidatures) ; statut
  front `Retirée` distinct de `Refusée`.
- **Finitions** : `.env.example` (front) créé ; `ALLOWED_ORIGINS` inclut `:3001` ; **attestation de formation**
  implémentée (modale, marquée « démonstration »). Réévaluation : **déjà câblée** (RevueCandidats). Voir lignes ci-dessous.

---

## 1. Écritures / persistance (#1)

| # | Sév. | Remarque | Détail / recommandation |
|---|------|----------|-------------------------|
| 1.1 | ✅ | **Postuler** persiste | `POST /api/candidatures` câblé (OffreDetailView collab). 201 vérifié + garde doublon 400. |
| 1.2 | ✅ | **Notifications lues** persistent | `PATCH /notifications/{id}/lu` + `POST /notifications/lues` (3 vues). 200 vérifié. |
| 1.3 | ✅ | **Décision candidat** persiste | `PATCH /candidatures/{id}/decision` (RevueCandidats RH). 200 sur les 3 statuts. |
| 1.4 | ✅ | **Retrait de candidature (2026-08-03)** — `PATCH /candidatures/{id}/retrait` (ownership : candidat ou RH/ADMIN) pose `statut=retiree` ; front `retirerCandidature` + bouton « Retirer ». Retrait logique (pas de DELETE dur, trace conservée). |
| 1.5 | ✅ | **Édition profil : RH + self-service collab** | RH : `PATCH /profils/{id}`. **`PATCH /profils/me`** existe (`profil_controller.py:94`) → édition self-service du collaborateur débloquée backend. |
| 1.6 | ✅ | **Souhaits : pousser + créer + éditer (2026-08-03)** | `pushSouhait` + **`createSouhait` (`POST /souhaits`)** + **`updateSouhait` (`PATCH /souhaits/{id}`)** ; `SouhaitsView` a un vrai formulaire (BaseModal). Fin des toasts « à venir ». |
| 1.7 | ✅ | **Publier une offre persiste** | `apiService.publishOffer` → `POST /offres` (brouillon, `synthetique`). Modale manager câblée. **Règle backend découverte** : un **MANAGER ne peut publier qu'une mission/projet, pas un POSTE (403)** ; les postes sont réservés à la RH → modale manager restreinte à Mission/Projet. *Reste : côté RH le bouton « Publier » n'a pas encore de modale.* |
| 1.8 | 🟡 | **Statuts candidature : front plus riche que back** | Le front distingue `entretien`/`preselection` ; le backend n'accepte que `en_evaluation`/`retenue`/`rejetee`. **Choix DIFFÉRÉ assumé (2026-08-03)** : élargir l'automate d'états (enum modèle + `CandidatureDecision` + notifications) pour un gain 🟡 n'est pas justifié ; le flux reste fonctionnel (les deux persistent en `en_evaluation`). |
| 1.9 | 🟡 | **Démotion « un seul retenu » non persistée** | Dans RevueCandidats, retenir un candidat rétrograde l'ancien retenu **localement seulement** → peut diverger du backend. |
| 1.10 | ✅ | **Réévaluation câblée** | `POST /candidatures/{id}/reevaluation` **déclenché depuis le front** : `RevueCandidatsView.reevaluer()` → `apiService.reevaluerCandidature(id)`. *(Le registre la disait inutilisée : périmé.)* |

## 2. Recommandation & cartographie (#3) — reco ET cartographie RÉSOLUES (live)

| # | Sév. | Remarque | Détail / recommandation |
|---|------|----------|-------------------------|
| 3.1 | ✅ | **Reco : résolue en live** | Contournement de la latence ~128 s (génération Ollama synchrone) : la session parallèle a ajouté **`GET /api/competences/ma-reco`** (pré-calculé / caché). `getReco` **et** `getManagerReco` sont désormais **LIVE** via `mapReco(RecommendationOut)`. Le vieux `POST /competences/recommandations` synchrone reste réservé à un usage async/on-demand. |
| 3.2 | ✅ | **Reco : entrées gérées côté backend** | `/ma-reco` dérive lui-même `poste_texte` du poste visé/aspiration du profil → le front n'a plus à collecter d'entrée. |
| 3.3 | ✅ | **Carto LIVE sur l'organigramme réel (2026-08-03)** | Le backend `cartographie()` était déjà data-driven (N pôles × M familles) et le front `CartoMatrix` aligné — le vrai défaut était le **seed** (6 clés inventées, ~2 départements peuplés). **`_seed_carto` réécrit** sur `config/departements_metiers.yaml` → **67 profils sur les 33 départements / 6 pôles réels**, compétences taguées par 6 familles. Labels via référentiel (`nom`) + **regroupement par pôle** (`CartoLigne.pole` + intertitres `Heatmap.vue`). Mock front réaligné. **Vérifié : 33 lignes riches.** |
| 3.4 | ✅ | **Bilan live : ~58/58 méthodes `apiService` en live** | `getCarto`/`getCartoPole` désormais **live** (branche `/dashboards/cartographie`). Les 2 « mock-only » apparents (`getReco`/`getManagerReco`) passent par `fetchRecoLive` (async) → live. |

## 3. Trous de données (replis neutres des mappers)

Champs affichés par le front mais **non portés par le backend** → repli `—` / `[]` :

| Endroit | Champs en repli | Note |
|---------|-----------------|------|
| `mapProfil` / `mapTeamMember` | `seniority`, `evalScore`, `lastRh`, `lastEntretien`, `gaps`, `flag`, `aspirationHorizon` | Le modèle `Profil` ne porte ni ancienneté, ni note d'éval, ni date de dernier entretien, ni écarts. |
| `mapFormation` | `status`='recommended', `progress`=0 | Pas de suivi LMS par collaborateur côté backend. |
| `mapOffre` | narratif `mission` dérivé, `managerInformed`/confidentialité **inférés du type** | `description` backend souvent nulle. |
| `mapCollabProfile` | `horizon`=''`, `todos`=[] | Non portés. |

## 4. Dette technique (#5)

| # | Sév. | Remarque | Statut |
|---|------|----------|--------|
| 5.1 | ✅ | **chart.js + vue-chartjs inutilisés** | Aucun import dans `src/` (la « Courbe » est en SVG, la heatmap en grille CSS). **Retirés de `package.json`** → lancer `npm install` pour purger `node_modules`. |
| 5.2 | ✅ | **`tsconfig.node.json` orphelin** | Aucune référence (ni `references`, ni import). **Supprimé.** |
| 5.3 | ✅ | **`lucide-vue-next` déprécié → migré vers `@lucide/vue`** | Confirmé déprécié (npm : « Please use @lucide/vue instead »). Migré : chemin d'import remplacé sur **47 fichiers** (`@lucide/vue` = drop-in, mêmes exports nommés), package déprécié désinstallé. Vérifié : **typecheck exit 0 + build OK**. |
| 5.4 | ✅ | **Tests en place** | **vitest : 54 tests** (mappers 41 + store session 8 + …). Backend **pytest : 149**. Plus « zéro test ». |

## 5. Auth / session / infra

| # | Sév. | Remarque | Détail |
|---|------|----------|--------|
| 6.1 | ✅ | **Durcissement session (#4) — vérifié runtime** | Intercepteur 401 (`http.ts` → `main.ts` : `session.expire()` + redirection `connexion?redirect`), `hydrate()` purge le cache sur 401. **Rejoué au navigateur (live)** : session révoquée serveur → appel API → 401 → redirection `/connexion?redirect=/app/rh/notifications` + store purgé. ✅ |
| 6.2 | ✅ | **CORS `:3001` ajouté (2026-08-03)** | `ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173` (backend/.env). Utile si le front est servi hors proxy Vite. |
| 6.3 | ✅ | **`.env.example` fourni (2026-08-03)** | `frontend/.env.example` documente `VITE_API_MODE` (défaut **live** ; `mock` = fixtures hors-ligne). `frontend/.env.local` (cette machine) réglé sur **`live`** pour la démo backend complète (cartographie 33 départements, reco IA, persistance). |
| 6.4 | 🟡 | **Backend à lancer sur `:5001`** | `uvicorn app.main:app --port 5001` (défaut 8000 sinon). SQLite = un seul writer. |

## 6. Coordination inter-sessions

| # | Sév. | Remarque |
|---|------|----------|
| 7.1 | ✅ | **Reco de la session parallèle intégrée** : `getReco` / `getManagerReco` live via `/competences/ma-reco`, `mapReco` utilisé. **Typecheck revenu au vert.** Vigilance maintenue : `apiService.ts` / `mappers.ts` restent édités des deux côtés. |
| 7.3 | 🟠 | **Mon lot #4/#1/#5 non commité** : `http.ts`, `main.ts`, `session.ts`, 4 vues, `package.json`, suppression `tsconfig.node.json` sont **modifiés dans le working tree, pas commités** (la session parallèle, elle, commite). À commiter pour éviter une perte sur un `git reset` externe. |
| 7.2 | 🟠 | **Données de test dans la base partagée** (tests d'écriture) : candidatures id **8**/**9** (Marc) ; **offres id 7 (mission), 8 (projet), 9 (poste RH)** ; souhait id **2** passé à `pousse`. Peu/pas nettoyables (pas de DELETE candidature — cf. 1.4). À purger via re-seed si besoin d'une démo propre. |
