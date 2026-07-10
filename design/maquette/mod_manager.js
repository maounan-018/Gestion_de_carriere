/*==SCREENS==*/
[["ficheCollab","Fiche collaborateur","Manager"],["evalNew","Nouvelle évaluation","Manager"],["posterOffre","Publier une offre","Manager"],["souhaitsRecus","Souhaits d'évolution reçus","Manager"],["prepEntretien","Préparer l'entretien annuel","Manager"],["pousserCours","Pousser un cours","Manager"]]
/*==CSS==*/
/* Aucun style additionnel : réutilise intégralement le design system existant. */
/*==JS==*/
S.ficheCollab=()=>`<div class="fade app">${sidebar('manager','Mon équipe')}<div class="main">${top('Fiche collaborateur','Profil détaillé d\'un membre de votre équipe','manager')}
  <div class="content">
    ${crumb([['Mon équipe','manager'],['Alice Martin',null]])}
    <div class="card p"><div class="phead">
      <div class="ava xl">AM</div>
      <div class="pinfo"><h2>Alice Martin <span class="badge b-gold">${ic('award','s')} Top potentiel</span></h2>
        <div class="role">Analyste Senior · Direction de Pôle Risques</div>
        <div class="pmeta"><span>${ic('pin','s')} Casablanca, Siège</span><span>${ic('mail','s')} alice.martin@bnpparibas.com</span><span>${ic('cal','s')} Dans l'équipe depuis 2019 · 5 ans</span></div></div>
      <div class="mini-ring" style="--p:88"><i>88</i></div>
    </div>
      <div class="toolbar" style="margin-top:16px">
        <button class="btn btn-p btn-sm" data-go="evalNew">${ic('check','s')} Évaluer</button>
        <button class="btn btn-g btn-sm" data-go="prepEntretien">${ic('chat','s')} Préparer l'entretien</button>
        <button class="btn btn-g btn-sm" data-go="pousserCours">${ic('book','s')} Pousser un cours</button>
      </div>
    </div>
    <div class="cols"><div class="stack">
      <div class="card p"><div class="sec-h"><h3>Compétences clés</h3><span class="eyebrow">Évaluées T2 2026</span></div>
        <div class="bars">
          <div class="bar-row"><div class="lab"><span>Analyse financière</span><b>92 %</b></div><div class="bar-tr"><i style="width:92%"></i></div></div>
          <div class="bar-row"><div class="lab"><span>Modélisation du risque (IFRS9)</span><b>84 %</b></div><div class="bar-tr"><i style="width:84%"></i></div></div>
          <div class="bar-row"><div class="lab"><span>Python · SQL</span><b>78 %</b></div><div class="bar-tr"><i style="width:78%"></i></div></div>
          <div class="bar-row"><div class="lab"><span>Communication client</span><b>65 %</b></div><div class="bar-tr"><i style="width:65%"></i></div></div>
        </div></div>
      <div class="card p"><div class="sec-h"><h3>Évaluations reçues</h3><span class="pill mut">2 avis</span></div>
        <div class="rev"><div class="ava sm">JM</div><div><p>« Analyste rigoureuse, livrables toujours fiables. A pris en main le scoring corporate avec une réelle autonomie. »</p><div class="who"><span class="stars">★★★★★</span> Jean-Marc Dupont · Directeur de Pôle · Mars 2026</div></div></div>
        <div class="rev"><div class="ava sm">SL</div><div><p>« Excellente coéquipière sur le projet Bâle IV, sait vulgariser des sujets techniques complexes. »</p><div class="who"><span class="stars">★★★★☆</span> Sophie Lefebvre · Chef de projet · Janv. 2026</div></div></div>
      </div>
    </div><div class="stack">
      <div class="card p"><div class="sec-h"><h3>Historique de poste</h3></div>
        <div class="pstations" style="grid-template-columns:1fr">
          <div class="pstat"><div class="yr">2019 — 2021</div><h4>Analyste Risque Junior</h4><p>Intégration via le Graduate Program, portefeuille PME.</p></div>
          <div class="pstat"><div class="yr">2021 — 2023</div><h4>Analyste Risque Confirmé</h4><p>Scoring crédit, entreprises intermédiaires.</p></div>
          <div class="pstat"><div class="yr">2023 — présent</div><h4>Analyste Senior</h4><p>Référente IFRS9, encadrement de 2 juniors.</p></div>
        </div></div>
      <div class="callout"><div class="ci">${ic('spark','s')}</div><div><h4>Lecture Coach IA</h4><p>Profil orienté <b>expertise</b> et mûr pour un rôle de <b>Lead Analyst</b>. Un module « Management d'équipe » consoliderait la trajectoire managériale.</p></div></div>
    </div></div>
  </div></div></div>`;

