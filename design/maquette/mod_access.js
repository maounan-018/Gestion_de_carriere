/*==SCREENS==*/
[["motDePasseOublie","Mot de passe oublié","Accès"],["onboardingErreur","Onboarding — incohérence","Accès"],["notifications","Notifications","Collaborateur"],["confidentialite","Confidentialité","Collaborateur"]]
/*==CSS==*/
/* amber = ton d'alerte de la palette (alias sur --warning, aucune couleur nouvelle) */
:root{--amber:var(--warning);--amber-soft:var(--warning-soft)}

/* bandeau d'alerte (onboardingErreur) */
.alertband{display:flex;gap:12px;align-items:flex-start;padding:14px;border-radius:var(--r);background:var(--amber-soft);border:1px solid color-mix(in srgb,var(--amber) 32%,transparent);text-align:left}
.alertband .abi{width:34px;height:34px;border-radius:10px;background:var(--amber);color:#fff;display:grid;place-items:center;flex:none}
.alertband b{font-size:13px;font-weight:750;color:var(--amber);display:block}
.alertband p{font-size:12.5px;color:var(--ink-2);line-height:1.5;margin-top:3px}

/* rappel des infos saisies */
.recap{border:1px solid var(--border);border-radius:var(--r);overflow:hidden;background:var(--paper)}
.recap-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 13px;border-top:1px solid var(--border);font-size:13px}
.recap-row:first-child{border-top:0}
.recap-row .rk{display:inline-flex;align-items:center;gap:7px;color:var(--ink-3);font-weight:600}
.recap-row .rv{font-weight:700;color:var(--ink);display:inline-flex;align-items:center;gap:8px;text-align:right}

/* centre de notifications */
.nlist{display:flex;flex-direction:column;margin:2px -6px 0}
.notif{display:flex;gap:13px;padding:14px 12px;border-top:1px solid var(--border);align-items:flex-start;border-radius:12px;transition:background .16s}
.notif:first-child{border-top:0}
.notif.unread{background:var(--green-ghost)}
.notif .ni{width:38px;height:38px;border-radius:11px;background:var(--green-soft);color:var(--green-deep);display:grid;place-items:center;flex:none}
.notif .nb{flex:1;min-width:0}
.notif .nb h4{font-size:13.5px;font-weight:700;display:flex;align-items:center;gap:8px;flex-wrap:wrap;line-height:1.25}
.notif .nb p{font-size:12.5px;color:var(--ink-3);line-height:1.45;margin-top:3px}
.notif .nt{font-size:11px;color:var(--ink-3);white-space:nowrap;font-weight:600;flex:none;margin-top:2px}

/* confidentialité */
.conf-row{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:15px 0;border-top:1px solid var(--border);flex-wrap:wrap}
.conf-row:first-child{border-top:0}
.conf-row .ct{min-width:200px;flex:1}
.conf-row .ct h4{font-size:13.5px;font-weight:700}
.conf-row .ct p{font-size:12px;color:var(--ink-3);margin-top:2px;line-height:1.4}
.conf-row .seg{flex:none}
.conf-row .seg .svgi{margin-right:5px}
/*==JS==*/
/* ============ 1) MOT DE PASSE OUBLIÉ — parcours auth en 3 étapes ============ */
S.motDePasseOublie=()=>`<div class="fade auth"><div class="acard">
  <div class="blk"><div class="mk">B</div><div><b>BMCI Carrière</b><span>Gestion de carrière</span></div></div>
  <div class="ministep" id="mdpSteps"></div>
  <div id="mdpBody"></div>
</div></div>`;

