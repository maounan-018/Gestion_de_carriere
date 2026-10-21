#!/usr/bin/env python3
"""
services/ai_router.py — Routeur IA : le bon modèle local pour chaque tâche.

RÔLE
    Point d'entrée UNIQUE pour toute génération LLM de la plateforme. À partir du
    nom d'une TÂCHE (ex. "extraction_competences", "conseil"), lit `ia/routing.yaml`
    pour choisir le modèle Ollama, le num_ctx, la température et le format, puis
    appelle Ollama en local. Gère : JSON tolérant, réessais, repli (fallback) sur
    un second modèle, et fençage anti-injection des données non fiables.

    Changer le modèle d'une fonctionnalité = éditer routing.yaml (1 ligne),
    jamais ce fichier. Chaque fonctionnalité obtient ainsi le meilleur modèle,
    avec une SORTIE STRUCTURÉE (JSON) réexploitable par les autres briques.

SÉCURITÉ
    100 % local (Ollama :11434, jamais exposé). Les données passées au modèle
    sont fencées (<donnee>…</donnee>) et déclarées non-instructions.
    ⚠️ Leçon de perf : num_ctx est TOUJOURS borné (défaut 4096) — le contexte
    128K par défaut d'Ollama fait déborder le modèle sur le CPU.

EMPLACEMENT MVC
    Couche "services" : logique IA, sans route HTTP.
"""

import json
import logging
import re
import threading

import requests
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

# 8 Go de VRAM : un seul gros LLM tient à la fois. Ce sémaphore SÉRIALISE les
# générations (les endpoints sync tournent dans un threadpool) → pas de bataille
# pour la VRAM (= débordement CPU). Embeddings/reranker (CPU) ne passent PAS ici.
_GPU_LOCK = threading.Semaphore(1)


# ============================ JSON tolérant ============================


def extract_json_from_text(text: str) -> dict:
    """Extrait un objet JSON d'une réponse potentiellement bruitée (fences markdown,
    texte autour). Reprend la logique éprouvée de smart-objective."""
    text = (text or "").strip()

    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            text = text[start:end].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    first, last = text.find("{"), text.rfind("}")
    if first != -1 and last > first:
        try:
            return json.loads(text[first : last + 1])
        except json.JSONDecodeError:
            pass

    cleaned = text.replace("\n", " ").replace("\r", "")
    first, last = cleaned.find("{"), cleaned.rfind("}")
    if first != -1 and last > first:
        return json.loads(cleaned[first : last + 1])

    raise json.JSONDecodeError("Aucun JSON valide trouvé", text, 0)


def fence(data: str, tag: str = "donnee") -> str:
    """Encadre une donnée non fiable (descriptif de poste, CV, saisie utilisateur)
    dans une balise, en neutralisant toute balise de même nom présente dedans.
    À utiliser dans les prompts : le système déclarera ce bloc comme DONNÉE, jamais
    comme instruction (défense contre l'injection indirecte)."""
    safe = re.sub(rf"</?\s*{tag}\s*>", f"[{tag}]", data or "", flags=re.IGNORECASE)
    return f"<{tag}>\n{safe}\n</{tag}>"


# ============================ Appel Ollama ============================


def _post_generate(
    model: str,
    prompt: str,
    system: str,
    num_ctx: int,
    temperature: float,
    as_json: bool,
    think: bool | None = None,
) -> str:
    """Un appel HTTP à /api/generate ; renvoie le texte brut de 'response'.
    Les erreurs d'infrastructure (Ollama éteint/timeout) lèvent une HTTPException
    et ne sont pas réessayées (inutile).

    `think` : pour un modèle à raisonnement (qwen3…), `False` coupe le mode
    « thinking » de façon FIABLE (paramètre Ollama), là où le hack texte `/no_think`
    n'est pas garanti. `None` = ne rien imposer (défaut du modèle)."""
    payload = {
        "model": model,
        "system": system or "",
        "prompt": f"/no_think\n{prompt}",
        "stream": False,
        "keep_alive": settings.OLLAMA_KEEP_ALIVE,  # garde le modèle en VRAM (anti cold-start)
        "options": {
            "temperature": temperature,
            "num_ctx": num_ctx,  # borné : évite le débordement CPU (128K par défaut)
            "seed": settings.AI_SEED,
        },
    }
    if think is not None:
        payload["think"] = think  # interrupteur fiable du raisonnement (qwen3…)
    if as_json:
        payload["format"] = "json"
    try:
        with _GPU_LOCK:  # une génération LLM à la fois (VRAM 8 Go)
            r = requests.post(settings.OLLAMA_GENERATE_URL, json=payload, timeout=300)
        r.raise_for_status()
        return r.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, detail="Ollama n'est pas démarré (lancez 'ollama serve')."
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Le modèle met trop de temps à répondre.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur Ollama (%s): %s", model, e)
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'appel au modèle.")


