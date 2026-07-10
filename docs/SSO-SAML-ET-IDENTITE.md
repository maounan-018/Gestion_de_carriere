# Identité, SSO SAML & répertoire des comptes

> Porté depuis *smart-objective* (patron éprouvé, `SSO_SAML.md`), adapté à la
> plateforme carrière. Objectif : **aucune inscription publique**, comptes
> provisionnés par l'annuaire de la banque, et un **répertoire de comptes
> synthétiques** pour démontrer/tester sans exposer d'employés réels.

---

## 1. SSO SAML 2.0 (production)

- **Protocole** : SAML 2.0, IdP = **ADFS** ou **Entra ID** (au choix de la DSI BMCI).
- **Librairie** : `python3-saml` (dépendance **optionnelle**, `requirements-saml.txt`).
- **JIT provisioning** : au 1ᵉʳ login SSO, le compte est **créé automatiquement**,
  le **rôle est déduit des groupes de l'annuaire** (ex. `BMCI-RH` → RH,
  `BMCI-Managers` → MANAGER, défaut → COLLAB).
- **Assertions signées exigées** (RSA-SHA256, strict), **token jamais dans l'URL**
  (échange par code à usage unique).
- En production + SSO configuré : **la connexion locale et les comptes démo sont
  coupés automatiquement** (`LOCAL_AUTH_ENABLED=auto`, `SEED_DEMO_ACCOUNTS=false`).

### Flux
```
Utilisateur ──▶ /api/auth/saml/login ──▶ IdP (ADFS/Entra) ──▶ /api/auth/saml/acs
      ▲                                         (assertion signée)      │
      └──── cookie de session (HttpOnly/Secure/SameSite) ◀── /exchange ─┘
```

### Endpoints (identiques à smart-objective)
`/api/auth/saml/login` · `/acs` · `/metadata` (à donner à la DSI) · `/exchange` · `/status`.

### Simulation (dev, sans IdP)
`SAML_SIMULATION=true` permet de tester tout le flux **sans** ADFS/Entra — **refusé
si `ENV=production`**. Indispensable pour développer le SSO avant que la DSI ne
fournisse les vrais paramètres.

---

## 2. Sécurité de session (héritée)

| Mesure | Mise en œuvre |
|---|---|
| Mots de passe (local de secours) | PBKDF2-HMAC-SHA256 salé, vérif temps constant |
| Session | token aléatoire **hashé en base**, cookie HttpOnly/Secure/SameSite |
| CSRF | double-submit (`csrf_token` ↔ `X-CSRF-Token`) sur les mutations |
| Anti brute-force | blocage 429 par **email ET IP** |
| Inscription publique | **supprimée** (aucune auto-attribution de rôle) |

---

## 3. Répertoire des comptes — trois natures

La plateforme distingue **trois types de comptes**, gérés séparément :

### a) Comptes réels (humains)
- Créés par **SSO/JIT** (prod) ou par l'admin via `create_user.py` (local de secours).
- Rôle : COLLAB / MANAGER / RH / ADMIN. Périmètre RBAC strict.

### b) Comptes de service / techniques (connecteurs SIRH)
- Pour les **intégrations** (Workday, SAP SuccessFactors, LMS…) évoquées par les
  acteurs du secteur : imports d'effectifs, de postes, de formations.
- **Non-interactifs** : pas de mot de passe humain, mais **clé/API token** à portée
  restreinte, **journalisés** (audit), **révocables**. Rôle dédié `SERVICE` (lecture/écriture bornée).
- Stockés dans le même annuaire mais marqués `type=service`, exclus du SSO humain.

### c) Comptes synthétiques (« comptes artificiels » de démonstration)
- **Personas fictifs** (Jean-Marc Dupont, Sarah Kabbaj, Alice Martin, Aya Bennani,
  Ahmed B.…) déjà présents dans la maquette `design/`, avec **portraits** (`design/assets/`).
- Servent à **peupler une démo réaliste** (cartographie, matching, succession) **sans
  aucune donnée d'employé réel** → parfait pour présenter à un COMEX / jury.
- Générés et chargés par un **seed dédié** (`backend/app/database/seed_personas.py`),
  marqués `type=synthetic`, **désactivés automatiquement en production**
  (`SEED_DEMO_ACCOUNTS=false` + `ENV=production`).
- Un **répertoire versionné** (`ia/referentiels/personas/` ou `backend/.../seed`)
  décrit chaque persona : identité, poste, compétences, historique, aspirations —
  cohérent avec le graphe de compétences pour que les démos « tiennent ».

> ⚠️ **Cloisonnement** : les comptes synthétiques et de service ne doivent **jamais**
> se mélanger aux comptes réels en production. Le marquage `type` + le flag `ENV`
> garantit qu'un environnement de prod ne charge que des comptes réels.

---

## 4. Configuration (`.env`) — extrait

```ini
AUTH_PROVIDER=local            # local | saml
LOCAL_AUTH_ENABLED=auto        # auto | true | false
SAML_SIMULATION=false          # true en dev sans IdP (interdit en prod)
SAML_SP_* / SAML_IDP_*         # secrets réels → .env.local (jamais committé)
SAML_ALLOWED_GROUPS=BMCI-RH,BMCI-Managers,BMCI-Collab
SEED_DEMO_ACCOUNTS=true        # false en prod
SEED_SYNTHETIC_PERSONAS=true   # personas de démo (false en prod)
```

---

## 5. À faire

- [ ] Porter `auth/` (IdentityProvider local + SAML) depuis smart-objective.
- [ ] Adapter les groupes→rôles à l'annuaire réel BMCI (à confirmer avec la DSI).
- [ ] Écrire `seed_personas.py` à partir du répertoire des personas de la maquette.
- [ ] Définir le rôle `SERVICE` + gestion des tokens des connecteurs SIRH.

> Référence d'implémentation : `bmci-smartobjective/SSO_SAML.md` (simulation → réel → retrait).