WIRE.motDePasseOublie=function(){
  const steps=$('#mdpSteps'),body=$('#mdpBody');
  if(!steps||!body)return;
  function setSteps(cur){
    steps.innerHTML=[0,1,2].map(i=>{
      const cls=i<cur?'s done':i===cur?'s on':'s';
      const inner=i<cur?'✓':(i+1);
      return `<span class="${cls}">${inner}</span>`+(i<2?`<span class="ln${i<cur?' on':''}"></span>`:'');
    }).join('');
  }
  /* étape 1 : e-mail professionnel */
  function step1(){
    setSteps(0);
    body.innerHTML=`<h1>Mot de passe oublié ?</h1>
      <p class="sub">Saisissez votre e-mail professionnel <b>@bmci.local</b> : nous vous enverrons un code de réinitialisation.</p>
      <div class="field"><label for="mdpEmail">E-mail professionnel</label>
        <div class="inp" id="mdpEw"><span class="ic">${ic('mail','s')}</span><input id="mdpEmail" placeholder="prenom.nom@bmci.local"><span class="ic" id="mdpEtick"></span></div>
        <div class="fhint" id="mdpEhint" hidden></div></div>
      <button class="btn btn-p block" id="mdpNext1" disabled style="margin-top:6px">Envoyer le code →</button>
      <p class="sub" style="margin:16px 0 0"><button class="link" data-go="connexion">← Retour à la connexion</button></p>`;
    const email=$('#mdpEmail'),btn=$('#mdpNext1');
    function chk(){
      const v=email.value.trim(),ok=/^[^@\s.]+\.[^@\s]+@bmci\.local$/i.test(v),has=v.length>0;
      $('#mdpEtick').innerHTML=ok?ic('check','s'):'';$('#mdpEtick').style.color='var(--green-deep)';
      $('#mdpEw').classList.toggle('ok',ok);$('#mdpEw').classList.toggle('err',has&&!ok);
      const h=$('#mdpEhint');
      if(!has){h.hidden=true;}
      else if(!ok){h.hidden=false;h.className='fhint err';h.innerHTML=ic('lock','s')+' Format attendu : prenom.nom@bmci.local';}
      else{h.hidden=false;h.className='fhint ok';h.innerHTML=ic('check','s')+' Adresse professionnelle valide';}
      btn.disabled=!ok;return ok;
    }
    email.addEventListener('input',chk);
    btn.addEventListener('click',()=>{if(chk()){toast('Code envoyé à '+email.value.trim(),'info');step2();}});
    email.focus();
  }
  /* étape 2 : code à 6 chiffres (style .otp) */
  function step2(){
    setSteps(1);
    body.innerHTML=`<div style="text-align:center;margin-bottom:4px;color:var(--green-deep)">${ic('mail')}</div>
      <h1>Entrez le code reçu</h1><p class="sub">Un code à 6 chiffres vient d'être envoyé à votre adresse professionnelle.</p>
      <div class="otp" id="mdpOtp">${[0,1,2,3,4,5].map(i=>`<input inputmode="numeric" maxlength="1" aria-label="Chiffre ${i+1}">`).join('')}</div>
      <div class="fhint ok" id="mdpOhint" hidden>${ic('check','s')} Code complet</div>
      <button class="btn btn-p block" id="mdpNext2" disabled style="margin-top:18px">Continuer →</button>
      <p class="sub" style="margin:16px 0 0">Pas reçu ? <button class="link" id="mdpResend">Renvoyer le code</button></p>`;
    const inp=$$('#mdpOtp input'),btn=$('#mdpNext2');
    inp.forEach((x,i)=>{
      x.addEventListener('input',()=>{
        x.value=x.value.replace(/\D/g,'').slice(0,1);
        if(x.value&&i<5)inp[i+1].focus();
        const full=inp.every(y=>y.value);$('#mdpOhint').hidden=!full;btn.disabled=!full;
      });
      x.addEventListener('keydown',e=>{if(e.key==='Backspace'&&!x.value&&i>0)inp[i-1].focus();});
    });
    inp[0].focus();
    const rs=$('#mdpResend');if(rs)rs.addEventListener('click',()=>toast('Nouveau code envoyé','info'));
    btn.addEventListener('click',()=>{if(inp.every(y=>y.value))step3();});
  }
  /* étape 3 : nouveau mot de passe (barre + critères verts) */
  function step3(){
    setSteps(2);
    body.innerHTML=`<h1>Nouveau mot de passe</h1><p class="sub">Choisissez un mot de passe robuste pour sécuriser votre espace.</p>
      <div class="field" style="margin-bottom:8px"><label for="mdpPass">Nouveau mot de passe</label>
        <div class="inp" id="mdpPw"><span class="ic">${ic('lock','s')}</span><input id="mdpPass" type="password" placeholder="Créez un mot de passe robuste"><button class="link" id="mdpTpass" type="button" style="font-size:12px">Afficher</button></div>
        <div class="meter"><i id="mdpMeter"></i></div><div class="fhint" id="mdpStr"></div>
        <ul class="crit" id="mdpCrit"><li data-c="len"><span class="tick">${ic('check','s')}</span>8 caractères min.</li><li data-c="upper"><span class="tick">${ic('check','s')}</span>Une majuscule</li><li data-c="lower"><span class="tick">${ic('check','s')}</span>Une minuscule</li><li data-c="digit"><span class="tick">${ic('check','s')}</span>Un chiffre</li><li data-c="special"><span class="tick">${ic('check','s')}</span>Un caractère spécial</li></ul>
      </div>
      <div class="field"><label for="mdpPass2">Confirmez le mot de passe</label>
        <div class="inp" id="mdpP2w"><span class="ic">${ic('lock','s')}</span><input id="mdpPass2" type="password" placeholder="Retapez votre mot de passe"></div>
        <div class="fhint" id="mdpMatch" hidden></div></div>
      <button class="btn btn-p block" id="mdpDone" disabled style="margin-top:6px">${ic('shield','s')} Réinitialiser mon mot de passe</button>`;
    const pass=$('#mdpPass'),pass2=$('#mdpPass2'),btn=$('#mdpDone');
    const T={len:v=>v.length>=8,upper:v=>/[A-Z]/.test(v),lower:v=>/[a-z]/.test(v),digit:v=>/\d/.test(v),special:v=>/[^A-Za-z0-9]/.test(v)};
    function ep(){
      const v=pass.value;let ok=0;
      Object.entries(T).forEach(([k,fn])=>{const li=$(`#mdpCrit li[data-c="${k}"]`);const p=fn(v);li.classList.toggle('ok',p);if(p)ok++;});
      const m=$('#mdpMeter');m.style.width=(ok/5*100)+'%';
      const col=['var(--danger)','var(--danger)','var(--warning)','var(--warning)','var(--green)'];
      m.style.background=v?(col[ok-1]||'var(--danger)'):'transparent';
      const st=$('#mdpStr'),lab=['Très faible','Faible','Moyen','Bon','Excellent'];
      if(!v){st.hidden=true;}else{st.hidden=false;st.className='fhint '+(ok===5?'ok':'err');st.innerHTML=(ok===5?ic('check','s'):ic('lock','s'))+' Force : '+(lab[ok-1]||'Très faible');}
      $('#mdpPw').classList.toggle('ok',ok===5);return ok===5;
    }
    function em(){
      const a=pass.value,b=pass2.value,h=$('#mdpMatch');
      if(!b){h.hidden=true;return false;}
      const ok=a===b;h.hidden=false;h.className='fhint '+(ok?'ok':'err');
      h.innerHTML=(ok?ic('check','s'):ic('lock','s'))+(ok?' Les mots de passe correspondent':' Les mots de passe ne correspondent pas');
      return ok;
    }
    function rf(){btn.disabled=!(ep()&&em());}
    [pass,pass2].forEach(el=>el.addEventListener('input',rf));
    $('#mdpTpass').addEventListener('click',()=>{const t=pass.type==='password';pass.type=t?'text':'password';$('#mdpTpass').textContent=t?'Masquer':'Afficher';});
    btn.addEventListener('click',()=>{toast('Mot de passe réinitialisé');go('connexion');});
    rf();
  }
  step1();
};

