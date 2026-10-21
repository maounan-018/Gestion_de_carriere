#!/usr/bin/env python3
"""
backend/gunicorn.conf.py — Configuration de production du serveur applicatif.

ROLE
    En dev, l'app tourne derriere `uvicorn --reload` (1 process, auto-reload).
    En prod, on remplace par gunicorn qui gere plusieurs WORKERS uvicorn
    (concurrence reelle, resilience : un worker qui plante est redemarre
    automatiquement sans couper le service).

LANCEMENT PROD (depuis backend/)
    gunicorn -c gunicorn.conf.py app.main:app

ARCHITECTURE
    gunicorn (master, orchestre les workers)
      |
      +-- worker 1 : uvicorn.workers.UvicornWorker (ASGI, 1 event loop)
      +-- worker 2 : uvicorn.workers.UvicornWorker
      +-- ... (N workers = par defaut CPU*2+1)

    Attention : le GPU est SERIALISE au niveau application (ai_router._GPU_LOCK,
    `threading.Semaphore(1)`). Il protege contre la concurrence intra-process
    mais PAS inter-process -> en multi-workers, deplacer ce lock vers un
    semaphore inter-process (ex. filelock) OU limiter le nb de workers qui
    appellent Ollama a 1. Pour une premiere mise en prod sur un serveur avec
    1 seul GPU : WEB_CONCURRENCY=2 (API + 1 worker IA actif) est raisonnable.

VARIABLES D'ENVIRONNEMENT
    WEB_CONCURRENCY  : nb de workers (defaut : CPU*2+1).
    BIND_HOST        : adresse d'ecoute (defaut 127.0.0.1 ; mettre 0.0.0.0
                       derriere un reverse proxy nginx/traefik, jamais expose
                       directement sur Internet).
    BIND_PORT        : port (defaut 5001, aligne sur le dev).
    GUNICORN_TIMEOUT : timeout d'une requete en secondes (defaut 180 : certains
                       appels IA Ollama prennent plus d'une minute).

EMPLACEMENT MVC
    Infra / exploitation, hors de la logique applicative.
"""

from __future__ import annotations

import multiprocessing
import os

# ---- Reseau ----------------------------------------------------------------
bind = f"{os.getenv('BIND_HOST', '127.0.0.1')}:{os.getenv('BIND_PORT', '5001')}"
# Backlog = taille de la file d'attente TCP avant que l'OS refuse les connexions.
# 2048 convient a une charge modeste (interne banque) ; monter si pic d'arrivee.
backlog = int(os.getenv("GUNICORN_BACKLOG", "2048"))


# ---- Workers ---------------------------------------------------------------
# Formule recommandee par gunicorn : CPU*2+1. On la surcharge via WEB_CONCURRENCY
# si l'infra l'impose (GPU unique partage avec Ollama -> 2 ou 3 suffisent).
workers = int(os.getenv("WEB_CONCURRENCY", str(multiprocessing.cpu_count() * 2 + 1)))

# ASGI (FastAPI) : il FAUT UvicornWorker, pas le worker sync par defaut.
worker_class = "uvicorn.workers.UvicornWorker"

# Nombre de connexions concurrentes par worker (ASGI event loop). 1000 est le
# defaut uvicorn ; aligne avec les workers thread-pooled.
worker_connections = int(os.getenv("WORKER_CONNECTIONS", "1000"))

# Timeout : un worker qui depasse cette duree est tue + redemarre. On autorise
# 3 min pour laisser passer les appels IA les plus longs (Coach Carriere +
# mistral-nemo peut dépasser 60 s).
timeout = int(os.getenv("GUNICORN_TIMEOUT", "180"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# Recyclage preventif : au bout de max_requests requetes, un worker est redemarre.
# Immunise contre les fuites memoire lentes (ex. embeddings qui gardent des
# references). Jitter evite que tous les workers redemarrent en meme temps.
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))


# ---- Journalisation --------------------------------------------------------
# access_log : INFO par requete (methode, path, status, duree). "-" = stdout
# pour permettre au reverse proxy / au systeme d'init (systemd, k8s) de capturer.
accesslog = os.getenv("GUNICORN_ACCESSLOG", "-")
errorlog = os.getenv("GUNICORN_ERRORLOG", "-")
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")

# Format d'access log : status, methode, path, duree ms, identifiant utilisateur
# (vide si non authentifie), user-agent. Permet le monitoring sans traverser le code.
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)s "%(f)s" "%(a)s"'


# ---- Processus -------------------------------------------------------------
# Nom affiche dans `ps` / `top` : identifie clairement notre app.
proc_name = "bmci-carrieres-api"

# En prod, un systemd/supervisord gere le lifecycle ; en standalone,
# daemonize=False est le defaut (geste explicite pour clarte).
daemon = False