def generate(task: str, prompt: str, system: str = "", is_valid=None):
    """Génère une réponse pour une TÂCHE donnée (routée via routing.yaml).

    - task     : clé de routing.yaml (ex. "extraction_competences", "conseil").
    - is_valid : callback(dict|str) -> bool pour juger une réponse exploitable ;
                 sinon on réessaie (jusqu'à AI_MAX_ATTEMPTS) puis on bascule sur le
                 modèle `fallback` défini dans routing.yaml.

    Renvoie un `dict` si la tâche est en format JSON, sinon le texte brut.
    """
    cfg = settings.task_model(task)
    as_json = cfg.get("format") == "json"
    num_ctx = int(cfg.get("num_ctx", 4096))
    temperature = float(cfg.get("temperature", 0))
    think = cfg.get("think")  # None si absent ; False pour couper le thinking (qwen3…)
    models = [cfg["model"]] + ([cfg["fallback"]] if cfg.get("fallback") else [])
    attempts = max(1, settings.AI_MAX_ATTEMPTS)

    last_parsed = None
    last_error: HTTPException | None = None
    for model in models:
        for attempt in range(1, attempts + 1):
            try:
                text = _post_generate(model, prompt, system, num_ctx, temperature, as_json, think)
            except HTTPException as e:
                # Erreur d'infra (503/504/500 d'Ollama) : inutile de réessayer CE
                # modèle -> on bascule sur le suivant (fallback défini dans routing.yaml).
                last_error = e
                logger.warning(
                    "[%s] modèle %s indisponible (%s) — bascule vers le suivant.",
                    task,
                    model,
                    e.detail,
                )
                break
            logger.debug("[%s/%s] essai %d : %s…", task, model, attempt, text[:200])

            if not as_json:
                if text.strip() and (is_valid is None or is_valid(text)):
                    return text
                continue

            try:
                result = extract_json_from_text(text)
            except json.JSONDecodeError:
                continue  # non parsable -> nouvel essai
            if result and (is_valid is None or is_valid(result)):
                return result
            last_parsed = result or last_parsed

    # Épuisé : on rend le dernier JSON parsable (l'appelant complète ses défauts) ;
    # sinon on remonte l'erreur d'infra si tous les modèles ont échoué, ou on échoue proprement.
    if as_json and last_parsed is not None:
        return last_parsed
    if last_error is not None:
        raise last_error
    raise HTTPException(
        status_code=500,
        detail=f"Réponse IA {'invalide' if as_json else 'vide'} pour la tâche '{task}'.",
    )


# ============================ Chat + outils (agent) ============================


def chat_call(
    model: str,
    messages: list[dict],
    tools: list | None = None,
    num_ctx: int = 8192,
    temperature: float = 0,
) -> dict:
    """Un appel HTTP à /api/chat (multi-tours + tool-calling). Renvoie le dict
    `message` d'Ollama, qui peut contenir `content` et/ou `tool_calls`. Même
    sérialisation GPU et gestion d'erreur d'infra que `generate`."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": False,  # coupe le raisonnement des modèles 'thinking'
        "keep_alive": settings.OLLAMA_KEEP_ALIVE,
        "options": {"temperature": temperature, "num_ctx": num_ctx, "seed": settings.AI_SEED},
    }
    if tools:
        payload["tools"] = tools
    try:
        with _GPU_LOCK:  # une génération LLM à la fois (VRAM 8 Go)
            r = requests.post(settings.OLLAMA_CHAT_URL, json=payload, timeout=300)
        r.raise_for_status()
        return r.json().get("message", {}) or {}
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, detail="Ollama n'est pas démarré (lancez 'ollama serve')."
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Le modèle met trop de temps à répondre.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur Ollama chat (%s): %s", model, e)
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'appel au modèle.")


def chat_stream(
    model: str,
    messages: list[dict],
    tools: list | None = None,
    num_ctx: int = 8192,
    temperature: float = 0,
):
    """Variante STREAMING de `chat_call` : générateur qui `yield` au fil de l'eau.

    - `{"delta": "<fragment de texte>"}` pour chaque morceau de contenu ;
    - un dernier `{"tool_calls": [...], "done": True}` à la fin du tour (les
      `tool_calls` éventuels arrivent groupés en fin de génération avec Ollama).

    Le verrou GPU est tenu sur TOUTE la durée du flux (une génération LLM à la
    fois, VRAM 8 Go). Les erreurs d'infra lèvent une HTTPException, comme `generate`."""
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "think": False,
        "keep_alive": settings.OLLAMA_KEEP_ALIVE,
        "options": {"temperature": temperature, "num_ctx": num_ctx, "seed": settings.AI_SEED},
    }
    if tools:
        payload["tools"] = tools
    try:
        with _GPU_LOCK:  # sérialise le GPU pour toute la durée du stream
            with requests.post(
                settings.OLLAMA_CHAT_URL, json=payload, stream=True, timeout=300
            ) as r:
                r.raise_for_status()
                tool_calls: list = []
                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    msg = obj.get("message") or {}
                    delta = msg.get("content") or ""
                    if delta:
                        yield {"delta": delta}
                    if msg.get("tool_calls"):
                        tool_calls += msg["tool_calls"]
                    if obj.get("done"):
                        yield {"tool_calls": tool_calls, "done": True}
                        return
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, detail="Ollama n'est pas démarré (lancez 'ollama serve')."
        )
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Le modèle met trop de temps à répondre.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Erreur Ollama chat stream (%s): %s", model, e)
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'appel au modèle.")


# ============================ Préchauffage ============================


def warmup(models: list[str] | None = None) -> None:
    """Précharge des modèles en VRAM (prompt minimal) pour éviter le cold-start du
    PREMIER vrai appel (chargement du modèle = le gros du délai). Best-effort :
    n'interrompt jamais le démarrage si Ollama est éteint. À lancer en tâche de fond."""
    mods = models if models is not None else settings.AI_WARMUP_MODELS
    for model in mods:
        try:
            with _GPU_LOCK:
                requests.post(
                    settings.OLLAMA_GENERATE_URL,
                    json={
                        "model": model,
                        "prompt": "ok",
                        "stream": False,
                        "keep_alive": settings.OLLAMA_KEEP_ALIVE,
                        "options": {"num_ctx": 512, "num_predict": 1},
                    },
                    timeout=180,
                )
            logger.info("Modèle préchauffé : %s", model)
        except Exception as e:
            logger.warning("Préchauffage %s ignoré (%s).", model, e)
