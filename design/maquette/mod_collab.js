/*==SCREENS==*/
[["editProfil","Éditer mon profil","Collaborateur"],["recoDetail","Parcours : Manager de Pôle","Collaborateur"],["formation","Formations","Collaborateur"],["offreDetail","Détail de l'offre","Collaborateur"],["mesCandidatures","Mes candidatures","Collaborateur"],["souhaitSuivi","Mes souhaits d'évolution","Collaborateur"]]
/*==CSS==*/
/* Réglages de visibilité (editProfil) */
.vrow{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 0;border-top:1px solid var(--border)}
.vrow:first-of-type{border-top:0}
.vrow small{display:block;margin-top:2px}
/* Modale de candidature (offreDetail) */
.mfoot{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}
.chk{display:flex;align-items:flex-start;gap:10px;font-size:13px;color:var(--ink-2);cursor:pointer;padding:6px 0 12px;line-height:1.45}
.chk input{width:18px;height:18px;accent-color:var(--green);margin-top:1px;flex:none}
.rcap{display:flex;flex-direction:column;margin-bottom:2px}
.rrow{display:flex;justify-content:space-between;gap:16px;padding:10px 0;border-top:1px solid var(--border);font-size:13px}
.rrow:first-child{border-top:0}
/* Liste des candidatures (mesCandidatures) */
.clist{display:flex;flex-direction:column}
.crow{display:flex;align-items:center;gap:13px;padding:14px 2px;border-top:1px solid var(--border)}
.crow:first-child{border-top:0}
.crow .ci2{width:38px;height:38px;border-radius:11px;background:var(--green-soft);color:var(--green-deep);display:grid;place-items:center;flex:none}
.crow .cmain{flex:1;min-width:0}
.crow .cmain h4{font-size:14px;font-weight:700;line-height:1.25}
.crow .cmeta{display:flex;flex-wrap:wrap;gap:5px 14px;margin-top:4px;font-size:11.5px;color:var(--ink-3)}
.crow .cmeta span{display:inline-flex;align-items:center;gap:5px}
/*==JS==*/
S.editProfil=()=>`<div class="fade app">${sidebar('collab','Mon profil')}<div class="main">${top('Éditer mon profil','Votre profil de carrière','collab')}
  <div class="content">
    ${crumb([['Mon profil','collab'],['Éditer',null]])}
    <div class="cols">
      <div class="card p">
        <div class="sec-h"><h3>Informations générales</h3></div>
        <div class="phead" style="margin-bottom:20px">
          <div class="ava xl">JM</div>
          <div class="pinfo">
            <button class="btn btn-g btn-sm" id="changePhoto">${ic('user','s')} Changer la photo</button>
            <p class="muted" style="font-size:11.5px;margin-top:9px">JPG ou PNG · 2 Mo maximum · visible selon vos réglages de confidentialité.</p>
          </div>
        </div>
        <div class="formrow"><label>Nom d'affichage</label><input class="ctrl" value="Jean-Marc Dupont" placeholder="Prénom Nom"></div>
        <div class="formrow"><label>Description</label><textarea class="ta" placeholder="Décrivez votre parcours en quelques lignes…">Analyste Risque Senior à la Direction de l'Audit. Spécialiste du scoring IFRS 9 et de l'automatisation du reporting réglementaire. J'accompagne les juniors sur Python et l'analyse de données.</textarea></div>
        <button class="btn btn-p" id="saveProfil" style="margin-top:4px">${ic('check','s')} Enregistrer</button>
      </div>
      <div class="stack">
        <div class="card p">
          <div class="sec-h"><h3>Visibilité</h3></div>
          <p class="muted" style="font-size:12px;margin-bottom:6px">Choisissez ce que les autres collaborateurs du Groupe peuvent consulter sur votre profil.</p>
          <div class="vrow"><div><b style="font-size:13px">Profil</b><small class="muted">Poste, description et parcours</small></div><button class="tog" aria-checked="true" data-tog><span class="on">Public</span><span class="tk"><span class="kn"></span></span></button></div>
          <div class="vrow"><div><b style="font-size:13px">Compétences</b><small class="muted">Niveaux et certifications</small></div><button class="tog" aria-checked="true" data-tog><span class="on">Public</span><span class="tk"><span class="kn"></span></span></button></div>
          <div class="vrow"><div><b style="font-size:13px">Avis des pairs</b><small class="muted">Retours de vos collègues</small></div><button class="tog" aria-checked="false" data-tog><span class="on">Privé</span><span class="tk"><span class="kn"></span></span></button></div>
        </div>
        <div class="callout"><div class="ci">${ic('shield','s')}</div><div><h4>Données protégées</h4><p>Vos réglages s'appliquent immédiatement. Les RH conservent une vue conforme à la politique de mobilité du Groupe.</p></div></div>
      </div>
    </div>
  </div>
</div></div>`;
WIRE.editProfil=function(){
  const p=$('#changePhoto'); if(p) p.addEventListener('click',()=>toast('Ouvrez votre galerie pour changer la photo','info'));
  const save=$('#saveProfil'); if(save) save.addEventListener('click',()=>{ toast('Profil mis à jour'); go('collab'); });
};