/* ============ 2) ONBOARDING — INCOHÉRENCE (état d'erreur) ============ */
S.onboardingErreur=()=>`<div class="fade auth"><div class="acard" style="max-width:480px">
  <div class="blk"><div class="mk">B</div><div><b>BMCI Carrière</b><span>Configuration du profil</span></div></div>
  ${stepper(2)}
  <div class="alertband"><span class="abi">${ic('flag','s')}</span><div><b>Incohérence détectée dans l'annuaire</b>
    <p>L'entité et le poste sélectionnés ne correspondent pas à votre adresse e-mail dans l'annuaire BMCI.</p></div></div>
  <h1 style="font-size:21px;margin-top:16px">Vérifions vos informations</h1>
  <p class="sub" style="margin:6px 0 16px">Voici ce que vous avez saisi. Corrigez l'étape concernée pour poursuivre la configuration.</p>
  <div class="recap">
    <div class="recap-row"><span class="rk">${ic('mail','s')} E-mail</span><span class="rv">jm.dupont@bmci.local</span></div>
    <div class="recap-row"><span class="rk">${ic('grid','s')} Entité déclarée</span><span class="rv">IT &amp; Digital <span class="pill warn">à vérifier</span></span></div>
    <div class="recap-row"><span class="rk">${ic('brief','s')} Poste déclaré</span><span class="rv">Chef de projet <span class="pill warn">à vérifier</span></span></div>
  </div>
  <div class="wnote" style="margin-top:14px">${ic('shield','s')} <span>Dans l'annuaire, l'adresse <b>jm.dupont@bmci.local</b> est rattachée à la <b>Direction de l'Audit</b>. Sélectionnez l'entité et le poste correspondants, ou contactez les RH si votre rattachement vient de changer.</span></div>
  <button class="btn btn-p block" data-go="onboarding" style="margin-top:16px">${ic('route','s')} Refaire cette étape</button>
  <button class="btn btn-g block" id="obErrSupport" style="margin-top:10px">${ic('chat','s')} Contacter le support RH</button>
</div></div>`;

