/*==SCREENS==*/
[["rhPerso","Espace RH — Vue personnelle","RH"],["cartoDetail","Cartographie — Pôle Risques","RH"],["ficheCollabRh","Fiche collaborateur — RH","RH"],["hautsPotentiels","Hauts potentiels & succession","RH"],["posterPoste","Publier un poste","RH"],["campagneEval","Campagne d'évaluation","RH"]]
/*==CSS==*/
.heat.c4{grid-template-columns:150px repeat(4,1fr);min-width:440px}
.succ{display:flex;align-items:center;gap:12px;padding:12px 14px;border:1px solid var(--border);border-radius:12px;background:var(--panel)}
.succ b{font-size:13px;font-weight:700}
.succ small{font-size:11.5px;line-height:1.4;display:block;margin-top:2px}
.evrow{display:flex;align-items:center;gap:16px;padding:14px 0}
.evrow+.evrow{border-top:1px solid var(--border)}
.evrow .bar-wrap{flex:1;min-width:0}
/*==JS==*/
S.rhPerso=()=>`<div class="fade app">${sidebar('rh','Tableau de bord')}<div class="main">${top('Espace RH — Vue personnelle','Votre profil de carrière personnel','rh')}
  <div class="content">
    ${crumb([["Tableau de bord","rh"],["Vue personnelle",null]])}
    <div class="callout"><div class="ci">${ic('user','s')}</div><div style="flex:1"><h4>Vous consultez votre espace personnel</h4><p>Ce profil est le vôtre, en tant que collaboratrice du Groupe. Pour piloter les talents et la cartographie, revenez à votre espace professionnel.</p></div><button class="btn btn-g btn-sm" style="align-self:center" data-go="rh">Basculer en vue professionnelle</button></div>
    <div class="card p"><div class="phead"><div class="ava xl">NA</div>
      <div class="pinfo"><h2>Nadia Alami <span class="badge b-gold">${ic('award','s')} Talent RH 2025</span></h2>
        <div class="role">Responsable Développement RH · Direction des Ressources Humaines</div>
        <div class="pmeta"><span>${ic('pin','s')} Casablanca, Siège</span><span>${ic('mail','s')} nadia.alami@bnpparibas.com</span><span>${ic('cal','s')} Arrivée en 2016</span></div></div>
      <button class="btn btn-g btn-sm">Modifier</button></div></div>
    <div class="cols"><div class="stack">
      <div class="card p"><div class="sec-h"><h3>Mon parcours RH</h3><span class="eyebrow">2016 → aujourd'hui</span></div>
        <div class="parc"><svg viewBox="0 0 700 140" preserveAspectRatio="none" aria-hidden="true">
          <path class="pt" d="M30,116 C170,114 210,92 300,80 C400,66 470,46 670,24"/><path class="pp" id="rhpArc" d="M30,116 C170,114 210,92 300,80 C400,66 470,46 670,24"/>
          <circle class="nd" cx="30" cy="116" r="7"/><circle class="nd" cx="230" cy="89" r="7"/><circle class="nd now" cx="430" cy="62" r="8"/><circle class="nd goal" cx="670" cy="24" r="8"/></svg>
        <div class="pstations"><div class="pstat"><div class="yr">2016 — 2018</div><h4>Chargée RH</h4><p>Recrutement & intégration.</p></div>
          <div class="pstat"><div class="yr">2018 — 2021</div><h4>HR Business Partner</h4><p>Pôle Retail · 320 collaborateurs.</p></div>
          <div class="pstat"><div class="yr">2021 — présent</div><h4>Responsable Dév. RH</h4><p>Talents, mobilité & succession.</p></div>
          <div class="pstat goal"><div class="yr">Objectif</div><h4>Directrice des Talents</h4><p>Station visée · horizon 2027.</p></div></div></div></div>
      <div class="card p"><div class="sec-h"><h3>Mes compétences</h3><button class="tog" aria-checked="true" data-tog><span class="on">Public</span><span class="tk"><span class="kn"></span></span></button></div>
        <div style="display:flex;flex-wrap:wrap;gap:7px"><span class="chip g">Gestion des talents</span><span class="chip g">People analytics</span><span class="chip g">Droit social</span><span class="chip g">Conduite du changement</span><span class="chip g">SIRH · Workday</span><span class="chip g">Mobilité interne</span><span class="chip add">+ Ajouter</span></div></div>
    </div><div class="stack">
      <div class="card p"><div class="sec-h"><h3>Souhaits d'évolution</h3></div><div class="stack" style="gap:9px">
        <div class="wish">${ic('route','s')} Horizon 2 ans — Directrice des Talents</div>
        <div class="wish">${ic('spark','s')} Piloter le programme Leadership Groupe</div>
        <div class="wish">${ic('pin','s')} Mobilité Paris (siège BNP Paribas)</div></div>
        <button class="btn btn-g btn-sm block" id="rhpShare" style="margin-top:12px">Partager à ma hiérarchie</button></div>
      <div class="card p"><div class="sec-h"><h3>Reconnaissance</h3></div><div class="stack" style="gap:11px">
        <div class="ach"><div class="ai">${ic('award','s')}</div><div><h4>Talent RH de l'année 2025</h4><p>Programme de mobilité interne primé au niveau Groupe.</p></div></div>
        <div class="ach"><div class="ai">${ic('team','s')}</div><div><h4>+18 % de mobilités internes</h4><p>Sur le périmètre Siège en 2025.</p></div></div></div></div>
    </div></div>
  </div></div></div>`;