S.evalNew=()=>`<div class="fade app">${sidebar('manager','Mon équipe')}<div class="main">${top('Nouvelle évaluation','Évaluation de performance · cycle 2026','manager')}
  <div class="content">
    ${crumb([['Mon équipe','manager'],['Alice Martin','ficheCollab'],['Évaluation',null]])}
    <div class="cols"><div class="stack">
      <div class="card p"><div class="sec-h"><h3>Collaborateur évalué</h3></div>
        <div class="phead" style="align-items:center"><div class="ava md">AM</div><div class="pinfo"><h2 style="font-size:17px">Alice Martin</h2><div class="role">Analyste Senior · Pôle Risques</div></div><span class="pill ai">${ic('spark','s')} Cycle T2 2026</span></div>
      </div>
      <div class="card p"><div class="sec-h"><h3>Évaluation des compétences</h3><span class="eyebrow">Notez de 1 à 5</span></div>
        <div class="stack" style="gap:14px">
          ${[['Analyse financière',5],['Modélisation du risque',4],['Python · SQL',4],['Communication & collaboration',3]].map(c=>`<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap"><span style="font-size:13.5px;font-weight:600">${c[0]}</span><div class="rating">${[1,2,3,4,5].map(n=>`<button type="button" class="${n<=c[1]?'on':''}">★</button>`).join('')}</div></div>`).join('')}
        </div></div>
      <div class="card p"><div class="formrow"><label>Points forts</label><textarea class="ta" placeholder="Ce qui a particulièrement bien fonctionné cette année…">Excellente maîtrise du scoring IFRS9 et grande autonomie sur les dossiers corporate. Fiabilité des livrables saluée par les métiers.</textarea></div>
        <div class="formrow"><label>Axes de progrès</label><textarea class="ta" placeholder="Pistes de développement pour l'année à venir…">Développer la posture managériale et l'aisance de communication en comité de direction.</textarea></div>
      </div>
    </div><div class="stack">
      <div class="card p"><div class="sec-h"><h3>Destinataire</h3></div>
        <div class="seg" id="evalDest"><button class="on">Collaborateur</button><button>RH</button><button>Les deux</button></div>
        <p class="muted" style="font-size:12px;margin-top:10px">Le collaborateur reçoit une notification. Les RH n'ont accès qu'aux évaluations explicitement partagées.</p>
        <div class="divider" style="margin:14px 0"></div>
        <button class="btn btn-p block" id="submitEval">${ic('check','s')} Soumettre l'évaluation</button>
        <button class="btn btn-g block" style="margin-top:9px" data-go="ficheCollab">Annuler</button>
      </div>
      <div class="callout"><div class="ci">${ic('shield','s')}</div><div><h4>Confidentialité</h4><p>L'évaluation est horodatée et archivée. Le collaborateur pourra y répondre lors de l'entretien annuel.</p></div></div>
    </div></div>
  </div></div></div>`;

S.posterOffre=()=>`<div class="fade app">${sidebar('manager','Offres internes')}<div class="main">${top('Publier une offre','Diffusez un poste, une mission ou un projet','manager')}
  <div class="content">
    ${crumb([['Offres internes','offres'],['Publier',null]])}
    <div class="cols"><div class="stack">
      <div class="card p"><div class="sec-h"><h3>Type d'opportunité</h3></div>
        <div class="seg" id="offerType"><button class="on" data-t="Poste">Poste</button><button data-t="Mission">Mission</button><button data-t="Projet">Projet</button><button data-t="Gig">Gig</button></div>
        <div class="wnote" id="offerNote" style="display:none;margin-top:14px">${ic('bell','s')} Pour une mission / projet, le manager du candidat sera automatiquement informé.</div>
      </div>
      <div class="card p">
        <div class="formrow"><label>Titre de l'offre</label><input class="ctrl" placeholder="Ex : Analyste Crédit Senior — Corporate Banking" value="Analyste Crédit Senior — Corporate Banking"></div>
        <div class="formrow"><label>Description</label><textarea class="ta" placeholder="Missions, contexte, compétences attendues…">Analyse des dossiers de crédit sur le segment Grandes Entreprises, en appui de l'équipe Risques du Siège. Interaction directe avec les chargés d'affaires.</textarea></div>
        <div class="formrow"><label>Entité</label><select class="ctrl"><option>Risques &amp; Conformité</option><option>Corporate &amp; Investment Banking</option><option>Banque de Détail</option><option>IT &amp; Digital</option><option>Finance</option><option>Ressources Humaines</option></select></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="formrow"><label>Localisation</label><input class="ctrl" placeholder="Ville / mode" value="Casablanca, Siège"></div>
          <div class="formrow"><label>Durée</label><input class="ctrl" placeholder="Ex : CDI, 6 mois, 3 jours" value="CDI"></div>
        </div>
      </div>
    </div><div class="stack">
      <div class="card p"><div class="sec-h"><h3>Publication</h3></div>
        <p class="muted" style="font-size:12.5px">L'offre sera visible dans <b>Offres internes</b> pour tous les collaborateurs éligibles du Groupe.</p>
        <div class="divider" style="margin:14px 0"></div>
        <button class="btn btn-p block" id="publishOffer">${ic('send','s')} Publier l'offre</button>
        <button class="btn btn-g block" style="margin-top:9px" data-go="offres">Aperçu des offres</button>
      </div>
      <div class="card p"><div class="sec-h"><h3>Bonnes pratiques</h3></div><div class="stack" style="gap:10px">
        <div class="rec ai"><div class="ri">${ic('spark','s')}</div><div><h4>Soyez précis sur l'impact</h4><p>Les offres décrivant un résultat attendu reçoivent 2× plus de candidatures.</p></div></div>
        <div class="rec ai"><div class="ri">${ic('team','s')}</div><div><h4>Ouvrez aux profils atypiques</h4><p>Mentionnez les compétences transférables acceptées.</p></div></div>
      </div></div>
    </div></div>
  </div></div></div>`;

S.souhaitsRecus=()=>`<div class="fade app">${sidebar('manager','Mon équipe')}<div class="main">${top('Souhaits d\'évolution reçus','Les aspirations poussées par votre équipe','manager')}
  <div class="content">
    ${crumb([['Mon équipe','manager'],['Souhaits d\'évolution',null]])}
    <div class="toolbar"><span class="eyebrow" style="flex:1">3 souhaits en attente de votre retour</span><span class="pill new">${ic('route','s')} À traiter</span></div>
    <div class="stack">
      ${[
        ['AM','Alice Martin','Analyste Senior','Évoluer vers un poste de Manager d\'équipe Risques à horizon 12 mois.','Poussé le 3 juillet 2026'],
        ['MV','Marc Vasseur','Chargé Entreprises','Rejoindre une mission transverse sur la transformation digitale des agences.','Poussé le 28 juin 2026'],
        ['TL','Thomas Leroy','Auditeur Junior','Mobilité internationale — bureau de Paris ou Londres sur 2 ans.','Poussé le 21 juin 2026']
      ].map(w=>`<div class="card p"><div style="display:flex;gap:14px;align-items:flex-start">
        <div class="ava md">${w[0]}</div>
        <div style="flex:1;min-width:0"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><b style="font-size:14.5px">${w[1]}</b><span class="chip">${w[2]}</span><span class="muted" style="font-size:11.5px;margin-left:auto">${w[4]}</span></div>
          <p style="font-size:13.5px;color:var(--ink-2);line-height:1.5;margin-top:8px">${ic('route','s')} ${w[3]}</p>
          <div class="toolbar" style="margin-top:12px"><button class="btn btn-p btn-sm" data-transmit>${ic('send','s')} Appuyer &amp; transmettre aux RH</button><button class="btn btn-g btn-sm" data-discuss>${ic('chat','s')} Discuter</button></div>
        </div></div></div>`).join('')}
    </div>
  </div></div></div>`;

S.prepEntretien=()=>`<div class="fade app">${sidebar('manager','Entretiens')}<div class="main">${top('Préparer l\'entretien annuel','Briefing contextualisé avant l\'échange','manager')}
  <div class="content">
    ${crumb([['Entretiens','entretien'],['Préparation',null]])}
    <div class="card p"><div class="sec-h"><h3>Collaborateur</h3><span class="pill mut">Campagne 2026</span></div>
      <div class="seg" id="prepWho"><button class="on" data-name="Alice Martin">Alice Martin</button><button data-name="Marc Vasseur">Marc Vasseur</button><button data-name="Sophie Lefebvre">Sophie Lefebvre</button><button data-name="Thomas Leroy">Thomas Leroy</button></div>
    </div>
    <div class="cols"><div class="stack">
      <div class="card p"><div class="phead" style="align-items:center"><div class="ava xl" id="briefAva">AM</div>
        <div class="pinfo"><h2 style="font-size:19px" id="briefName">Alice Martin</h2><div class="role">Analyste Senior · Pôle Risques · 5 ans d'ancienneté</div>
          <div class="pmeta"><span>${ic('spark','s')} Profil complété à 88 %</span><span>${ic('award','s')} Top potentiel</span></div></div></div>
      </div>
      <div class="card p"><div class="sec-h"><h3>Missions récentes</h3></div><div class="grid3" style="grid-template-columns:1fr 1fr">
        <div class="ach"><div class="ai">${ic('bolt','s')}</div><div><h4>Refonte du scoring IFRS9</h4><p>Livré · −12 % de provisions.</p></div></div>
        <div class="ach"><div class="ai">${ic('team','s')}</div><div><h4>Encadrement 2 juniors</h4><p>Onboarding réussi sur Python.</p></div></div>
        <div class="ach"><div class="ai">${ic('shield','s')}</div><div><h4>Projet Bâle IV</h4><p>Volet modélisation, en cours.</p></div></div>
        <div class="ach"><div class="ai">${ic('book','s')}</div><div><h4>Certif. Risk Analytics</h4><p>Obtenue en mai 2026.</p></div></div>
      </div></div>
    </div><div class="stack">
      <div class="card p"><div class="sec-h"><h3>Dernières évaluations</h3></div>
        <div class="rev"><div class="ava sm">JM</div><div><p>« Analyste rigoureuse, autonome sur le corporate. »</p><div class="who"><span class="stars">★★★★★</span> Vous · Mars 2026</div></div></div>
        <div class="rev"><div class="ava sm">SL</div><div><p>« Sait vulgariser les sujets techniques. »</p><div class="who"><span class="stars">★★★★☆</span> Sophie L. · Janv. 2026</div></div></div>
      </div>
      <div class="callout"><div class="ci">${ic('spark','s')}</div><div><h4>Points à aborder — Coach IA</h4><p>Aspiration <b>managériale</b> exprimée. Cadrer un plan de montée en compétences <i>leadership</i> et évoquer la mission transverse « Digital ».</p></div></div>
      <button class="btn btn-p block" data-go="entretien">${ic('spark','s')} Lancer la simulation contextualisée</button>
    </div></div>
  </div></div></div>`;

S.pousserCours=()=>`<div class="fade app">${sidebar('manager','Mon équipe')}<div class="main">${top('Pousser un cours','Assignez une formation ciblée à un membre','manager')}
  <div class="content">
    ${crumb([['Mon équipe','manager'],['Pousser un cours',null]])}
    <div class="card p"><div class="sec-h"><h3>Destinataire</h3></div>
      <div class="seg" id="courseMember"><button class="on" data-name="Alice Martin">Alice Martin</button><button data-name="Marc Vasseur">Marc Vasseur</button><button data-name="Sophie Lefebvre">Sophie Lefebvre</button><button data-name="Thomas Leroy">Thomas Leroy</button></div>
    </div>
    <div class="card p"><div class="sec-h"><h3>Catalogue recommandé</h3><span class="pill ai">${ic('spark','s')} Suggéré par l'IA</span></div>
      <div class="ogrid">
        ${[
          ['Leadership Excellence @BNP','Management','Certifiant · 6 modules','Renforce la posture managériale et la conduite d\'équipe.'],
          ['Modélisation avancée du risque','Risques','Expert · 8 h','Approfondit IFRS9 et le stress-testing Bâle IV.'],
          ['Python pour la data financière','Data','Intermédiaire · 12 h','Automatisation des analyses et du reporting réglementaire.'],
          ['Communication d\'impact','Soft skills','Atelier · 3 h','Prise de parole et synthèse en comité.']
        ].map(c=>`<div class="offer"><span class="pill mut" style="width:max-content">${c[1]}</span><h4>${c[0]}</h4><p class="od">${c[3]}</p><div class="om"><span>${ic('book','s')} ${c[2]}</span></div><button class="btn btn-p btn-sm" data-assign>${ic('send','s')} Assigner</button></div>`).join('')}
      </div>
    </div>
  </div></div></div>`;

WIRE.evalNew=function(){
  $$('.rating').forEach(function(rt){
    var bs=$$('button',rt);
    bs.forEach(function(b,i){b.addEventListener('click',function(){bs.forEach(function(x,j){x.classList.toggle('on',j<=i);});});});
  });
  var dest=$('#evalDest');
  if(dest){dest.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;dest.querySelectorAll('button').forEach(function(x){x.classList.remove('on');});b.classList.add('on');});}
  var s=$('#submitEval');
  if(s){s.addEventListener('click',function(){toast('Évaluation transmise');go('manager');});}
};

WIRE.posterOffre=function(){
  var t=$('#offerType'),note=$('#offerNote');
  if(t){t.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;t.querySelectorAll('button').forEach(function(x){x.classList.remove('on');});b.classList.add('on');if(note)note.style.display=(b.dataset.t==='Poste')?'none':'flex';});}
  var p=$('#publishOffer');
  if(p){p.addEventListener('click',function(){toast('Offre publiée');go('offres');});}
};

WIRE.souhaitsRecus=function(){
  $$('[data-transmit]').forEach(function(b){b.addEventListener('click',function(){toast('Souhait transmis aux RH');b.disabled=true;b.innerHTML=ic('check','s')+' Transmis';});});
  $$('[data-discuss]').forEach(function(b){b.addEventListener('click',function(){toast('Invitation à discuter envoyée','info');});});
};

WIRE.prepEntretien=function(){
  var seg=$('#prepWho'),nm=$('#briefName'),av=$('#briefAva');
  if(seg){seg.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;seg.querySelectorAll('button').forEach(function(x){x.classList.remove('on');});b.classList.add('on');
    if(nm)nm.textContent=b.dataset.name;
    if(av)av.textContent=b.dataset.name.split(' ').map(function(w){return w.charAt(0);}).join('');});}
};

WIRE.pousserCours=function(){
  var seg=$('#courseMember'),cur={n:'Alice Martin'};
  if(seg){seg.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;seg.querySelectorAll('button').forEach(function(x){x.classList.remove('on');});b.classList.add('on');cur.n=b.dataset.name;});}
  $$('[data-assign]').forEach(function(b){b.addEventListener('click',function(){toast('Cours assigné à '+cur.n);});});
};