WIRE.onboardingErreur=function(){
  const s=$('#obErrSupport');
  if(s)s.addEventListener('click',()=>toast('Demande transmise au support RH','info'));
};

/* ============ 3) NOTIFICATIONS — centre de notifications ============ */
S.notifications=()=>`<div class="fade app">${sidebar('collab','Tableau de bord')}<div class="main">${top('Notifications','Ce qui a bougé sur votre carrière','collab')}
  <div class="content">
    ${crumb([['Tableau de bord','collab'],['Notifications',null]])}
    <div class="card p">
      <div class="sec-h"><h3>Vos notifications <span class="badge b-mut" id="nUnread">3 non lues</span></h3>
        <button class="btn btn-g btn-sm" id="markAll">${ic('check','s')} Tout marquer comme lu</button></div>
      <div class="nlist" id="nlist">
        ${[
          ['award','var(--gold-soft)','var(--gold)','Nouvelle évaluation reçue','Sarah Kettani a finalisé votre évaluation annuelle 2025 — appréciation « Dépasse les attentes ».','Il y a 2 h',1],
          ['brief','','','Candidature passée en revue','Votre candidature au poste « Analyste Crédit Senior » est en cours d\'examen par la Direction des Risques.','Il y a 5 h',1],
          ['book','','','Formation assignée par votre manager','Jean-Marc Dupont vous a inscrit au parcours « Leadership Excellence @BNP ». Début le 21 juillet.','Hier',1],
          ['route','','','Votre souhait d\'évolution a été appuyé','Votre manager a soutenu le souhait « Manager d\'équipe Risques » auprès des RH.','Il y a 2 j',0],
          ['spark','','','Nouvelle offre correspondant à votre profil','« Chef de Projet Lean Management » — 88 % de compatibilité avec vos compétences.','Il y a 3 j',0],
          ['cal','','','Entretien annuel planifié','Rendez-vous confirmé avec Sarah Kettani le 18 juillet à 14 h 00, salle Atlas.','Il y a 4 j',0]
        ].map(n=>`<div class="notif ${n[6]?'unread':''}"><div class="ni"${n[1]?` style="background:${n[1]};color:${n[2]}"`:''}>${ic(n[0],'s')}</div>
          <div class="nb"><h4>${n[3]}${n[6]?' <span class="pill new">Non lu</span>':''}</h4><p>${n[4]}</p></div>
          <span class="nt">${n[5]}</span></div>`).join('')}
      </div>
    </div>
  </div></div></div>`;

