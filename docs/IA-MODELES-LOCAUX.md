# Modèles IA locaux — un modèle par tâche

> Principe : **plusieurs petits modèles spécialisés** valent mieux qu'un seul gros
> générique. Chaque tâche reçoit le modèle le mieux adapté (qualité/latence/VRAM),
> tous **open source** et **exécutés localement** via Ollama ou un service Python.
> Recherche menée en juillet 2026 ; à revalider sur nos propres données.

---

## Vue d'ensemble

| # | Tâche | Modèle retenu | Taille | Support | Exécution |
|---|---|---|---|---|---|
| 1 | Embeddings (matching sémantique) | **BGE-M3** ✅ déjà installé | 1,2 Go | 100+ langues, hybride | Ollama ou CPU |
| 1b | Embeddings (option qualité) | **Qwen3-Embedding-0.6B/4B** | 0,6–4 Go | excellent FR | CPU/GPU |
| 2 | Reranking (précision top-k) | **bge-reranker-v2-m3** | ~0,6 Go | multilingue | service Python |
| 3 | Extraction de compétences | **Qwen3-8B** → `lc-extracteur` | 5,2 Go | FR/EN | Ollama/GPU |
| 4 | Normalisation sémantique | **Qwen3-8B** → `lc-normaliseur` | (partagé) | FR/EN | Ollama/GPU |
| 5 | Recommandation / conseil | **Qwen3-8B** → `lc-conseiller` | (partagé) | FR/EN | Ollama/GPU |
| 6 | Rédaction / résumé FR-EN | **Qwen3-8B** → `lc-redacteur` | (partagé) | FR/EN | Ollama/GPU |
| 7 | Raisonnement lourd (batch) | **qwen3.6** ✅ déjà installé | 23 Go | FR/EN | CPU+RAM |
| 8 | Agent multi-étapes | **Qwen3-8B** (function calling) | (partagé) | outils | Ollama/GPU |

> Les modèles #3–#6 et #8 partagent **le même poids de base** (`qwen3:8b`) : on ne
> multiplie pas la VRAM, on multiplie les **Modelfiles** (system prompt + params
> spécialisés). C'est exactement ta pratique `smart-qwen8`.

---

## 1. Embeddings — BGE-M3 (déjà présent)

Le cheval de bataille du RAG multilingue self-hosted en 2026 : dense **+** sparse
**+** multi-vecteur, 100+ langues, excellent FR/EN. Sert au **matching** (profil↔offre,
compétence↔compétence) et à l'ancrage des extractions dans le référentiel.

```bash
ollama list          # bge-m3:latest déjà là
# usage embeddings via Ollama:  POST :11434/api/embeddings  {"model":"bge-m3","prompt":"..."}
```

**Option qualité** : `Qwen3-Embedding` (sorti début 2026, en tête du MTEB v2
open-weight, FR ≈ 69,8). À benchmarker contre BGE-M3 sur nos offres/compétences
avant de trancher.

## 2. Reranking — bge-reranker-v2-m3

Cross-encoder qui **reclasse** les meilleurs candidats d'une recherche vectorielle
(query, compétence) → gros gain de précision. Défaut 2026 (léger, multilingue,
licence saine). Ollama ne rerank pas correctement → on l'expose via un petit
service Python (**FlagEmbedding** ou **Text-Embeddings-Inference**).

```python
# backend: pip install FlagEmbedding
from FlagEmbedding import FlagReranker
reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)
scores = reranker.compute_score([[query, cand] for cand in candidats])
```

## 3–6. Modèles LLM spécialisés (Modelfiles sur Qwen3-8B)

Même base `qwen3:8b`, un **Modelfile par tâche** (`ia/modelfiles/`) : system prompt
strict, sortie **JSON valide uniquement**, `temperature 0`, `/no_think` (rapidité).

- **`lc-extracteur`** — entrée : descriptif de poste / mission ; sortie : `{taches[], competences[{label_fr,label_en,esco_uri?,niveau_sfia?}], seniorite}`.
- **`lc-normaliseur`** — canonicalise intitulés & compétences (synonymes, casse, langue), rapproche des libellés officiels.
- **`lc-conseiller`** — entrée : profil + graphe (RAG) ; sortie : recommandations (mobilités, mentors, **formations**) justifiées.
- **`lc-redacteur`** — reformulations bilingues, résumés d'entretien, descriptifs d'offre.

```bash
# exemple de build (à écrire dans ia/modelfiles/lc-extracteur.Modelfile)
ollama create lc-extracteur -f ia/modelfiles/lc-extracteur.Modelfile
```

Gabarit (repris de ton `smart-qwen8`) :

```Dockerfile
FROM qwen3:8b
SYSTEM """/no_think
Tu es un extracteur de compétences bilingue (FR/EN).
Retourne UNIQUEMENT un JSON valide { ... }.  # schéma strict par tâche
"""
PARAMETER temperature 0
PARAMETER num_ctx 8192
```

## 7. Raisonnement lourd — qwen3.6 (déjà présent, 23 Go)

Pour les tâches **hors-ligne** à fort raisonnement (planification des talents,
scénarios de succession, synthèses RH). Tourne sur **CPU + RAM** (pas assez de
VRAM) → on l'appelle en **batch** (jobs asynchrones), pas dans le flux temps réel.

## 8. Agent multi-étapes

Qwen3-8B en **function calling** : un orchestrateur maison expose des « outils »
(rechercher_competences, matcher_profil, lister_formations, interroger_graphe…)
et laisse le modèle enchaîner les étapes pour une tâche composée
(« proposer un plan de mobilité pour Aya »). Local, traçable, borné.

---

## Adéquation VRAM (RTX 5060 Laptop, 8 Go)

- 1 LLM 8B chaud sur GPU (~5,2 Go) **OU** embeddings+reranker sur CPU : **jamais tout sur GPU en même temps**.
- Embeddings/reranker sur **CPU** (Ryzen 9 = rapide) → VRAM réservée au LLM.
- `qwen3.6` (23 Go) → **CPU + 32 Go RAM**, batch uniquement.
- Ollama décharge/recharge à la demande : coût maîtrisé.

---

## Sources (recherche juillet 2026)

- [Best Open-Source Embedding Models 2026 — BentoML](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models)
- [Embedding Models 2026 (FR) — Ailog](https://app.ailog.fr/en/blog/news/embedding-models-2026)
- [Choose an embedding model for RAG 2026 — Milvus](https://milvus.io/blog/choose-embedding-model-rag-2026.md)
- [Reranking & Cross-Encoders 2026 — Local AI Master](https://localaimaster.com/blog/reranking-cross-encoders-guide)
- [Top 5 Reranking Models — MachineLearningMastery](https://machinelearningmastery.com/top-5-reranking-models-to-improve-rag-results/)
- [BAAI/bge-reranker-v2-m3 — Hugging Face](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- [Skill-LLM: Repurposing LLMs for Skill Extraction — arXiv 2410.12052](https://arxiv.org/abs/2410.12052)
- [Enhancing Job Matching with ESCO & EQF — arXiv 2512.03195](https://arxiv.org/pdf/2512.03195)
