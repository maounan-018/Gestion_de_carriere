const fs = require('fs');
const path = require('path');
const vm = require('vm');

const DIR = __dirname;
const TARGET = path.join(DIR, 'BMCI-La-Courbe-blanc-vert.html');
const OUT = path.join(DIR, 'BMCI-La-Courbe-COMPLET.html');
const MODULES = ['mod_collab.js', 'mod_manager.js', 'mod_rh.js', 'mod_access.js'];

function parseModule(file) {
  const raw = fs.readFileSync(path.join(DIR, file), 'utf8');
  const iS = raw.indexOf('/*==SCREENS==*/');
  const iC = raw.indexOf('/*==CSS==*/');
  const iJ = raw.indexOf('/*==JS==*/');
  if (iS < 0 || iC < 0 || iJ < 0) throw new Error(`${file}: sections manquantes`);
  const screensRaw = raw.slice(iS + 15, iC).trim();
  const css = raw.slice(iC + 11, iJ).trim();
  const js = raw.slice(iJ + 10).trim();
  const screens = JSON.parse(screensRaw);
  return { file, screens, css, js };
}

const mods = MODULES.map(parseModule);

// duplicate detection
const seen = {};
for (const m of mods) for (const s of m.screens) {
  if (seen[s[0]]) throw new Error(`ID dupliqué "${s[0]}" dans ${m.file} et ${seen[s[0]]}`);
  seen[s[0]] = m.file;
}

// validate each JS section parses in a sandbox with stubbed globals
for (const m of mods) {
  const sandbox = { S: {}, WIRE: {}, sidebar:()=> '', top:()=> '', crumb:()=> '', ic:()=> '',
    openModal:()=>({querySelector:()=>null,querySelectorAll:()=>[]}), closeModal:()=>{}, toast:()=>{},
    emptyState:()=>'', go:()=>{}, $:()=>null, $$:()=>[], drawPath:()=>{}, stepper:()=>'',
    document:{}, window:{}, setTimeout:()=>{}, matchMedia:()=>({matches:false}), NAV:{collab:[],manager:[],rh:[]} };
  try {
    vm.runInNewContext(m.js, sandbox, { filename: m.file });
  } catch (e) {
    throw new Error(`${m.file}: JS invalide -> ${e.message}`);
  }
  const nS = Object.keys(sandbox.S).length, nW = Object.keys(sandbox.WIRE).length;
  console.log(`OK ${m.file}: ${m.screens.length} écrans déclarés, ${nS} S.* définis, ${nW} WIRE.* définis`);
}

// load embedded portrait photos (base64) + build avatar CSS
const PHOTO_CLASSES = ['jm', 'sk', 'ahmed', 'woman2'];
const photoCss = ['\n/* ==== PHOTOS (avatars) ==== */',
  '.ava.ph{background-size:cover;background-position:center 20%;background-repeat:no-repeat;color:transparent;text-shadow:none;overflow:hidden}'];
for (const cls of PHOTO_CLASSES) {
  const b64 = fs.readFileSync(path.join(DIR, `photo_${cls}.b64`), 'utf8').trim();
  photoCss.push(`.ava.${cls}{background-image:url(data:image/jpeg;base64,${b64})}`);
}

// ==== POLISH « façon Stitch » : profondeur, hover-lift, photos premium ====
const polishCss = [`
/* ==== POLISH — profondeur & interactions ==== */
/* cartes interactives qui se soulèvent au survol (le "vivant" façon Stitch) */
.offer,.kpi,.rec,.org-n,.match,.crow{transition:transform .22s cubic-bezier(.22,.8,.28,1),box-shadow .22s,border-color .22s}
.offer:hover,.kpi:hover,.org-n:hover,.match:hover{transform:translateY(-4px);box-shadow:var(--shadow-float);border-color:var(--green-line)}
.rec:hover{transform:translateY(-2px);box-shadow:var(--shadow);border-color:var(--green-line)}
.crow:hover{background:var(--green-ghost);border-radius:12px}
.offer{background:linear-gradient(180deg,#fff,var(--panel));position:relative}
.kpi{background:linear-gradient(180deg,#fff,var(--panel))}
/* boutons : micro-lift + ombre plus riche */
.btn{transition:transform .15s cubic-bezier(.22,.8,.28,1),box-shadow .18s,background .18s,border-color .18s}
.btn-p:hover{transform:translateY(-1px);box-shadow:0 14px 28px -10px rgba(0,145,90,.55),inset 0 1px 0 rgba(255,255,255,.3)}
.btn-g:hover,.btn-s:hover{transform:translateY(-1px)}
.btn:active{transform:translateY(0)}
/* PHOTOS premium : anneau blanc net + ombre flottante (headshots qui "flottent") */
.ava.ph{box-shadow:0 6px 18px -6px rgba(14,26,20,.4),inset 0 0 0 2px #fff,0 0 0 1px rgba(14,26,20,.06)}
.ava.xl.ph{box-shadow:0 14px 30px -12px rgba(14,26,20,.45),inset 0 0 0 3px #fff,0 0 0 1px var(--border)}
.phead .ava.xl.ph{position:relative}
.phead .ava.xl.ph::after{content:"";position:absolute;inset:-6px;border-radius:50%;border:1.5px solid var(--green-line);opacity:.55;pointer-events:none}
/* HERO : le visage de la personne mis en avant (aperçu produit) */
.pv-profile{padding:15px 16px}
.pv-profile .ava.md{width:54px;height:54px;font-size:0}
.pv-profile .ava.ph{box-shadow:0 10px 24px -8px rgba(0,145,90,.5),inset 0 0 0 2px #fff,0 0 0 1px var(--green-line)}
.pv-profile h4{font-size:16px}
/* barre du haut : l'avatar photo prend un anneau discret */
.top .ava.md.ph{box-shadow:0 4px 12px -4px rgba(14,26,20,.4),inset 0 0 0 2px #fff}
/* avis des pairs : la carte respire au survol */
.rev{transition:background .2s,border-radius .2s}.rev:hover{background:var(--green-ghost);border-radius:12px}
/* sections : titres un peu plus présents */
.sec-h h3{letter-spacing:-.01em}
@media (prefers-reduced-motion:reduce){
  .offer,.kpi,.rec,.org-n,.match,.crow,.btn{transition:none}
  .offer:hover,.kpi:hover,.org-n:hover,.match:hover,.rec:hover,.btn-p:hover,.btn-g:hover,.btn-s:hover{transform:none}
}`];

