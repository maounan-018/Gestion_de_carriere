# CONTRAT DE MODULE — BMCI Carrière « La Courbe »

Tu construis des écrans supplémentaires pour un prototype HTML **existant** (une seule page, routeur JS maison). Ton code sera **collé tel quel** à l'intérieur de l'IIFE existante et dans le `<style>`. Respecte ce contrat **à la lettre**, sinon l'intégration casse.

## 0. Avant de coder
Lis `base_reference.html` (même dossier) : c'est le prototype actuel **sans les polices** (base64 retiré). Tu y verras le design system (CSS), les helpers, et des exemples d'écrans (`S.portail`, `S.collab`, `S.manager`, `S.rh`, `S.reco`, `S.offres`, `S.entretien`, `S.inscription`…). **Copie leurs conventions.**

## 1. Règles absolues
- **Aucune couleur hors palette.** Utilise UNIQUEMENT les variables CSS existantes (`var(--green)`, `var(--green-deep)`, `var(--green-soft)`, `var(--ink)`, `var(--ink-2)`, `var(--ink-3)`, `var(--paper)`, `var(--panel)`, `var(--panel-2)`, `var(--border)`, `var(--gold)` pour réussite/objectif, `var(--amber)`/`--danger` pour alerte). **JAMAIS de noir en fond.** Pas de mode sombre.
- **Typo** : titres via `class="disp"` ou headings dans `.sec-h h3` / `.top .tt` (déjà en Bricolage). Corps = défaut (Hanken). N'ajoute pas de police.
- **Langue** : français. E-mails au format `prenom.nom@bnpparibas.com`.
- **Aucune ressource externe** (pas d'image URL, pas de CDN, pas de fetch). Avatars = `<div class="ava md">XX</div>` (initiales). Si une photo est nécessaire, laisse un `.ava`.
- Réutilise les classes existantes (voir §4). N'invente une classe QUE si indispensable, et déclare-la dans le bloc CSS.
- Respecte `prefers-reduced-motion` (déjà géré globalement).

## 2. Helpers DISPONIBLES dans le scope (NE PAS redéfinir, NE PAS importer)
- `ic(name,cls)` → renvoie un `<svg>`. Noms dispo : home,user,route,chat,brief,book,team,grid,spark,bell,gear,lock,mail,check,shield,search,logout,pin,cal,clock,flag,bolt,send,mic,filter,award. Ex : `ic('check','s')` (s = petit).
- `sidebar(role,active)` → barre latérale canonique. role ∈ `'collab'|'manager'|'rh'`. active = le libellé exact à surligner (ex `'Offres internes'`).
- `top(titre,sousTitre,role)` → barre supérieure avec badge de rôle.
- `crumb([[label,goId],[label,null]])` → fil d'ariane (dernier élément goId=null = page courante).
- `openModal(html)` → ouvre une modale, **renvoie l'élément `.modal`** (pour brancher tes listeners dessus). `closeModal()` ferme. Un bouton avec l'attribut `data-mclose` ferme aussi.
- `toast(msg[,kind])` → notification transitoire. kind `'ok'` (défaut, vert) ou `'info'`.
- `emptyState(icon,titre,texte,cta)` → HTML d'état vide. cta optionnel = `{label, go}` ou `{label, act}`.
- `go(id)` → navigue vers l'écran id. `$(sel)` / `$$(sel)` = querySelector(All) dans #vp.
- `drawPath(el)` anime un tracé SVG (optionnel).

## 3. FORMAT DE SORTIE (obligatoire)
Écris **un seul fichier** `mod_<NOM>.js` (nom donné dans ta tâche) contenant EXACTEMENT ces 3 sections délimitées :

```
/*==SCREENS==*/
[["editProfil","Éditer mon profil","Collaborateur"],["mesCandidatures","Mes candidatures","Collaborateur"]]
/*==CSS==*/
.macle{...}   /* uniquement si nécessaire ; sinon laisse vide */
/*==JS==*/
S.editProfil=()=>`...`;
WIRE.editProfil=function(){ /* listeners sur les éléments de #vp */ };
S.mesCandidatures=()=>`...`;
```

- `/*==SCREENS==*/` : un tableau JSON `[[id,titre,groupe],...]` de TOUS tes écrans (groupe = `Collaborateur`/`Manager`/`RH`/`Accès`).
- `/*==CSS==*/` : CSS additionnel (souvent vide). Pas de `<style>`, juste les règles.
- `/*==JS==*/` : tes `S.<id>=()=>\`...\`;` et `WIRE.<id>=function(){...};`. **Pas d'IIFE, pas de DOMContentLoaded, pas de `const` de helpers déjà existants.**

## 4. Gabarits à copier

**Écran d'app (avec sidebar) :**
```js
S.editProfil=()=>`<div class="fade app">${sidebar('collab','Mon profil')}<div class="main">${top('Éditer mon profil','Votre profil de carrière','collab')}
  <div class="content">
    ${crumb([['Mon profil','collab'],['Éditer',null]])}
    <div class="card p"> ... </div>
  </div>
</div></div>`;
```

**Interactions (branchées après rendu) :**
```js
WIRE.editProfil=function(){
  const save=$('#saveProfil'); if(save) save.addEventListener('click',()=>{ toast('Profil mis à jour'); go('collab'); });
};
```

**Modale multi-étapes (ex candidature) :**
```js
WIRE.offreDetail=function(){
  const b=$('#postuler'); if(!b)return;
  b.addEventListener('click',()=>{
    const m=openModal('<div class="mhead"><h3>Postuler</h3><button class="xbtn" data-mclose>✕</button></div><div id="mbody">…étape 1…</div>');
    // gérer les étapes dans m.querySelector('#mbody'), puis: toast('Candidature envoyée'); closeModal(); go('mesCandidatures');
  });
};
```

**Champs de formulaire dispo** : `.formrow > label + (.ctrl | textarea.ta | select.ctrl)`, `.seg` (onglets segmentés), `.rating` (étoiles), `.ministep` (étapes de modale), `.tog` (public/privé). **Boutons** : `.btn .btn-p` (principal), `.btn .btn-g` (secondaire), `.btn-sm`, `.block`. **Cartes** : `.card.p`, `.sec-h>h3`. **Divers** : `.chip`, `.chip.g`, `.chip.gap`, `.pill.new/.hot/.warn/.mut/.ai`, `.badge.b-role/.b-gold`, `.kpi`, `.bar-row/.bar-tr`, `.rec.ai/.warn/.crit`, `.match`, `.jalon`, `.offer`, `.wnote`, `.mini-ring` (anneau `style="--p:76"><i>76%</i>`), `.gauges`.

## 5. Qualité
- Contenu **réaliste** (noms, chiffres, métiers bancaires BMCI/BNP Paribas), jamais de lorem.
- Chaque écran de détail commence par un `crumb(...)`.
- Chaque action se termine par un `toast(...)` de confirmation et/ou une navigation.
- Écris du contenu dense mais lisible, cohérent avec les écrans existants.
- Vérifie mentalement que ton JS parse (guillemets, backticks, `${}`).

Livre le fichier `mod_<NOM>.js` dans ce dossier, puis résume en 3 lignes les écrans créés + les liens attendus depuis les écrans existants (ex : « le bouton *Postuler* de `S.offres` doit pointer vers `offreDetail` »).