WIRE.notifications=function(){
  const b=$('#markAll');
  if(!b)return;
  b.addEventListener('click',()=>{
    $$('#nlist .notif').forEach(n=>n.classList.remove('unread'));
    $$('#nlist .notif .pill').forEach(p=>p.remove());
    const c=$('#nUnread');if(c){c.textContent='À jour';c.className='badge b-role';}
    b.disabled=true;
    toast('Notifications marquées comme lues');
  });
};

/* ============ 4) CONFIDENTIALITÉ — visibilité par élément ============ */
S.confidentialite=()=>`<div class="fade app">${sidebar('collab','Mon profil')}<div class="main">${top('Confidentialité','Vous décidez qui voit quoi','collab')}
  <div class="content">
    ${crumb([['Mon profil','collab'],['Confidentialité',null]])}
    <div class="callout"><div class="ci">${ic('shield','s')}</div><div><h4>Votre nom d'affichage reste privé</h4>
      <p>Le nom choisi pendant l'onboarding n'est visible que de <b>vous</b> et du <b>Coach IA</b>. Les autres collaborateurs vous identifient uniquement via votre adresse e-mail professionnelle.</p></div></div>
    <div class="card p">
      <div class="sec-h"><h3>Visibilité de mon profil</h3><span class="eyebrow">5 éléments</span></div>
      <div id="confList">
        ${[
          ['Profil & description','Votre titre de poste, votre parcours et votre bio.',0],
          ['Compétences','Vos compétences évaluées et leurs niveaux.',0],
          ['Avis des pairs','Les évaluations laissées par vos collègues.',1],
          ['Souhaits d\'évolution','Vos aspirations de carrière et de mobilité.',1],
          ['Réalisations','Vos accomplissements et projets marquants.',0]
        ].map(r=>`<div class="conf-row"><div class="ct"><h4>${r[0]}</h4><p>${r[1]}</p></div>
          <div class="seg">${['Tout le monde','Mon manager & RH','Moi seul'].map((o,i)=>`<button class="${i===r[2]?'on':''}">${o}</button>`).join('')}</div></div>`).join('')}
      </div>
      <div class="divider" style="margin:16px 0"></div>
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
        <p class="muted" style="font-size:12px;flex:1;min-width:200px">${ic('lock','s')} Vos préférences s'appliquent immédiatement à l'ensemble du Groupe BMCI.</p>
        <button class="btn btn-p" id="saveConf">${ic('check','s')} Enregistrer mes préférences</button>
      </div>
    </div>
  </div></div></div>`;

WIRE.confidentialite=function(){
  $$('#confList .seg').forEach(seg=>{
    seg.addEventListener('click',e=>{
      const btn=e.target.closest('button');if(!btn)return;
      seg.querySelectorAll('button').forEach(x=>x.classList.remove('on'));
      btn.classList.add('on');
    });
  });
  const s=$('#saveConf');
  if(s)s.addEventListener('click',()=>toast('Préférences enregistrées'));
};