WIRE.rhPerso=function(){if(!reduce)drawPath($('#rhpArc'));const s=$('#rhpShare');if(s)s.addEventListener('click',()=>toast('Souhaits partagés'));};

S.cartoDetail=()=>`<div class="fade app">${sidebar('rh','Cartographie')}<div class="main">${top('Cartographie — Pôle Risques','Cartographie détaillée des compétences','rh')}
  <div class="content">
    ${crumb([["Cartographie","rh"],["Pôle Risques",null]])}
    <div class="toolbar"><div class="seg" id="cartoSeg"><button class="on">Tout le pôle</button><button>Écarts critiques</button><button>Hauts niveaux</button></div><span style="flex:1"></span>
      <button class="btn btn-g btn-sm">${ic('filter','s')} Exporter</button></div>
    <div class="grid3" style="grid-template-columns:repeat(4,1fr)"><div class="kpi"><div class="ki">${ic('team','s')}</div><b class="tnum">6</b><small>Effectif du pôle</small></div>
      <div class="kpi"><div class="ki">${ic('spark','s')}</div><b class="tnum">3,5/5</b><small>Niveau moyen</small><span class="tr">+0,3 / an</span></div>
      <div class="kpi"><div class="ki">${ic('award','s')}</div><b class="tnum">2</b><small>Experts (niveau 5)</small></div>
      <div class="kpi"><div class="ki">${ic('flag','s')}</div><b class="tnum">3</b><small>Écarts à combler</small></div></div>
    <div class="card p"><div class="sec-h"><h3>Niveaux par collaborateur</h3><span class="pill mut">6 collaborateurs</span></div>
      <div class="heatw"><div class="heat c4">
        <div class="hd"></div><div class="hd">Analyse crédit</div><div class="hd">Modélisation</div><div class="hd">Réglementaire</div><div class="hd">Data / Python</div>
        ${[["Aya Bennani","Chargée d'Affaires Senior","AB",[4,4,4,3],"ficheCollabRh"],["Karim Idrissi","Analyste Risque","KI",[3,4,4,4],""],["Sofia Haddad","Modélisatrice Quant","SH",[3,5,3,5],""],["Yassine Berrada","Analyste Crédit","YB",[4,3,4,3],""],["Leïla Fassi","Risk Officer","LF",[4,3,5,3],""],["Omar Tazi","Chargé d'Affaires Junior","OT",[2,2,3,2],""]].map(function(c){var cells=c[3].map(function(v){var l=v<=2?1:v===3?2:v===4?3:4;return `<div class="cell l${l}" title="${c[0]} · ${v}/5">${v}</div>`;}).join('');var name=c[4]?`<button class="link" data-go="${c[4]}">${c[0]}</button>`:`<button class="link cartoName" data-fiche>${c[0]}</button>`;return `<div class="rl" title="${c[1]}"><div class="ava sm" style="margin-right:8px">${c[2]}</div>${name}</div>${cells}`;}).join('')}
      </div></div>
      <div class="hleg"><span><i style="background:var(--heat-1)"></i>Émergent (1–2)</span><span><i style="background:var(--heat-2)"></i>Avancé (3)</span><span><i style="background:var(--heat-3)"></i>Confirmé (4)</span><span><i style="background:var(--heat-4)"></i>Expert (5)</span></div>
      <p class="muted" style="font-size:11px;margin-top:8px">Le niveau est indiqué en chiffre dans chaque case — l'information ne repose pas que sur la couleur (accessibilité WCAG). Cliquez un nom pour ouvrir la fiche.</p></div>
  </div></div></div>`;
