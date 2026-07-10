# Référentiels de compétences — ESCO · O*NET · SFIA (FR/EN)

> Le référentiel unifié est le **socle** de toute la plateforme : extraction,
> matching, recommandations et succession s'y ancrent. On combine trois sources
> complémentaires, **bilingues FR/EN**, fusionnées en un **graphe de compétences unique**.

---

## 1. Les trois sources

### 🇪🇺 ESCO — colonne vertébrale
Classification européenne **multilingue** des compétences, occupations et qualifications.

| | |
|---|---|
| Couverture | **3 039 occupations**, **13 939 compétences** liées |
| Langues | **28** (toutes langues UE dont **FR + EN**, + IS/NO/UK/AR) |
| Version | **v1.2.1** (pilier compétences en hiérarchie à 4 sous-classifications) |
| Formats | **CSV, JSON-LD, RDF, TTL, XML, ODS** |
| Accès | téléchargement complet **+ API** (Web Services **et** API locale téléchargeable) |
| Licence | **EUPL 1.2** (composants Apache 2.0) — **libre, gratuit** ✅ |

➡️ **Backbone multilingue** : c'est ESCO qui donne les libellés FR **et** EN
« gratuitement » (même URI, traductions officielles), plus les relations
compétence↔occupation.

### 🇺🇸 O*NET — richesse métier (US)
Base du Département du Travail américain : taxonomie occupations + compétences,
aptitudes, activités de travail, contexte.

| | |
|---|---|
| Contenu | O*NET-SOC (occupations) + Content Model (skills, abilities, work activities…) |
| Formats | **Excel** + **CTDL JSON-LD** (machine-readable) |
| Langue | **anglais uniquement** → **traduction FR via `lc-redacteur`** (local) |
| Licence | **Creative Commons** — usage commercial **encouragé** ✅ |
| MàJ | trimestrielle (891 occupations mises à jour en 2026) |

➡️ Apporte la **granularité comportementale** (aptitudes, activités) qu'ESCO a moins.
À traduire en FR localement (pas de FR officiel).

### 🧩 SFIA 9 — compétences IT/digital + niveaux de responsabilité
Cadre mondial des compétences du numérique, structuré en **niveaux de responsabilité (1–7)**.

| | |
|---|---|
| Contenu | ~147 compétences digitales × 7 niveaux de responsabilité |
| Langues | **11–12** dont **le français** ✅ |
| Formats | PDF, **Excel, JSON, RDF** (après inscription gratuite) |
| Licence | **gratuit** individus/PME · **payant** grande entreprise & usage commercial ⚠️ |

➡️ Indispensable pour les **filières IT/digital de la banque** et surtout pour la
notion de **séniorité/niveau** (que ni ESCO ni O*NET ne structurent aussi bien).
**⚠️ Point budget** : BMCI = grande entreprise → **licence commerciale SFIA à
prévoir** pour la production (le dev/évaluation reste possible gratuitement).

---

## 2. Stratégie bilingue FR/EN

- **FR + EN natifs** via ESCO (traductions officielles, même identifiant) et SFIA (FR officiel).
- **O*NET** : libellés EN → **traduction FR générée localement** (`lc-redacteur`),
  puis **validée** en rapprochant l'embedding FR de la compétence ESCO la plus proche
  (contrôle de cohérence, pas de traduction « hors-sol »).
- Chaque compétence du graphe porte **`label_fr` + `label_en` + définitions** dans les deux langues.

---

## 3. Le graphe de compétences unifié (crosswalk)

Les trois référentiels ne parlent pas le même langage → on construit une **table de
correspondance (crosswalk)** vers un **identifiant interne unique** par compétence.

```
Compétence interne (uuid)
├── label_fr / label_en / def_fr / def_en
├── esco_uri        (si trouvée)      ← source de vérité multilingue
├── onet_element_id (si trouvée)      ← aptitudes / activités
├── sfia_code + niveau (1–7)          ← séniorité digitale
├── embedding (bge-m3)                ← pour matching sémantique
└── relations: {broader, narrower, related, requiert, mène_à}
```

**Méthode d'alignement** (semi-automatique, local) :
1. Charger ESCO (pivot) → un nœud par compétence, FR+EN.
2. Embedder tous les libellés (`bge-m3`).
3. Pour O*NET/SFIA : embedder chaque élément → chercher le nœud ESCO le plus proche
   → **reranker** (`bge-reranker-v2-m3`) → **valider par LLM** (`lc-normaliseur` :
   « ces deux libellés désignent-ils la même compétence ? oui/non + justification »).
4. Seuil de confiance : au-dessus → fusion ; en dessous → nouveau nœud + à revoir (RH).

➡️ On obtient un **référentiel vivant**, bilingue, qui relie compétences ↔ rôles ↔
niveaux — l'équivalent local du knowledge graph de Gloat / des embeddings d'Eightfold.

---

## 4. Plan d'ingestion (`ia/referentiels/` + `scripts/`)

| Étape | Script | Sortie |
|---|---|---|
| 1. Télécharger ESCO (CSV/RDF v1.2.1) | `scripts/fetch_esco.py` | `ia/referentiels/esco/` |
| 2. Télécharger O*NET (Excel/JSON-LD) | `scripts/fetch_onet.py` | `ia/referentiels/onet/` |
| 3. Importer SFIA (Excel/JSON, après licence) | `scripts/fetch_sfia.py` | `ia/referentiels/sfia/` |
| 4. Normaliser + embedder | `scripts/build_skill_graph.py` | table `skills` + vecteurs |
| 5. Crosswalk (align + rerank + LLM) | `scripts/crosswalk.py` | table `skill_mappings` |
| 6. Traduire O*NET FR | `scripts/translate_onet_fr.py` | libellés FR validés |

Tout tourne **en local** (aucun appel externe passé le téléchargement initial des
référentiels, qui sont des données publiques et non des données banque).

---

## 5. Licences — récapitulatif

| Référentiel | Licence | Coût prod BMCI | Action |
|---|---|---|---|
| **ESCO** | EUPL 1.2 / Apache 2.0 | **gratuit** | télécharger |
| **O*NET** | Creative Commons | **gratuit** (commercial OK) | télécharger + traduire FR |
| **SFIA 9** | libre PME / **payant grande entreprise** | **licence à budgéter** ⚠️ | inscription gratuite (dev) → licence commerciale (prod) |

---

## Sources

- [ESCO — Download](https://esco.ec.europa.eu/en/use-esco/download) · [ESCO API](https://esco.ec.europa.eu/en/use-esco/use-esco-services-api) · [ESCO v1.2.1](https://esco.ec.europa.eu/en/news/esco-v121-live)
- [O*NET Database & licence](https://www.onetcenter.org/database.html) · [O*NET-SOC Taxonomy](https://www.onetcenter.org/taxonomy.html)
- [SFIA 9](https://sfia-online.org/en/sfia-9) · [SFIA 9 — documents & langues](https://sfia-online.org/en/sfia-9/documentation)
- [Job Matching with ESCO & EQF — arXiv 2512.03195](https://arxiv.org/pdf/2512.03195)
