# 🎨 Design — Maquette UI/UX « La Courbe »

Travail UI/UX **déplacé ici** depuis l'espace de travail temporaire. C'est la
**référence d'ergonomie et de parcours** pour l'implémentation Vue à venir — le
rendu final devra faire **nettement mieux** graphiquement, mais les 34 écrans et
les 3 parcours (Collaborateur / Manager / RH) sont déjà cartographiés ici.

## Contenu

| Fichier | Rôle |
|---|---|
| `maquette/BMCI-La-Courbe-COMPLET.html` | **Prototype assemblé** (34 écrans, photos, profondeur visuelle) — ouvrable au double-clic |
| `maquette/BMCI-La-Courbe-blanc-vert.html` | Base avec polices embarquées (avant assemblage) |
| `maquette/base_reference.html` | Référence allégée (conventions, sans polices base64) |
| `maquette/bmci-workflow-map.html` | Cartographie des parcours (existant vs manquant) |
| `maquette/assemble.js` | Pipeline d'assemblage (modules → prototype, photos, polish) |
| `maquette/prep_photos.py` | Redimensionne/encode les portraits en base64 |
| `maquette/mod_*.js` | Modules par parcours (collab, manager, rh, access) |
| `maquette/mod_contract.md` | Contrat partagé des modules |
| `maquette/photo_*.b64` | Portraits encodés (jm, sk, ahmed, woman2) |
| `assets/portrait-*.png` | Portraits sources (personas) |

## Personas (→ répertoire des comptes synthétiques)

| Persona | Rôle | Portrait |
|---|---|---|
| Jean-Marc Dupont | Collaborateur (Analyste Risque Senior) | `assets/portrait-jean-marc-dupont.png` |
| Sarah Kabbaj | Manager / Directrice | `assets/portrait-sarah-kabbaj.png` |
| Alice Martin / Aya Bennani | Collaboratrices / hauts potentiels | `assets/portrait-alice-aya.png` |
| Ahmed B. | Pair / collaborateur | `assets/portrait-ahmed-b.png` |

Ces personas alimenteront le **seed synthétique** (voir
[`../docs/SSO-SAML-ET-IDENTITE.md`](../docs/SSO-SAML-ET-IDENTITE.md) §3c).

## Régénérer le prototype

```bash
cd maquette
node assemble.js         # réassemble BMCI-La-Courbe-COMPLET.html
```

## Contraintes design (feedback utilisateur)

- **Blanc + vert uniquement**, **jamais de noir ni de mode sombre**.
- Photos de personnes réelles (embarquées en base64, contrainte CSP des artifacts).
- Profondeur « façon Stitch » : ombres douces, hover-lift, hero « aperçu produit ».