WIRE.cartoDetail=function(){const seg=$('#cartoSeg');if(seg)seg.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;seg.querySelectorAll('button').forEach(x=>x.classList.remove('on'));b.classList.add('on');});$$('.cartoName').forEach(b=>b.addEventListener('click',()=>toast('Fiche détaillée en préparation','info')));};

S.ficheCollabRh=()=>`<div class="fade app">${sidebar('rh','Cartographie')}<div class="main">${top('Fiche collaborateur','Aya Bennani · Pôle Risques','rh')}
  <div class="content">
    ${crumb([["Cartographie","rh"],["Pôle Risques","cartoDetail"],["Aya Bennani",null]])}
    <div class="card p"><div class="phead"><div class="ava xl">AB</div>
      <div class="pinfo"><h2>Aya Bennani <span class="badge b-gold">${ic('award','s')} 4,8/5</span></h2>
        <div class="role">Chargée d'Affaires Senior · Pôle Risques</div>
        <div class="pmeta"><span>${ic('pin','s')} Casablanca, Siège</span><span>${ic('mail','s')} aya.bennani@bnpparibas.com</span><span>${ic('cal','s')} 6 ans d'ancienneté</span></div></div>
      <div class="ring"><svg width="76" height="76" viewBox="0 0 76 76"><circle class="rt" cx="38" cy="38" r="32"/><circle class="rp" id="ficheRing" cx="38" cy="38" r="32"/></svg><div class="rc"><div><b class="tnum">88%</b><small>Profil</small></div></div></div></div></div>
    <div class="cols"><div class="stack">
      <div class="card p"><div class="sec-h"><h3>Compétences clés</h3><span class="eyebrow">Évaluation 2025</span></div>
        <div class="bars"><div class="bar-row"><div class="lab"><span>Analyse crédit</span><b>90 %</b></div><div class="bar-tr"><i style="width:90%"></i></div></div>
        <div class="bar-row"><div class="lab"><span>Relation client entreprise</span><b>85 %</b></div><div class="bar-tr"><i style="width:85%"></i></div></div>
        <div class="bar-row"><div class="lab"><span>Négociation</span><b>88 %</b></div><div class="bar-tr"><i style="width:88%"></i></div></div>
        <div class="bar-row"><div class="lab"><span>Réglementaire (Bâle III)</span><b>78 %</b></div><div class="bar-tr"><i style="width:78%"></i></div></div>
        <div class="bar-row"><div class="lab"><span>Data / Python</span><b>62 %</b></div><div class="bar-tr"><i style="width:62%"></i></div></div></div></div>
      <div class="card p"><div class="sec-h"><h3>Historique</h3></div><div class="pstations" style="grid-template-columns:repeat(4,1fr)">
        <div class="pstat"><div class="yr">2019</div><h4>Chargée d'Affaires Junior</h4><p>Arrivée au Pôle Risques.</p></div>
        <div class="pstat"><div class="yr">2021</div><h4>Chargée d'Affaires</h4><p>Portefeuille 40 PME.</p></div>
        <div class="pstat"><div class="yr">2023 — présent</div><h4>Chargée d'Affaires Senior</h4><p>+22 % de PNB sur le segment.</p></div>
        <div class="pstat goal"><div class="yr">2025</div><h4>Meilleure performance</h4><p>Prix commercial régional.</p></div></div></div>
    </div><div class="stack">
      <div class="callout"><div class="ci">${ic('spark','s')}</div><div style="flex:1"><h4>Recommandation IA</h4><p>6 ans d'ancienneté, évaluations excellentes (4,8/5), compétences clés maîtrisées → envisager une promotion ou une revalorisation salariale.</p></div></div>
      <div class="card p"><div class="sec-h"><h3>Évaluations annuelles</h3></div>
        <div class="rev"><div class="ava sm">SK</div><div><p><b>2025 · 4,8/5</b> — « Performance commerciale remarquable, très bonne maîtrise du risque. »</p><div class="who"><span class="stars">★★★★★</span> Sarah K. · Directrice de Pôle</div></div></div>
        <div class="rev"><div class="ava sm">MV</div><div><p><b>2024 · 4,7/5</b> — « Rigueur analytique et sens du client au-dessus de la moyenne. »</p><div class="who"><span class="stars">★★★★★</span> Marc V. · Manager Risques</div></div></div>
        <div class="rev"><div class="ava sm">SK</div><div><p><b>2023 · 4,6/5</b> — « Progression constante, prête à prendre plus de responsabilités. »</p><div class="who"><span class="stars">★★★★★</span> Sarah K. · Directrice de Pôle</div></div></div></div>
      <div class="card p"><div class="sec-h"><h3>Décision RH</h3></div><div class="toolbar">
        <button class="btn btn-p" id="promote">${ic('award','s')} Proposer une promotion</button>
        <button class="btn btn-g" data-go="posterPoste">${ic('brief','s')} Ouvrir un poste adapté</button></div>
        <div class="wnote ok" style="margin-top:12px">${ic('check','s')} Profil éligible à la revue annuelle des talents 2026.</div></div>
    </div></div>
  </div></div></div>`;
