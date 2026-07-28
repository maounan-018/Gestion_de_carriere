# Câblage frontend ↔ backend — registre des remarques & blocages

> Journal vivant de tout ce qui bloque, manque, ou a été contourné pendant le
> branchement du frontend Vue sur l'API FastAPI. Tenu à jour au fil des chantiers.
> Sévérité : 🔴 bloquant · 🟠 à traiter · 🟡 dette/finition · ✅ fait.
>
> Dernière mise à jour : 2026-07-27.

---

## 1. Écritures / persistance (#1)

| # | Sév. | Remarque | Détail / recommandation |
|---|------|----------|-------------------------|
| 1.1 | ✅ | **Postuler** persiste | `POST /api/candidatures` câblé (OffreDetailView collab). 201 vérifié + garde doublon 400. |
| 1.2 | ✅ | **Notifications lues** persistent | `PATCH /notifications/{id}/lu` + `POST /notifications/lues` (3 vues). 200 vérifié. |
| 1.3 | ✅ | **Décision candidat** persiste | `PATCH /candidatures/{id}/decision` (RevueCandidats RH). 200 sur les 3 statuts. |
| 1.4 | 🔴 | **Pas d'endpoint DELETE candidature** | Impossible de nettoyer une candidature ni de la retirer côté collaborateur. Le statut `retiree` existe dans le schéma mais **aucune route ne le pose**. → besoin d'un `DELETE /candidatures/{id}` ou `PATCH …/retrait`. |
| 1.5 | 🟠 | **Pas de champ d'édition de profil** | `PATCH /api/profils/{id}` existe mais **aucun formulaire front** ne l'utilise ; « Éditer mon profil » reste un toast « à venir ». → construire l'écran d'édition (poste visé, aspirations, compétences). |
| 1.6 | 🟠 | **Type `Souhait` (front) sans `id`** | Bloque « pousser / éditer » un souhait existant via `PATCH /souhaits/{id}`. Le POST (créer + pousser) est possible, l'update non. → ajouter `id` au type `Souhait` + le porter dans `mapSouhait`. |
| 1.7 | 🟠 | **Publier une offre non câblé** | `POST /api/offres` existe ; côté manager/RH « Publier une offre » est un toast. → câbler la modale de publication. |
| 1.8 | 🟡 | **Statuts candidature : front plus riche que back** | Le front distingue `entretien`/`preselection` ; le backend n'accepte que `en_evaluation`/`retenue`/`rejetee`. « Convoquer » et « Présélectionner » persistent tous deux en `en_evaluation` (perte de granularité). |
| 1.9 | 🟡 | **Démotion « un seul retenu » non persistée** | Dans RevueCandidats, retenir un candidat rétrograde l'ancien retenu **localement seulement** → peut diverger du backend. |
| 1.10 | 🟡 | **Réévaluation inutilisée** | `POST /candidatures/{id}/reevaluation` existe mais aucun déclencheur front. |

## 2. Recommandation & cartographie (#3) — reco RÉSOLUE (live), cartographie encore bloquée

| # | Sév. | Remarque | Détail / recommandation |
|---|------|----------|-------------------------|
| 3.1 | ✅ | **Reco : résolue en live** | Contournement de la latence ~128 s (génération Ollama synchrone) : la session parallèle a ajouté **`GET /api/competences/ma-reco`** (pré-calculé / caché). `getReco` **et** `getManagerReco` sont désormais **LIVE** via `mapReco(RecommendationOut)`. Le vieux `POST /competences/recommandations` synchrone reste réservé à un usage async/on-demand. |
| 3.2 | ✅ | **Reco : entrées gérées côté backend** | `/ma-reco` dérive lui-même `poste_texte` du poste visé/aspiration du profil → le front n'a plus à collecter d'entrée. |
| 3.3 | 🟠 | **Carto : forme incompatible (SEUL mock restant)** | `GET /api/dashboards/cartographie` renvoie **département × top-compétences** (`effectif`, `niveau_moyen`, `top_competences[]`), alors que le front attend une **matrice 9 pôles × 6 familles fixes** (`levels[6]`, `people[]`, `analyse{criticité,focus}`). Aucune correspondance → wiring = **fabriquer** la matrice (contraire au principe « ne pas fabriquer de données »). → soit un endpoint carto aligné sur les 6 familles, soit redessiner la Heatmap sur les données réelles. |
| 3.4 | 🟠 | **Bilan live : 32/34 méthodes `apiService` en live** | Reco (`/ma-reco`) et **vacances** (`/offres/vacances`, matching inverse) désormais **live** ; il ne reste plus que `getCarto` / `getCartoPole` en **mock** (cf. 3.3). |

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
| 5.3 | 🟡 | **`lucide-vue-next` ^1.0.0 signalé déprécié** | Migration = toucher `AppIcon` + ~tous les imports d'icônes (~50 fichiers) → risqué. **Différé** ; vérifier d'abord le successeur réel (`@lucide/vue` ?) avant migration de masse. |
| 5.4 | 🟡 | **Zéro test** | Aucun harnais (pas de vitest). **Différé** ; démarrage le moins coûteux = tests unitaires des fonctions pures des mappers (`relativeTime`, `initialsOf`, `mapOffre`, `mapCandidature`). |

## 5. Auth / session / infra

| # | Sév. | Remarque | Détail |
|---|------|----------|--------|
| 6.1 | ✅ | **Durcissement session (#4)** | Intercepteur 401 (`http.ts` → `main.ts` : `session.expire()` + redirection `connexion?redirect`), `hydrate()` purge le cache sur 401. *Réserve : scénario 401→redirection pas encore rejoué au navigateur.* |
| 6.2 | 🟡 | **CORS `ALLOWED_ORIGINS` sans `:3001`** | Sans effet **tant qu'on passe par le proxy Vite** `/api→:5001` (same-origin). À corriger seulement si le front est servi hors proxy. |
| 6.3 | 🟠 | **Pas de `.env` → mode `live` par défaut** | Sans backend lancé, tous les appels live échouent. (Chantier #2 mis de côté par l'utilisateur.) → fournir `.env.example` + trancher le défaut, ou `VITE_API_MODE=mock`. |
| 6.4 | 🟡 | **Backend à lancer sur `:5001`** | `uvicorn app.main:app --port 5001` (défaut 8000 sinon). SQLite = un seul writer. |

## 6. Coordination inter-sessions

| # | Sév. | Remarque |
|---|------|----------|
| 7.1 | ✅ | **Reco de la session parallèle intégrée** : `getReco` / `getManagerReco` live via `/competences/ma-reco`, `mapReco` utilisé. **Typecheck revenu au vert.** Vigilance maintenue : `apiService.ts` / `mappers.ts` restent édités des deux côtés. |
| 7.3 | 🟠 | **Mon lot #4/#1/#5 non commité** : `http.ts`, `main.ts`, `session.ts`, 4 vues, `package.json`, suppression `tsconfig.node.json` sont **modifiés dans le working tree, pas commités** (la session parallèle, elle, commite). À commiter pour éviter une perte sur un `git reset` externe. |
| 7.2 | 🟠 | **Données de test dans la base partagée** : candidatures id **8** (offre 4) & **9** (offre 2) pour Marc (profil_id 3) créées lors des tests d'écriture ; cand. 8 laissée `rejetee`. Non nettoyables (pas de DELETE — cf. 1.4). |