S.recoDetail=()=>`<div class="fade app">${sidebar('collab','Recommandations')}<div class="main">${top('Parcours : Manager de Pôle','Direction de la Clientèle Entreprise · 92 % de match','collab')}
  <div class="content">
    ${crumb([['Recommandations','reco'],['Manager de Pôle',null]])}
    <div class="match">
      <div class="mt">
        <div><span class="pill new">Recommandation prioritaire</span><h4 style="margin-top:8px;font-size:20px">Manager de Pôle</h4><p class="muted" style="font-size:12.5px">Direction de la Clientèle Entreprise · Casablanca, Siège</p></div>
        <div class="pct"><b>92 %</b><small>Match</small></div>
      </div>
      <p style="font-size:13.5px;color:var(--ink-2);line-height:1.55">Pilotage d'un pôle de 8 à 12 collaborateurs sur le segment Entreprises : cadrage des objectifs commerciaux, développement des talents et arbitrage des dossiers de crédit. Un poste d'encadrement aligné sur votre trajectoire d'Analyste Risque Senior.</p>
      <div class="divider"></div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div>
          <div class="eyebrow" style="margin-bottom:8px">Compétences acquises</div>
          <div style="display:flex;flex-wrap:wrap;gap:6px"><span class="chip g">${ic('check','s')} Analyse financière</span><span class="chip g">${ic('check','s')} Gestion de projet</span><span class="chip g">${ic('check','s')} Leadership d'équipe</span><span class="chip g">${ic('check','s')} Vision client</span></div>
        </div>
        <div>
          <div class="eyebrow" style="margin-bottom:8px">À développer</div>
          <div style="display:flex;flex-wrap:wrap;gap:6px"><span class="chip gap">Stratégie Groupe BNP Paribas</span><span class="chip gap">Management RH</span><span class="chip gap">Pilotage budgétaire</span></div>
        </div>
      </div>
    </div>

    <div class="card p">
      <div class="sec-h"><h3>Formations recommandées</h3><span class="pill ai">${ic('spark','s')} Sélection IA</span></div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px">
        <div class="offer">
          <span class="pill ai" style="width:max-content">Certifiante</span>
          <h4>Leadership Excellence @BNP</h4>
          <p class="od">Posture managériale, délégation et conduite du changement.</p>
          <div class="om"><span>${ic('clock','s')} 24 h</span><span>${ic('award','s')} Avancé</span></div>
          <button class="btn btn-p btn-sm" data-launch>${ic('bolt','s')} Lancer</button>
        </div>
        <div class="offer">
          <span class="pill new" style="width:max-content">Populaire</span>
          <h4>Management d'équipe & feedback</h4>
          <p class="od">Conduire des entretiens et animer un collectif au quotidien.</p>
          <div class="om"><span>${ic('clock','s')} 12 h</span><span>${ic('award','s')} Intermédiaire</span></div>
          <button class="btn btn-p btn-sm" data-launch>${ic('bolt','s')} Lancer</button>
        </div>
        <div class="offer">
          <span class="pill mut" style="width:max-content">Sur inscription</span>
          <h4>Finance stratégique pour managers</h4>
          <p class="od">Pilotage budgétaire et arbitrages financiers d'un centre de profit.</p>
          <div class="om"><span>${ic('clock','s')} 18 h</span><span>${ic('award','s')} Avancé</span></div>
          <button class="btn btn-p btn-sm" data-launch>${ic('bolt','s')} Lancer</button>
        </div>
      </div>
    </div>

    <div class="card p">
      <div class="sec-h"><h3>Vos jalons vers ce poste</h3><span class="eyebrow">1 / 4 complété</span></div>
      <div class="jalons">
        <div class="jalon done"><div class="jn">${ic('check','s')}</div><h5>Auto-évaluation</h5><small>Complété</small></div>
        <div class="jalon active"><div class="jn">2</div><h5>Entretien manager</h5><small>À planifier</small></div>
        <div class="jalon"><div class="jn">3</div><h5>Formation Leadership L1</h5><small>Certifiante</small></div>
        <div class="jalon"><div class="jn">4</div><h5>Postulation interne</h5><small>Offres ciblées</small></div>
      </div>
    </div>

    <div class="callout"><div class="ci">${ic('spark','s')}</div><div style="flex:1"><h4>Le conseil de votre Coach IA</h4><p>« En finalisant <i>Leadership Excellence</i> puis une mission transverse, votre compatibilité passerait de 92 % à 96 %. »</p></div><button class="btn btn-ai btn-sm" style="align-self:center" data-go="entretien">Discuter avec le Coach</button></div>

    <div class="toolbar"><button class="btn btn-p" data-go="offres">${ic('brief','s')} Voir les offres liées</button><button class="btn btn-g" data-go="reco">← Retour aux recommandations</button></div>
  </div>
</div></div>`;
WIRE.recoDetail=function(){
  $$('[data-launch]').forEach(function(b){ b.addEventListener('click',function(){ toast('Formation ajoutée à votre suivi'); go('formation'); }); });
};

