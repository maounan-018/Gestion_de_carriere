# Déploiement — Front sur Vercel, backend local (Ollama)

## Architecture retenue

```
Navigateur ─▶ Front (Vercel, https://<app>.vercel.app)   ← statique, buildé par Vite
                   │  appels API en CROSS-ORIGIN (auth Bearer)
                   ▼
             FastAPI  (http://localhost:5001, SUR LA MACHINE de l'utilisateur)
                   ├─▶ Ollama local (:11434)          ← IA 100 % locale
                   └─▶ Supabase Postgres / pgvector   ← persistance cloud
```

Le front déployé n'appelle **pas** un backend hébergé : il appelle le FastAPI qui
tourne **en local chez l'utilisateur** (`VITE_API_BASE=http://localhost:5001`, cf.
`frontend/.env.production`). Conséquence assumée : le site n'est **fonctionnel que
si l'utilisateur lance le backend** (+ Ollama) sur sa propre machine. Supabase
n'apporte que la base de données ; il ne fait pas tourner le Python.

## Pourquoi Bearer (et pas les cookies)

En cross-origin (site public HTTPS → `localhost`), les cookies same-site ne sont
pas transmis. L'auth passe donc par l'en-tête `Authorization: Bearer <token>` :
- le `/auth/login` renvoie le jeton dans le corps (`token`), mémorisé côté front
  (localStorage) et rejoué sur chaque requête ;
- le backend accepte déjà le Bearer (`extract_token`) ;
- le CSRF double-submit est **sauté** quand l'auth est Bearer (aucun cookie → aucun
  vecteur CSRF ; cf. `_check_csrf`).

En dév local (`VITE_API_BASE` vide), **rien ne change** : proxy Vite `/api → :5001`,
cookies HttpOnly + CSRF comme avant.

---

## 1. Pousser le repo sur GitHub

Les secrets sont déjà couverts par `.gitignore` (`*.db`, `MDP.txt`, `.env.local`,
`backend/data/cv_profil/`). `backend/.env` est la config de **dév sans secret**.
Vérifier avant de pousser :

```bash
git status --ignored --short   # confirme que *.db, .env.local, MDP.txt sont ignorés
```

Puis créer le repo et pousser (remplacer l'URL) :

```bash
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin main
```

## 2. Déployer le front sur Vercel

Sur vercel.com → **Add New Project** → importer le repo GitHub, puis :

- **Root Directory** : `frontend`  ← indispensable (le `vercel.json` y est).
- Framework **Vite**, build `npm run build`, output `dist` (déjà dans `vercel.json`).
- Aucune variable d'env à ajouter : `VITE_API_BASE` vient de `frontend/.env.production`.

Vercel attribue une URL du type `https://<app>.vercel.app` (domaine gratuit).

> Pour piloter en CLI : `cd frontend && vercel && vercel --prod`.

## 3. Autoriser l'origine Vercel côté backend (CORS)

Dans `backend/.env.local` (ignoré par git), ajouter l'URL du site à `ALLOWED_ORIGINS` :

```
ALLOWED_ORIGINS=http://localhost:3001,https://<app>.vercel.app
```

Pour aussi accepter les **preview deployments** (URLs aléatoires), au lieu de les
lister une par une :

```
ALLOWED_ORIGIN_REGEX=https://.*\.vercel\.app$
```

Redémarrer le backend après modification.

## 4. Lancer le backend en local (chaque utilisateur)

Prérequis : Ollama démarré (modèles tirés) + `DATABASE_URL` Supabase dans
`backend/.env.local`. Puis :

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 5001
```

Au premier appel du site, **Chrome affiche un préflight Private Network Access**
(site public → réseau local). Le backend y répond
`Access-Control-Allow-Private-Network: true` ; l'utilisateur doit **autoriser**
l'accès au réseau local si le navigateur le demande.

---

## Limites à connaître

- **Le site ne marche que si le backend local tourne.** Un visiteur sans backend
  voit l'UI mais les appels échouent (c'est le choix « backend chez l'utilisateur »).
- **Navigateurs** : Chrome/Edge gèrent le mieux l'accès public → `localhost`.
  Firefox/Safari appliquent des règles différentes (Private/Local Network Access).
- **Coach (SSE)** : le flux passe en direct depuis le backend local (pas de proxy
  Vercel), donc l'effet « frappe en direct » est préservé.
- **HTTPS → http://localhost** : autorisé (localhost est « potentially trustworthy »,
  pas de blocage mixed-content).