// avatar → photo wiring (applied to final assembled html; AB collision resolved by size)
const AVATARS = [
  [`ava md">JM`, `ava md ph jm">JM`, 3],   // barre du haut, hero, org manager
  [`ava xl">JM`, `ava xl ph jm">JM`, 2],   // profil collab + editProfil
  [`ava sm">JM`, `ava sm ph jm">JM`, 2],   // manager (fiche/évaluation)
  [`ava sm">SK`, `ava sm ph sk">SK`, 3],   // Sarah Kabbaj (avis + RH)
  [`ava sm">AB`, `ava sm ph ahmed">AB`, 1],// Ahmed B. (avis des pairs, homme)
  [`ava xl">AB`, `ava xl ph woman2">AB`, 1],// Aya Bennani (fiche RH, femme)
  [`ava md">AM`, `ava md ph woman2">AM`, 1],// Alice Martin
  [`ava xl">AM`, `ava xl ph woman2">AM`, 1],// Alice Martin (fiche)
];

// build ORDER push entries: [id, title, subtitle, group]
const orderEntries = [];
const allCss = [];
const allJs = [];
for (const m of mods) {
  for (const s of m.screens) {
    orderEntries.push([s[0], s[1], s[2] + ' · parcours détaillé', s[2]]);
  }
  if (m.css) allCss.push(`/* ${m.file} */\n${m.css}`);
  allJs.push(`/* ===== ${m.file} ===== */\n${m.js}`);
}
const orderPush = 'ORDER.push(' + orderEntries.map(e => JSON.stringify(e)).join(',\n') + ');';

let html = fs.readFileSync(TARGET, 'utf8');