S.formation=()=>`<div class="fade app">${sidebar('collab','Formations')}<div class="main">${top('Formations','Développez les compétences de votre prochaine station','collab')}
  <div class="content">
    <div class="card p">
      <div class="sec-h"><h3>Mon suivi</h3><span class="pill ai">${ic('spark','s')} 2 en cours</span></div>
      <div class="stack" style="gap:18px">
        <div>
          <div class="bar-row"><div class="lab"><span>Leadership Excellence @BNP · Module 3 / 5</span><b>62 %</b></div><div class="bar-tr"><i style="width:62%"></i></div></div>
          <div style="display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:8px;font-size:11.5px;color:var(--ink-3)"><span>${ic('clock','s')} 24 h · 9 h restantes</span><span>${ic('cal','s')} Échéance 15 octobre 2026</span><span>${ic('award','s')} Certifiante</span></div>
        </div>
        <div>
          <div class="bar-row"><div class="lab"><span>Python pour l'analyse de risque · Module 2 / 4</span><b>40 %</b></div><div class="bar-tr"><i style="width:40%"></i></div></div>
          <div style="display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:8px;font-size:11.5px;color:var(--ink-3)"><span>${ic('clock','s')} 16 h · 10 h restantes</span><span>${ic('cal','s')} Échéance 28 novembre 2026</span><span>${ic('book','s')} E-learning</span></div>
        </div>
      </div>
    </div>

    <div class="toolbar"><span class="eyebrow" style="flex:1">Catalogue · 4 formations recommandées pour vous</span><button class="btn btn-g btn-sm">${ic('filter','s')} Filtrer</button></div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:14px">
      <div class="card p" style="display:flex;flex-direction:column;gap:8px">
        <span class="pill ai" style="width:max-content">Certifiante</span>
        <h4 style="font-size:14.5px;font-weight:720;line-height:1.3">Management d'équipe & feedback</h4>
        <p class="muted" style="font-size:12.5px;line-height:1.5">Conduire des entretiens, donner un feedback constructif et animer un collectif.</p>
        <div style="display:flex;flex-wrap:wrap;gap:8px 14px;font-size:11.5px;color:var(--ink-3)"><span>${ic('clock','s')} 12 h</span><span>${ic('award','s')} Intermédiaire</span></div>
        <button class="btn btn-p btn-sm" data-enroll style="margin-top:2px;width:max-content">S'inscrire</button>
      </div>
      <div class="card p" style="display:flex;flex-direction:column;gap:8px">
        <span class="pill new" style="width:max-content">Populaire</span>
        <h4 style="font-size:14.5px;font-weight:720;line-height:1.3">Finance stratégique pour managers</h4>
        <p class="muted" style="font-size:12.5px;line-height:1.5">Piloter un centre de profit : budget, marge et arbitrages d'investissement.</p>
        <div style="display:flex;flex-wrap:wrap;gap:8px 14px;font-size:11.5px;color:var(--ink-3)"><span>${ic('clock','s')} 18 h</span><span>${ic('award','s')} Avancé</span></div>
        <button class="btn btn-p btn-sm" data-enroll style="margin-top:2px;width:max-content">S'inscrire</button>
      </div>
      <div class="card p" style="display:flex;flex-direction:column;gap:8px">
        <span class="pill new" style="width:max-content">Nouveau</span>
        <h4 style="font-size:14.5px;font-weight:720;line-height:1.3">Prise de parole & influence</h4>
        <p class="muted" style="font-size:12.5px;line-height:1.5">Convaincre en comité, structurer un message et gagner en impact oral.</p>
        <div style="display:flex;flex-wrap:wrap;gap:8px 14px;font-size:11.5px;color:var(--ink-3)"><span>${ic('clock','s')} 8 h</span><span>${ic('award','s')} Tous niveaux</span></div>
        <button class="btn btn-p btn-sm" data-enroll style="margin-top:2px;width:max-content">S'inscrire</button>
      </div>
      <div class="card p" style="display:flex;flex-direction:column;gap:8px">
        <span class="pill mut" style="width:max-content">Expertise</span>
        <h4 style="font-size:14.5px;font-weight:720;line-height:1.3">IFRS 9 : approfondissement du scoring</h4>
        <p class="muted" style="font-size:12.5px;line-height:1.5">Modélisation avancée du risque de crédit et provisionnement réglementaire.</p>
        <div style="display:flex;flex-wrap:wrap;gap:8px 14px;font-size:11.5px;color:var(--ink-3)"><span>${ic('clock','s')} 14 h</span><span>${ic('award','s')} Avancé</span></div>
        <button class="btn btn-p btn-sm" data-enroll style="margin-top:2px;width:max-content">S'inscrire</button>
      </div>
    </div>
  </div>
</div></div>`;
WIRE.formation=function(){
  $$('[data-enroll]').forEach(function(b){ b.addEventListener('click',function(){ toast('Inscription confirmée'); }); });
};

