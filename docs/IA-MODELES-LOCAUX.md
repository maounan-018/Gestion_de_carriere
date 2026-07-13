# Modèles IA locaux — une panoplie, le meilleur par tâche

> Principe (validé avec toi) : **ne pas se limiter à Qwen**. On télécharge une
> **panoplie** de modèles open source via Ollama (Qwen3, Mistral, Hermes, Llama,
> Gemma, Granite, BGE…), on les **benchmarke sur nos propres données FR/EN**, et
> un **fichier de routage** (`ia/routing.yaml`) affecte à chaque tâche **le modèle
> gagnant**. Changer d'avis = **une ligne à éditer**, pas de refonte.
> Recherche menée en juillet 2026 ; « le meilleur » se décide sur *nos* données.

---

## Pourquoi une panoplie (et pas un seul modèle)

Chaque famille a une force différente :

| Famille | Force distinctive | Idéal pour |
|---|---|---|
| **Qwen3** (8B) | **champion du tool-calling** sur 8 Go VRAM, JSON fiable, 100+ langues | extraction, agents |
| **Mistral / Ministral** (8B) | **meilleur en français** (équipe FR, corpus francophone dense) | conseil, rédaction FR |
| **Hermes 3** (Nous, 8B) | taillé pour **sortie structurée + function calling** + très « steerable » | extraction stricte, agents |
| **Llama 3.1/3.3** | polyvalent, écosystème d'outils le plus large | secours généraliste |
| **Gemma 3** | **meilleur ratio perf/taille**, bon en FR | tâches légères, edge |
| **Granite 3** (IBM) | orienté **entreprise/RAG**, licence permissive | RAG, données métier |
| **BGE-M3** | embeddings **multilingues hybrides** (dense+sparse) | matching sémantique |

➡️ On exploite ces forces **par tâche**, au lieu d'imposer un généraliste partout.

---

## Vue d'ensemble : pool de candidats par tâche

Pour chaque tâche, un **pool** à benchmarker + un **champion pressenti** (à confirmer).

| # | Tâche | Pool de candidats (Ollama) | Champion pressenti |
|---|---|---|---|
| 1 | Embeddings (matching) | `bge-m3` ✅ · `qwen3-embedding` · `granite-embedding` · `mxbai-embed-large` | **bge-m3** |
| 2 | Reranking (top-k) | `bge-reranker-v2-m3` · `qwen3-reranker` · `jina-reranker-v2` | **bge-reranker-v2-m3** |
| 3 | Extraction compétences (JSON) | `hermes3:8b` · `qwen3:8b` · `granite3-dense` · `mistral` | **hermes3** ou **qwen3** |
| 4 | Normalisation sémantique | `qwen3:8b` · `mistral` · `gemma3` | **qwen3** |
| 5 | Recommandation / conseil (FR) | `mistral` · `qwen3:8b` · `gemma3` · `llama3.1:8b` | **mistral** (FR) |
| 6 | Rédaction / résumé FR-EN | `mistral` · `qwen3:8b` | **mistral** |
| 7 | Raisonnement lourd (batch) | `qwen3.6` ✅ · `deepseek-r1:32b` · `llama3.3:70b` (CPU) | **qwen3.6** |
| 8 | Agent multi-étapes (outils) | `qwen3:8b` · `hermes3:8b` · `granite3-dense` | **qwen3** |