// 0) wire links from EXISTING base screens to the new module screens
const WIRES = [
  // connexion → mot de passe oublié
  [`<button class="link">Mot de passe oublié ?</button>`,
   `<button class="link" data-go="motDePasseOublie">Mot de passe oublié ?</button>`, 1],
  // collab → éditer profil
  [`<button class="btn btn-g btn-sm">Modifier</button>`,
   `<button class="btn btn-g btn-sm" data-go="editProfil">Modifier</button>`, 1],
  // collab → suivi des souhaits
  [`<button class="btn btn-g btn-sm block" style="margin-top:12px">Pousser à mon manager</button>`,
   `<button class="btn btn-g btn-sm block" style="margin-top:12px" data-go="souhaitSuivi">Pousser à mon manager</button>`, 1],
  // offres → détail de l'offre (×6)
  [`<button class="btn btn-p btn-sm">Postuler</button>`,
   `<button class="btn btn-p btn-sm" data-go="offreDetail">Postuler</button>`, 6],
  // reco → détail du parcours
  [`<button class="btn btn-p btn-sm" style="width:max-content">Explorer ce parcours →</button>`,
   `<button class="btn btn-p btn-sm" style="width:max-content" data-go="recoDetail">Explorer ce parcours →</button>`, 1],
  // manager → nouvelle évaluation
  [`<button class="btn btn-p btn-sm">\${ic('check','s')} Soumettre une évaluation</button>`,
   `<button class="btn btn-p btn-sm" data-go="evalNew">\${ic('check','s')} Soumettre une évaluation</button>`, 1],
  // manager → fiche collaborateur (bouton dans un .map, 1 occurrence source)
  [`<button class="btn btn-g btn-sm">Voir les profils</button>`,
   `<button class="btn btn-g btn-sm" data-go="ficheCollab">Voir les profils</button>`, 1],
  // manager → préparer l'entretien
  [`<button class="btn btn-sm" style="background:var(--warning);color:#fff;margin-top:10px">Reprendre les entretiens</button>`,
   `<button class="btn btn-sm" style="background:var(--warning);color:#fff;margin-top:10px" data-go="prepEntretien">Reprendre les entretiens</button>`, 1],
  // manager toolbar → souhaits reçus + publier une offre
  [`<button class="btn btn-g btn-sm">\${ic('send','s')} Communiquer aux RH</button>`,
   `<button class="btn btn-g btn-sm" data-go="souhaitsRecus">\${ic('route','s')} Souhaits reçus</button><button class="btn btn-g btn-sm" data-go="posterOffre">\${ic('brief','s')} Publier une offre</button><button class="btn btn-g btn-sm">\${ic('send','s')} Communiquer aux RH</button>`, 1],
  // rh → cartographie détaillée
  [`<button class="link">Tous les services</button>`,
   `<button class="link" data-go="cartoDetail">Tous les services</button>`, 1],
  // rh → hauts potentiels (consulter)
  [`<div><h4>Hauts potentiels identifiés</h4><p>6 profils Risque aptes au management de transition.</p><button class="link" style="margin-top:6px">Consulter</button></div>`,
   `<div><h4>Hauts potentiels identifiés</h4><p>6 profils Risque aptes au management de transition.</p><button class="link" style="margin-top:6px" data-go="hautsPotentiels">Consulter</button></div>`, 1],
  // rh → hauts potentiels (succession)
  [`<div><h4>Poste critique · succession</h4><p>« Directeur Asset Management » sans successeur désigné.</p><button class="link" style="margin-top:6px">Lancer une analyse</button></div>`,
   `<div><h4>Poste critique · succession</h4><p>« Directeur Asset Management » sans successeur désigné.</p><button class="link" style="margin-top:6px" data-go="hautsPotentiels">Lancer une analyse</button></div>`, 1],
  // rh toolbar → publier un poste + campagne d'évaluation
  [`<span class="eyebrow" style="flex:1">Pilotage des talents · Groupe BMCI</span>`,
   `<span class="eyebrow" style="flex:1">Pilotage des talents · Groupe BMCI</span><button class="btn btn-g btn-sm" data-go="posterPoste">\${ic('brief','s')} Publier un poste</button><button class="btn btn-g btn-sm" data-go="campagneEval">\${ic('check','s')} Campagne d'évaluation</button>`, 1],
  // rh "vue personnelle" → espace RH perso
  [`if(b.dataset.v==='perso')go('collab')`,
   `if(b.dataset.v==='perso')go('rhPerso')`, 1],
  // top bar : cloche → notifications, engrenage → confidentialité (tous les écrans app)
  [`<button class="ib2">\${ic('bell','s')}</button><button class="ib2">\${ic('gear','s')}</button>`,
   `<button class="ib2" data-go="notifications" title="Notifications">\${ic('bell','s')}</button><button class="ib2" data-go="confidentialite" title="Confidentialité">\${ic('gear','s')}</button>`, 1],
];
for (const [search, replace, expected] of WIRES) {
  const count = html.split(search).length - 1;
  if (count !== expected) throw new Error(`Câblage: "${search.slice(0,50)}..." trouvé ${count}× (attendu ${expected})`);
  html = html.split(search).join(replace);
}
console.log(`Câblage OK : ${WIRES.length} liens base→modules posés`);

// 1) inject CSS before </style>
const cssBlock = `\n/* ==== ÉCRANS SUPPLÉMENTAIRES (modules) ==== */\n${allCss.join('\n')}\n${photoCss.join('\n')}\n${polishCss.join('\n')}\n`;
if (html.indexOf('</style>') < 0) throw new Error('</style> introuvable');
html = html.replace('</style>', cssBlock + '</style>');

// 2) inject ORDER.push + module JS right after the ORDER literal, before `let cur=`
const anchor = "'Modules IA']];";
if (html.indexOf(anchor) < 0) throw new Error('fin de ORDER introuvable');
const injectJs = anchor + `\n/* ==== ÉCRANS SUPPLÉMENTAIRES (modules) ==== */\n${orderPush}\n${allJs.join('\n\n')}\n`;
html = html.replace(anchor, injectJs);

// 3) apply avatar → photo wiring on the final html (base + modules)
let avatarCount = 0;
for (const [search, replace, expected] of AVATARS) {
  const count = html.split(search).length - 1;
  if (count !== expected) throw new Error(`Avatar: "${search}" trouvé ${count}× (attendu ${expected})`);
  html = html.split(search).join(replace);
  avatarCount += count;
}
console.log(`Photos OK : ${PHOTO_CLASSES.length} portraits embarqués, ${avatarCount} avatars transformés`);

fs.writeFileSync(OUT, html);
console.log(`\nAssemblé -> ${OUT}`);
console.log(`Écrans ajoutés : ${orderEntries.length}`);
console.log(`Taille : ${(html.length/1024).toFixed(0)} Ko`);