S.offreDetail=()=>`<div class="fade app">${sidebar('collab','Offres internes')}<div class="main">${top('Détail de l\'offre','Mission transverse · Retail Banking','collab')}
  <div class="content">
    ${crumb([['Offres internes','offres'],['Détail',null]])}
    <div class="cols">
      <div class="stack">
        <div class="card p">
          <div style="display:flex;align-items:flex-start;gap:8px;flex-wrap:wrap"><span class="pill ai" style="width:max-content">Mission transverse</span><span class="pill new" style="width:max-content">20 % de votre temps</span></div>
          <h2 class="disp" style="font-size:22px;margin:12px 0 6px">Ambassadeur Digital — Retail Banking</h2>
          <p class="muted" style="font-size:13px">Direction de la Banque de Détail · Réseau d'agences du Grand Casablanca</p>
          <div class="divider" style="margin:16px 0"></div>
          <h3 class="disp" style="font-size:15px;margin-bottom:8px">La mission</h3>
          <p style="font-size:13.5px;color:var(--ink-2);line-height:1.6">En tant qu'Ambassadeur Digital, vous accompagnez le déploiement des nouveaux outils digitaux (application mobile, signature électronique, ouverture de compte à distance) auprès des conseillers en agence. Vous animez des ateliers de prise en main, remontez les irritants terrain aux équipes produit et suivez les indicateurs d'adoption sur un panel de 12 agences pilotes.</p>
          <p style="font-size:13.5px;color:var(--ink-2);line-height:1.6;margin-top:10px">Cette mission de 3 mois, à hauteur de 20 % de votre temps, est un tremplin idéal pour développer votre leadership transverse et votre culture produit — deux compétences clés vers un poste de Manager de Pôle.</p>
          <div class="divider" style="margin:16px 0"></div>
          <h3 class="disp" style="font-size:15px;margin-bottom:10px">Compétences requises</h3>
          <div style="display:flex;flex-wrap:wrap;gap:8px"><span class="chip">Pédagogie & animation</span><span class="chip">Culture digitale</span><span class="chip">Connaissance du réseau</span><span class="chip">Communication</span><span class="chip">Analyse d'usage</span></div>
        </div>
      </div>
      <div class="stack">
        <div class="card p">
          <div class="sec-h"><h3>Informations</h3></div>
          <div style="display:flex;flex-direction:column;gap:12px;font-size:13px">
            <span style="display:inline-flex;align-items:center;gap:9px;color:var(--ink-2)">${ic('pin','s')} Localisation · Hybride (agences + Siège)</span>
            <span style="display:inline-flex;align-items:center;gap:9px;color:var(--ink-2)">${ic('clock','s')} Durée · 3 mois, 20 % du temps</span>
            <span style="display:inline-flex;align-items:center;gap:9px;color:var(--ink-2)">${ic('cal','s')} Échéance de candidature · 30 septembre 2026</span>
            <span style="display:inline-flex;align-items:center;gap:9px;color:var(--ink-2)">${ic('user','s')} Référent · Nadia El Amrani</span>
          </div>
          <div class="wnote" style="margin-top:14px">${ic('bell','s')} En postulant, votre manager direct sera informé de votre candidature à cette mission transverse.</div>
          <button class="btn btn-p block" id="postuler" style="margin-top:14px">${ic('send','s')} Postuler à cette mission</button>
        </div>
        <div class="callout"><div class="ci">${ic('spark','s')}</div><div><h4>+4 % de compatibilité</h4><p>Cette mission renforce « Leadership transverse » — un levier direct vers votre objectif Manager de Pôle.</p></div></div>
      </div>
    </div>
  </div>
</div></div>`;
WIRE.offreDetail=function(){
  const b=$('#postuler'); if(!b) return;
  b.addEventListener('click',function(){
    const m=openModal('<div class="mhead"><div><h3>Postuler à la mission</h3><p class="muted" style="font-size:12px;margin-top:3px">Ambassadeur Digital — Retail Banking</p></div><button class="xbtn" data-mclose>✕</button></div><div id="mbody"></div>');
    const state={motiv:'',consent:false};
    let step=0;
    const bar=a=>`<div class="ministep"><span class="s ${a>0?'done':'on'}">1</span><span class="ln ${a>0?'on':''}"></span><span class="s ${a>1?'done':a===1?'on':''}">2</span><span class="ln ${a>1?'on':''}"></span><span class="s ${a===2?'on':''}">3</span></div>`;
    function draw(){
      const body=m.querySelector('#mbody');
      if(step===0){
        body.innerHTML=bar(0)+`<div class="formrow"><label>Votre motivation</label><textarea class="ta" id="mMotiv" placeholder="En quoi cette mission correspond-elle à votre projet…">${state.motiv}</textarea></div>
          <div class="wnote ok">${ic('spark','s')} Astuce : reliez la mission à une compétence à développer (ex. digitalisation du réseau).</div>
          <div class="mfoot"><button class="btn btn-g btn-sm" data-mclose>Annuler</button><button class="btn btn-p btn-sm" id="mNext">Suivant →</button></div>`;
      }else if(step===1){
        body.innerHTML=bar(1)+`<label class="chk"><input type="checkbox" id="mConsent" ${state.consent?'checked':''}><span>J'accepte que mon manager direct (Sarah Kabbaj) soit informé de ma candidature à cette mission transverse.</span></label>
          <div class="wnote">${ic('bell','s')} Conformément à la politique de mobilité BMCI, votre manager reçoit une notification dès qu'un collaborateur postule à une mission transverse.</div>
          <div class="mfoot"><button class="btn btn-g btn-sm" id="mPrev">← Précédent</button><button class="btn btn-p btn-sm" id="mNext" ${state.consent?'':'disabled'}>Suivant →</button></div>`;
      }else{
        const mot=state.motiv?state.motiv:'<i class="muted">Non renseignée</i>';
        body.innerHTML=bar(2)+`<div class="rcap">
            <div class="rrow"><span class="muted">Mission</span><b style="text-align:right">Ambassadeur Digital — Retail Banking</b></div>
            <div class="rrow"><span class="muted">Candidat</span><b>Jean-Marc Dupont</b></div>
            <div class="rrow"><span class="muted">Motivation</span><span style="text-align:right;max-width:60%">${mot}</span></div>
            <div class="rrow"><span class="muted">Manager informé</span><b style="color:var(--green-deep)">Oui · Sarah Kabbaj</b></div>
          </div>
          <div class="mfoot"><button class="btn btn-g btn-sm" id="mPrev">← Précédent</button><button class="btn btn-p btn-sm" id="mSend">${ic('send','s')} Envoyer ma candidature</button></div>`;
      }
      hook();
    }
    function hook(){
      const t=m.querySelector('#mMotiv'); if(t) t.addEventListener('input',()=>state.motiv=t.value);
      const c=m.querySelector('#mConsent'); if(c) c.addEventListener('change',function(){ state.consent=c.checked; const n=m.querySelector('#mNext'); if(n) n.disabled=!c.checked; });
      const nx=m.querySelector('#mNext'); if(nx) nx.addEventListener('click',function(){ if(step===1&&!state.consent) return; step++; draw(); });
      const pv=m.querySelector('#mPrev'); if(pv) pv.addEventListener('click',function(){ step--; draw(); });
      const sd=m.querySelector('#mSend'); if(sd) sd.addEventListener('click',function(){ toast('Candidature envoyée'); closeModal(); go('mesCandidatures'); });
    }
    draw();
  });
};

