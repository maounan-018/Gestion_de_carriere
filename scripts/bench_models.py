#!/usr/bin/env python3
"""
Benchmark de modèles Ollama locaux — BMCI Gestion des Carrières.

Mesure, pour chaque modèle, le débit de génération et de prompt (tokens/s) et
le placement GPU/CPU, à num_ctx fixé. Sert à choisir le meilleur modèle par
tâche (voir docs/IA-MODELES-LOCAUX.md). Stdlib uniquement — aucune dépendance.

Leçon clé : TOUJOURS fixer num_ctx. Le défaut Ollama (128K) fait déborder le
cache KV sur le CPU et effondre le débit. 4096-8192 = 100% GPU sur les 8B.

Usage :
  python scripts/bench_models.py                       # pool par défaut @ num_ctx=4096
  python scripts/bench_models.py --ctx 8192 hermes3:8b qwen3:8b
"""
import argparse
import json
import time
import urllib.request

OLLAMA = "http://localhost:11434"
DEFAULT_POOL = ["hermes3:8b", "llama3.1:8b", "qwen3:8b", "mistral-nemo", "gemma3:4b"]
PROMPT = ("Rédige un paragraphe de 8 phrases en français sur la gestion des "
          "carrières et la mobilité interne dans une grande banque.")


def _post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        OLLAMA + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read().decode("utf-8"))


def _placement(model: str) -> str:
    try:
        for m in _post("/api/ps", {}).get("models", []):
            if m.get("name", "").startswith(model.split(":")[0]):
                total = m.get("size", 0) or 1
                vram = m.get("size_vram", 0)
                pct = round(100 * vram / total)
                return f"{pct}% GPU ({round(total/1e9,1)} Go)"
    except Exception:
        pass
    return "?"


def bench(model: str, ctx: int, n_predict: int = 260) -> dict:
    # décharge pour repartir propre, puis mesure
    try:
        _post("/api/generate", {"model": model, "keep_alive": 0, "prompt": ""})
    except Exception:
        pass
    time.sleep(1)
    r = _post("/api/generate", {
        "model": model, "prompt": PROMPT, "stream": False,
        "options": {"num_predict": n_predict, "num_ctx": ctx},
    })
    gen = r["eval_count"] / (r["eval_duration"] / 1e9)
    pe = r["prompt_eval_count"] / (r["prompt_eval_duration"] / 1e9)
    return {"model": model, "ctx": ctx, "gen": round(gen, 1),
            "prompt": round(pe, 1), "place": _placement(model)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctx", type=int, default=4096, help="num_ctx (défaut 4096)")
    ap.add_argument("models", nargs="*", default=DEFAULT_POOL, help="modèles à tester")
    args = ap.parse_args()

    print(f"{'MODELE':<22}{'CTX':>7}{'GEN tok/s':>12}{'PROMPT tok/s':>14}   PLACEMENT")
    print("-" * 78)
    for m in (args.models or DEFAULT_POOL):
        try:
            b = bench(m, args.ctx)
            print(f"{b['model']:<22}{b['ctx']:>7}{b['gen']:>12}{b['prompt']:>14}   {b['place']}")
        except Exception as e:  # noqa: BLE001
            print(f"{m:<22}{args.ctx:>7}   ERREUR: {e}")


if __name__ == "__main__":
    main()