WIRE.ficheCollabRh=function(){const r=$('#ficheRing');if(r){const R=32,C=2*Math.PI*R,p=88;r.style.strokeDasharray=C;r.style.strokeDashoffset=reduce?C*(1-p/100):C;if(!reduce)requestAnimationFrame(()=>r.style.strokeDashoffset=C*(1-p/100));}const b=$('#promote');if(b)b.addEventListener('click',()=>toast('Proposition transmise'));};

S.hautsPotentiels=()=>`<div class="fade app">${sidebar('rh','Recommandations')}<div class="main">${top('Hauts potentiels & succession','Vivier de talents & plans de succession','rh')}
  <div class="content">
    ${crumb([["Espace RH","rh"],["Hauts potentiels & succession",null]])}
    <div class="toolbar"><span class="eyebrow" style="flex:1">6 hauts potentiels identifiés · Périmètre Siège</span><button class="btn btn-g btn-sm">${ic('filter','s')} Filtrer</button><button class="btn btn-ai btn-sm">${ic('spark','s')} Recalculer via IA</button></div>
    <div class="ogrid">
      ${[["Aya Bennani","Chargée d'Affaires Senior","Directrice d'Agence",94,"AB"],["Karim Idrissi","Analyste Risque","Manager Risques",89,"KI"],["Sofia Haddad","Modélisatrice Quant","Lead Data Scientist",92,"SH"],["Youssef Amrani","Chef de Projet Digital","Product Owner Senior",86,"YA"],["Leïla Fassi","Risk Officer","Responsable Conformité",83,"LF"],["Mehdi Chraibi","Trésorier Adjoint","Responsable ALM",81,"MC"]].map(function(h){return `<div class="offer"><div style="display:flex;align-items:center;gap:11px"><div class="ava md">${h[4]}</div><div style="flex:1;min-width:0"><h4>${h[0]}</h4><p class="od">${h[1]}</p></div><div class="mini-ring" style="--p:${h[3]}"><i>${h[3]}</i></div></div><div class="om"><span>${ic('route','s')} Cible : <b style="color:var(--green-deep)">${h[2]}</b></span></div><button class="btn btn-g btn-sm" data-go="ficheCollabRh">Voir la fiche</button></div>`;}).join('')}
    </div>
    <div class="card p"><div class="sec-h"><h3>Plan de succession · Directeur Asset Management</h3><span class="pill hot">Poste critique</span></div>
      <div class="callout" style="background:var(--warning-soft);border-color:color-mix(in srgb,var(--warning) 25%,transparent)"><div class="ci" style="background:var(--warning)">${ic('flag','s')}</div><div><h4 style="color:var(--warning)">Poste critique sans successeur désigné</h4><p>Le titulaire actuel prévoit un départ à horizon 18 mois. Trois successeurs potentiels sont en cours de préparation.</p></div></div>
      <div class="stack" style="gap:10px;margin-top:14px">
        ${[["Sofia Haddad","SH","Modélisatrice Quant · Prête sous 6 mois · Formation Leadership finalisée",85,"Prêt","new"],["Karim Idrissi","KI","Analyste Risque · Mentorat en cours sur la gestion d'actifs",60,"À développer","warn"],["Mehdi Chraibi","MC","Trésorier Adjoint · Montée en compétences ALM, horizon 18–24 mois",48,"À développer","warn"]].map(function(s){return `<div class="succ"><div class="ava md">${s[1]}</div><div style="flex:1;min-width:0"><div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap"><b>${s[0]}</b><span class="pill ${s[5]}">${s[4]}</span></div><small class="muted">${s[2]}</small><div class="bar-tr" style="margin-top:8px"><i style="width:${s[3]}%"></i></div></div></div>`;}).join('')}
      </div></div>
  </div></div></div>`;

S.posterPoste=()=>`<div class="fade app">${sidebar('rh','Offres internes')}<div class="main">${top('Publier un poste','Nouvelle offre interne','rh')}
  <div class="content">
    ${crumb([["Offres internes","offres"],["Publier un poste",null]])}
    <div class="card p" style="max-width:760px">
      <div class="formrow"><label>Type d'offre</label><div class="seg" id="typeSeg"><button class="on">Poste</button><button>Mission transverse</button><button>Projet</button><button>Gig ponctuel</button></div></div>
      <div class="formrow"><label>Titre du poste</label><input class="ctrl" placeholder="Ex : Analyste Crédit Senior — Corporate Banking"></div>
      <div class="formrow"><label>Description</label><textarea class="ta" placeholder="Missions, responsabilités, profil recherché, compétences attendues…"></textarea></div>
      <div class="cols" style="grid-template-columns:1fr 1fr">
        <div class="formrow"><label>Entité</label><select class="ctrl"><option>Corporate &amp; Investment Banking</option><option>Banque de Détail</option><option>Risques</option><option>IT &amp; Digital</option><option>Finance &amp; ALM</option><option>Ressources Humaines</option></select></div>
        <div class="formrow"><label>Localisation</label><input class="ctrl" placeholder="Ex : Casablanca, Siège"></div>
      </div>
      <div class="formrow"><label>Fourchette salariale (MAD brut / an)</label><input class="ctrl" placeholder="Ex : 480 000 — 600 000"></div>
      <div class="wnote" id="posteNote">${ic('lock','s')} Pour un poste, le manager direct du candidat n'est PAS informé de sa candidature.</div>
      <div class="toolbar" style="margin-top:18px"><button class="btn btn-p" id="publishPoste">${ic('send','s')} Publier le poste</button><button class="btn btn-g" data-go="offres">Annuler</button></div>
    </div>
  </div></div></div>`;
WIRE.posterPoste=function(){const seg=$('#typeSeg'),note=$('#posteNote');if(seg)seg.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;seg.querySelectorAll('button').forEach(x=>x.classList.remove('on'));b.classList.add('on');if(note){const poste=b.textContent.trim()==='Poste';note.innerHTML=poste?ic('lock','s')+" Pour un poste, le manager direct du candidat n'est PAS informé de sa candidature.":ic('bell','s')+" Pour une mission ou un projet, le manager direct du candidat sera informé de sa candidature.";}});const p=$('#publishPoste');if(p)p.addEventListener('click',()=>{toast('Poste publié');go('offres');});};

S.campagneEval=()=>`<div class="fade app">${sidebar('rh','Tableau de bord')}<div class="main">${top("Campagne d'évaluation","Suivi trimestriel des entretiens","rh")}
  <div class="content">
    ${crumb([["Tableau de bord","rh"],["Campagne d'évaluation",null]])}
    <div class="toolbar"><span class="eyebrow" style="flex:1">Campagne T3 2026 · clôture le 30 septembre</span><button class="btn btn-g btn-sm">${ic('cal','s')} Prolonger la campagne</button></div>
    <div class="grid3"><div class="kpi"><div class="ki">${ic('spark','s')}</div><b class="tnum">72 %</b><small>Avancement global</small><span class="tr">+9 pts / semaine</span></div>
      <div class="kpi"><div class="ki">${ic('check','s')}</div><b class="tnum">142/210</b><small>Entretiens réalisés</small></div>
      <div class="kpi"><div class="ki">${ic('flag','s')}</div><b class="tnum">2</b><small>Équipes en retard</small></div></div>
    <div class="card p"><div class="sec-h"><h3>Avancement par équipe</h3><span class="pill mut">5 équipes</span></div>
      ${[["Finance & ALM",90,"18/20"],["Pôle Risques",82,"28/34"],["Banque de Détail",74,"46/62"],["Corporate Banking",61,"31/51"],["IT & Digital",55,"19/34"]].map(function(t){return `<div class="evrow"><div class="bar-wrap"><div class="bar-row"><div class="lab"><span>${t[0]} <small class="muted">· ${t[2]} entretiens</small></span><b>${t[1]} %</b></div><div class="bar-tr"><i style="width:${t[1]}%"></i></div></div></div><button class="btn btn-g btn-sm relaunch">${ic('send','s')} Relancer</button></div>`;}).join('')}
    </div>
    <div class="callout"><div class="ci">${ic('spark','s')}</div><div style="flex:1"><h4>Conseil du Coach IA</h4><p>Les équipes <b>Corporate Banking</b> et <b>IT & Digital</b> sont en retard. Une relance ciblée des managers avant le 15 septembre permettrait d'atteindre 90 % de couverture à la clôture.</p></div></div>
  </div></div></div>`;
WIRE.campagneEval=function(){$$('.relaunch').forEach(b=>b.addEventListener('click',()=>toast('Relance envoyée')));};