S.mesCandidatures=()=>`<div class="fade app">${sidebar('collab','Offres internes')}<div class="main">${top('Mes candidatures','Suivi de vos postulations internes','collab')}
  <div class="content">
    ${crumb([['Offres internes','offres'],['Mes candidatures',null]])}
    <div class="grid3" style="grid-template-columns:repeat(4,1fr)">
      <div class="kpi"><div class="ki">${ic('send','s')}</div><b class="tnum">4</b><small>Candidatures</small></div>
      <div class="kpi"><div class="ki">${ic('clock','s')}</div><b class="tnum">2</b><small>En cours</small></div>
      <div class="kpi"><div class="ki">${ic('cal','s')}</div><b class="tnum">1</b><small>Entretien planifié</small></div>
      <div class="kpi"><div class="ki">${ic('check','s')}</div><b class="tnum">50 %</b><small>Taux de réponse</small></div>
    </div>
    <div class="card p">
      <div class="sec-h"><h3>Historique</h3><button class="btn btn-g btn-sm" data-go="offres">${ic('search','s')} Explorer les offres</button></div>
      <div class="clist">
        ${[
          ['spark','Ambassadeur Digital — Retail Banking','Mission transverse','12 juillet 2026','new','Envoyée'],
          ['brief','Analyste Crédit Senior — Corporate Banking','Poste','28 juin 2026','warn','En revue'],
          ['bolt','Task Force — IA Générative & Compliance','Projet innovation','15 juin 2026','ai','Entretien planifié · 18 juil.'],
          ['clock','Relecture Expertise — Rapport ESG 2026','Gig ponctuel','2 mai 2026','hot','Refusée']
        ].map(c=>`<div class="crow"><div class="ci2">${ic(c[0])}</div><div class="cmain"><h4>${c[1]}</h4><div class="cmeta"><span>${ic('brief','s')} ${c[2]}</span><span>${ic('cal','s')} Envoyée le ${c[3]}</span></div></div><span class="pill ${c[4]}" style="width:max-content;white-space:nowrap">${c[5]}</span></div>`).join('')}
      </div>
    </div>
  </div>
</div></div>`;