> **Astuce VRAM** : les LLM de tâche (#3–#6, #8) sont tous des **8B** ⇒ un seul chaud
> à la fois sur le GPU (Ollama décharge/recharge). Les spécialisations se font par
> **Modelfile** (system prompt + `temperature 0` + `/no_think`), ta pratique `smart-qwen8`.

---

## La panoplie à télécharger (`scripts/pull_models.sh`)

```bash
# Embeddings & reranking (multilingues)
ollama pull bge-m3                 # ✅ déjà là
ollama pull qwen3-embedding        # option qualité FR
ollama pull granite-embedding      # alternative entreprise
ollama pull mxbai-embed-large      # alternative

# LLM de tâche (8B — tiennent sur 8 Go VRAM)
ollama pull qwen3:8b               # ✅ déjà là — tool-calling, JSON
ollama pull mistral                # français ++
ollama pull hermes3:8b             # sortie structurée / agents
ollama pull llama3.1:8b            # secours polyvalent
ollama pull gemma3                 # perf/taille
ollama pull granite3-dense:8b      # RAG / entreprise

# Raisonnement lourd (batch, CPU/RAM)
ollama pull qwen3.6                # ✅ déjà là (23 Go)
# ollama pull deepseek-r1:32b      # option raisonnement
```

Le reranker se sert **hors Ollama** (Ollama ne rerank pas bien) via **FlagEmbedding**
ou **Text-Embeddings-Inference** :

```python
from FlagEmbedding import FlagReranker
reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)
```

---

## Méthode : benchmark par tâche → on garde le gagnant

C'est **ça** qui répond à « utiliser ceux qui seraient les mieux pour chaque tâche ».
On ne devine pas : on **mesure** sur nos données.

1. **Jeu d'évaluation** (`ia/pipelines/evals/`) : ~30–50 exemples FR/EN **réels** par tâche
   (descriptifs de poste → compétences attendues ; profil+offre → bon match ; etc.).
2. **Métriques** par tâche : validité JSON (%), **F1 / exactitude** vs référence,
   **latence** (tok/s), respect du bilingue.
3. **Runner** (`scripts/bench_models.py`) : lance chaque candidat du pool, agrège un tableau.
4. **Décision** : le gagnant par tâche est inscrit dans `ia/routing.yaml`.
5. **Réversible** : un nouveau modèle sort ? on le `pull`, on l'ajoute au pool, on relance le bench.

---

## Le routage (`ia/routing.yaml`)

Le backend (`services/ai_router`) lit ce fichier ; changer un modèle = **une ligne**.

```yaml
# Chaque tâche → modèle gagnant + repli. Édite ici après un benchmark.
embeddings:
  model: bge-m3
  alt: qwen3-embedding
reranker:
  model: bge-reranker-v2-m3
  engine: flagembedding          # hors Ollama
taches:
  extraction_competences:
    model: hermes3:8b            # ou qwen3:8b selon bench
    fallback: qwen3:8b
    temperature: 0
    format: json
  normalisation:
    model: qwen3:8b
    temperature: 0
  conseil:
    model: mistral               # français
    temperature: 0.3
  redaction:
    model: mistral
    temperature: 0.4
  agent:
    model: qwen3:8b              # meilleur tool-calling 8 Go
    temperature: 0
  raisonnement_batch:
    model: qwen3.6               # CPU/RAM, hors-ligne
    temperature: 0.2
```

---

## Modelfiles spécialisés (`ia/modelfiles/`)

Un Modelfile par tâche structurée, quel que soit le modèle de base retenu :

```Dockerfile
FROM hermes3:8b            # ou qwen3:8b — la base gagnante du bench
SYSTEM """/no_think
Tu es un extracteur de compétences bilingue (FR/EN).
Retourne UNIQUEMENT un JSON valide { taches[], competences[...], seniorite }.
"""
PARAMETER temperature 0
PARAMETER num_ctx 8192
```

```bash
ollama create lc-extracteur -f ia/modelfiles/lc-extracteur.Modelfile
```

---

## Benchmarks réels — ta machine (RTX 5060 8 Go, 2026-07-13)

> ⚠️ **La découverte la plus importante du projet : fixer `num_ctx`.**
> Ollama charge par défaut le contexte **maximal du modèle (131072 = 128K)**. Le
> cache KV correspondant est énorme → il ne rentre pas dans 8 Go → le modèle
> **déborde sur le CPU** (jusqu'à 74 % des couches) → tout rame. En **fixant
> `num_ctx=4096`**, les modèles 8B tiennent **100 % sur le GPU** → ×4 de débit.

| Modèle | num_ctx défaut (128K) | **num_ctx=4096** | Placement @4096 |
|---|---|---|---|
| `hermes3:8b` | — | **61,6 tok/s** · prompt 598 | **100 % GPU** (5,0 Go) |
| `llama3.1:8b` | 13,2 tok/s | **52,9 tok/s** · prompt 478 | **100 % GPU** (5,3 Go) |
| `mistral-nemo` (12B) | 8,1 tok/s | **21 tok/s** · prompt 233 | 78 % GPU / 22 % CPU (7,9 Go) |

**Enseignements :**
- **Toujours fixer `num_ctx`** (4096–8192 selon la tâche) — c'est câblé dans `ia/routing.yaml`.
- **Real-time = modèles 8B** (hermes3, llama3.1, qwen3) : 100 % GPU, 50-60 tok/s. Parfait.
- **`mistral-nemo` (12B)** : meilleur FR mais déborde un peu (21 tok/s) → à réserver
  au **conseil/rédaction** où la qualité prime sur la vitesse ; sinon fallback 8B.
- Mesures faites en mode **équilibré (plafond 60 W)** → **encore plus rapide en Extreme (115 W)**.

## Adéquation VRAM (RTX 5060 Laptop, 8 Go)

- **1 LLM 8B chaud** sur GPU (~5–6 Go) à la fois ; Ollama swap à la demande.
- **Fixer `num_ctx`** (voir ci-dessus) — sinon le 128K par défaut force le CPU.
- **Embeddings + reranker sur CPU** (Ryzen 9 = rapide) → VRAM réservée au LLM.
- **Batch lourd** (`qwen3.6`, `deepseek-r1:32b`) → **CPU + 32 Go RAM**, hors-ligne.
- On ne charge **jamais** LLM + embeddings + reranker simultanément sur le GPU.

---

## Sources (recherche juillet 2026)

- [Best Local Models for Tool Calling 2026 — PromptQuorum](https://www.promptquorum.com/power-local-llm/best-local-models-tool-calling-2026)
- [I Tested 13 Local LLMs on Tool Calling (2026) — JD Hodges](https://www.jdhodges.com/blog/local-llms-on-tool-calling-2026-pt1-local-lm/)
- [Meilleur LLM local pour le français 2026 — QuelLLM.fr](https://quelllm.fr/meilleur-llm/francais)
- [Comparatif LLM open source 2026 (FR) — Ayi Nedjimi](https://ayinedjimi-consultants.fr/articles/ia-comparatif-llm-open-source-2026)
- [Meilleurs modèles Ollama 2026 par usage — Shubham Sharma](https://shubham-sharma.fr/articles/meilleurs-modeles-ollama-2026/)
- [Best Open-Source Embedding Models 2026 — BentoML](https://www.bentoml.com/blog/a-guide-to-open-source-embedding-models)
- [BAAI/bge-reranker-v2-m3 — Hugging Face](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- [Skill-LLM: Repurposing LLMs for Skill Extraction — arXiv 2410.12052](https://arxiv.org/abs/2410.12052)
