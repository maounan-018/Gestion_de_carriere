#!/usr/bin/env python3
"""
core/config.py — Configuration centralisée de l'application.

RÔLE
    Charge le .env (sans dépendance externe, comme smart-objective) et expose
    toute la configuration via l'objet `settings`. Charge aussi le routage
    modèle-par-tâche (`ia/routing.yaml`) : c'est ici qu'on relie chaque
    fonctionnalité au meilleur modèle IA local, sans coder de modèle en dur.

SÉCURITÉ
    Aucun secret codé en dur. CORS jamais en "*". L'IA reste 100 % locale.

EMPLACEMENT MVC
    Couche "core" : configuration et paramètres transverses.
"""

import os
import logging

logger = logging.getLogger(__name__)

# Racine du dépôt = backend/app/core/config.py -> remonter de 4 niveaux.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def load_dotenv(path: str = ".env") -> None:
    """Charge un .env simple (clé=valeur) dans os.environ, sans jamais écraser
    une variable déjà présente (l'environnement réel reste prioritaire)."""
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        logger.warning("Lecture .env impossible: %s", e)


def _load_routing(path: str) -> dict:
    """Charge le routage modèle-par-tâche (ia/routing.yaml). Tolérant : si le
    fichier ou PyYAML manque, on renvoie un routage vide (le code appelant a des
    valeurs de repli), sans faire tomber le démarrage."""
    if not path or not os.path.exists(path):
        logger.warning("routing.yaml introuvable (%s) — routage IA par défaut.", path)
        return {}
    try:
        import yaml  # dépendance déclarée dans requirements.txt
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("Lecture routing.yaml impossible (%s): %s", path, e)
        return {}


class Settings:
    """Paramètres applicatifs lus depuis l'environnement (après load_dotenv)."""

    def __init__(self) -> None:
        # Application
        self.APP_NAME = os.getenv("APP_NAME", "BMCI-Gestion-Carrieres")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()
        self.ENV = os.getenv("ENV", "development").strip().lower()

        # --- IA locale (Ollama) ---
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.OLLAMA_GENERATE_URL = f"{self.OLLAMA_BASE_URL}/api/generate"
        self.OLLAMA_CHAT_URL = f"{self.OLLAMA_BASE_URL}/api/chat"
        # /api/embed (pluriel) accepte une LISTE en entrée -> embeddings PAR LOTS
        # (~18 ms/embed vs ~2 s en un-par-un). Indispensable pour ingérer ESCO (~14k).
        self.OLLAMA_EMBED_URL = f"{self.OLLAMA_BASE_URL}/api/embed"
        self.OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")
        # Dimension des vecteurs (fixe le schéma vec0). bge-m3 = 1024.
        self.EMBED_DIM = int(os.getenv("EMBED_DIM", "1024"))
        self.AI_MAX_ATTEMPTS = int(os.getenv("AI_MAX_ATTEMPTS", "2"))
        self.AI_SEED = int(os.getenv("AI_SEED", "42"))

        # Routage modèle-par-tâche (ia/routing.yaml)
        self.ROUTING_PATH = os.getenv("ROUTING_PATH", "").strip() or os.path.join(REPO_ROOT, "ia", "routing.yaml")
        self.routing = _load_routing(self.ROUTING_PATH)

        # --- Reranker (hors Ollama, FlagEmbedding) ---
        self.RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
        self.RERANKER_ENABLED = os.getenv("RERANKER_ENABLED", "true").strip().lower() in ("1", "true", "yes")

        # --- Base de données ---
        self.DB_PATH = os.getenv("DATABASE_PATH", "bmci_carrieres.db")

        # --- Référentiels de compétences (ia/referentiels/) ---
        self.REFERENTIELS_DIR = os.getenv("REFERENTIELS_DIR", "").strip() or os.path.join(REPO_ROOT, "ia", "referentiels")

        # --- Sessions / sécurité (repris de smart-objective) ---
        self.TOKEN_EXPIRY_HOURS = int(os.getenv("SESSION_DURATION_HOURS", "24"))
        self.PBKDF2_ITERATIONS = int(os.getenv("PBKDF2_ITERATIONS", "200000"))
        self.MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.LOGIN_LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))
        self.MAX_REQUEST_SIZE_BYTES = int(os.getenv("MAX_REQUEST_SIZE_MB", "25")) * 1024 * 1024

        # --- CORS — JAMAIS "*" (combiné à allow_credentials = faille CSRF) ---
        _origins_raw = os.getenv("ALLOWED_ORIGINS", "").strip()
        if not _origins_raw or _origins_raw == "*":
            raise RuntimeError(
                "ALLOWED_ORIGINS doit être défini explicitement dans .env "
                "(ex: http://localhost:3000). Le wildcard \"*\" est interdit."
            )
        self.ALLOWED_ORIGINS = [o.strip() for o in _origins_raw.split(",") if o.strip()]

        # --- Authentification / SSO ---
        self.AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "local").strip().lower()
        self.LOCAL_AUTH_ENABLED = os.getenv("LOCAL_AUTH_ENABLED", "auto").strip().lower()
        self.SAML_SIMULATION = os.getenv("SAML_SIMULATION", "false").strip().lower() in ("1", "true", "yes")
        self.SEED_DEMO_ACCOUNTS = os.getenv("SEED_DEMO_ACCOUNTS", "true").strip().lower() in ("1", "true", "yes")
        self.SEED_SYNTHETIC_PERSONAS = os.getenv("SEED_SYNTHETIC_PERSONAS", "true").strip().lower() in ("1", "true", "yes")
        self.SEED_SYNTHETIC_OFFERS = os.getenv("SEED_SYNTHETIC_OFFERS", "true").strip().lower() in ("1", "true", "yes")

        # --- Cookies de session (HttpOnly) + CSRF double-submit ---
        self.SESSION_COOKIE = os.getenv("SESSION_COOKIE", "bmci_session")
        self.CSRF_COOKIE = os.getenv("CSRF_COOKIE", "bmci_csrf")
        self.CSRF_HEADER = os.getenv("CSRF_HEADER", "X-CSRF-Token")
        # "auto" = sécurisé en production (HTTPS), permissif en dev (HTTP localhost).
        self._cookie_secure_raw = os.getenv("COOKIE_SECURE", "auto").strip().lower()
        self.COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").strip().lower()

    @property
    def is_production(self) -> bool:
        return self.ENV in ("production", "prod")

    @property
    def cookie_secure(self) -> bool:
        """Flag Secure des cookies : forcé en prod (HTTPS), sinon selon COOKIE_SECURE."""
        if self._cookie_secure_raw == "auto":
            return self.is_production
        return self._cookie_secure_raw in ("1", "true", "yes")

    def task_model(self, task: str) -> dict:
        """Renvoie la config du modèle pour une tâche (modèle, num_ctx, température,
        format, fallback), depuis routing.yaml. Repli sûr si tâche inconnue :
        qwen3:8b, num_ctx 4096 (leçon de perf : toujours borner le contexte)."""
        cfg = ((self.routing or {}).get("taches") or {}).get(task)
        if not cfg:
            logger.warning("Tâche IA inconnue dans routing.yaml: '%s' — repli qwen3:8b.", task)
            return {"model": "qwen3:8b", "num_ctx": 4096, "temperature": 0}
        cfg = dict(cfg)
        cfg.setdefault("num_ctx", 4096)
        cfg.setdefault("temperature", 0)
        return cfg


# .env.local (secrets, ignoré par git) lu EN PREMIER = prioritaire ; puis .env.
load_dotenv(".env.local")
load_dotenv(".env")
settings = Settings()