S.souhaitSuivi=()=>`<div class="fade app">${sidebar('collab','Mon profil')}<div class="main">${top('Mes souhaits d\'évolution','Vos aspirations transmises à votre manager','collab')}
  <div class="content">
    ${crumb([['Mon profil','collab'],['Souhaits d\'évolution',null]])}
    <div class="callout"><div class="ci">${ic('route','s')}</div><div style="flex:1"><h4>Vos souhaits guident vos recommandations</h4><p>Les souhaits que vous poussez sont transmis à votre manager et alimentent le moteur de recommandations du Groupe.</p></div><button class="btn btn-g btn-sm" style="align-self:center" data-go="collab">Gérer sur mon profil</button></div>
    <div class="stack">
      <div class="card p">
        <div class="sec-h"><h3 style="font-size:15px">Manager d'équipe Risques</h3><span class="pill new" style="width:max-content">Appuyé par le manager</span></div>
        <div style="display:flex;flex-wrap:wrap;gap:8px 16px;font-size:12px;color:var(--ink-3)"><span>${ic('route','s')} Horizon 1 an</span><span>${ic('cal','s')} Poussé le 3 juin 2026</span><span>${ic('user','s')} Manager : Sarah Kabbaj</span></div>
        <div class="jalons" style="grid-template-columns:repeat(3,1fr);margin-top:14px">
          <div class="jalon done"><div class="jn">${ic('check','s')}</div><h5>Souhait poussé</h5><small>Par vous</small></div>
          <div class="jalon done"><div class="jn">${ic('check','s')}</div><h5>Transmis au manager</h5><small>Notifié le 4 juin</small></div>
          <div class="jalon active"><div class="jn">${ic('check','s')}</div><h5>Appuyé par le manager</h5><small>Recommandé aux RH</small></div>
        </div>
      </div>

      <div class="card p">
        <div class="sec-h"><h3 style="font-size:15px">Mobilité internationale (Paris / Londres)</h3><span class="pill ai" style="width:max-content">Transmis au manager</span></div>
        <div style="display:flex;flex-wrap:wrap;gap:8px 16px;font-size:12px;color:var(--ink-3)"><span>${ic('route','s')} Horizon 2 à 3 ans</span><span>${ic('cal','s')} Poussé le 21 juin 2026</span><span>${ic('pin','s')} Groupe BNP Paribas</span></div>
        <div class="jalons" style="grid-template-columns:repeat(3,1fr);margin-top:14px">
          <div class="jalon done"><div class="jn">${ic('check','s')}</div><h5>Souhait poussé</h5><small>Par vous</small></div>
          <div class="jalon active"><div class="jn">2</div><h5>Transmis au manager</h5><small>En cours d'examen</small></div>
          <div class="jalon"><div class="jn">3</div><h5>Appui du manager</h5><small>En attente</small></div>
        </div>
      </div>

      <div class="card p">
        <div class="sec-h"><h3 style="font-size:15px">Certification Risk Management (GARP)</h3><span class="pill mut" style="width:max-content">En attente</span></div>
        <div style="display:flex;flex-wrap:wrap;gap:8px 16px;font-size:12px;color:var(--ink-3)"><span>${ic('route','s')} Horizon 6 mois</span><span>${ic('cal','s')} Poussé le 1 juillet 2026</span><span>${ic('award','s')} Financement formation</span></div>
        <div class="jalons" style="grid-template-columns:repeat(3,1fr);margin-top:14px">
          <div class="jalon done"><div class="jn">${ic('check','s')}</div><h5>Souhait poussé</h5><small>Par vous</small></div>
          <div class="jalon"><div class="jn">2</div><h5>Transmis au manager</h5><small>En file d'attente</small></div>
          <div class="jalon"><div class="jn">3</div><h5>Appui du manager</h5><small>En attente</small></div>
        </div>
      </div>
    </div>
  </div>
</div></div>`;
