#!/usr/bin/env bash
# Télécharge la panoplie de modèles IA locaux (Ollama) — BMCI Gestion des Carrières
set -e

echo "== Embeddings & reranking (multilingues FR/EN) =="
ollama pull bge-m3                 # ✅ souvent déjà présent
ollama pull qwen3-embedding        # option qualité FR
ollama pull granite-embedding      # alternative entreprise
ollama pull mxbai-embed-large      # alternative

echo "== LLM de tâche (8B — tiennent sur 8 Go VRAM) =="
ollama pull qwen3:8b               # tool-calling, JSON
ollama pull mistral                # français ++
ollama pull hermes3:8b             # sortie structurée / agents
ollama pull llama3.1:8b            # secours polyvalent
ollama pull gemma3                 # perf/taille
ollama pull granite3-dense:8b      # RAG / entreprise

echo "== Raisonnement lourd (batch, CPU/RAM) =="
ollama pull qwen3.6                # 23 Go — hors-ligne
# ollama pull deepseek-r1:32b      # option raisonnement (décommenter si besoin)

echo "== Reranker (hors Ollama) =="
echo "  pip install FlagEmbedding   # BAAI/bge-reranker-v2-m3"

echo "OK — panoplie téléchargée. Lance ensuite: python scripts/bench_models.py"
