// ==UserScript==
// @name         ALIGN Bande Live
// @namespace    align-live
// @version      5.5
// @description  Bande du live ALIGN sur TradingView : messages Telegram, bulles, télécommande 15 s, infobulles roses
// @match        https://*.tradingview.com/chart/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==
(function () {
  'use strict';
  if (window.__ALIGN_BANDE__) { try { window.__ALIGN_BANDE__.stop(); } catch (e) {} }
  const VERSION = '5.5';
  const SUJET = 'align-live-2a4bccafd9548d93';
  const BASE = [
    '🟢 LIVE ALIGN 24/7 • BTC • GOLD • NASDAQ',
    '👉 ABONNE-TOI • PARTAGE • TAPOTE L\'ÉCRAN',
    '🔗 LIEN EN BIO : COACH EN DIRECT',
    '📲 Le coach ALIGN en direct • lien en bio 🎁 gratuit',
    '⚠️ Le trading comporte un risque de perte • ceci n\'est pas un conseil financier'
  ];
  const DUREE_MAIN = 15000, DUREE_MSG = 8000;

  // ───── style ─────
  const css = document.createElement('style');
  css.id = 'align-bande-css';
  css.textContent = `
  #align-bande{position:fixed;z-index:9999;height:76px;overflow:hidden;pointer-events:none;
    background:linear-gradient(90deg,#ff2d95,#8a2be2 50%,#1e90ff);border-radius:0 0 10px 10px;
    box-shadow:0 4px 14px rgba(0,0,0,.5);font:900 35px/76px system-ui,Segoe UI,Arial,sans-serif;color:#fff;
    text-shadow:0 2px 3px rgba(0,0,0,.45);transition:opacity .2s}
  #align-bande .piste{position:absolute;white-space:nowrap;will-change:transform}
  #align-bande .piste span{margin-right:70px}
  #align-bande .flash{position:absolute;inset:0;display:none;align-items:center;justify-content:flex-start;
    padding:0;white-space:nowrap;overflow:hidden;font:900 35px/76px system-ui,Segoe UI,Arial,sans-serif;
    background:linear-gradient(90deg,#ff4fa3,#ffd400);color:#000;text-shadow:none}
  /* v5.4 : même taille d'écriture que la bande normale, une couleur par type d'info (plus de bande blanche) */
  #align-bande .flash.bulle{background:linear-gradient(90deg,#ff7ab8,#ffb3d6);color:#000}
  #align-bande .flash.tp{background:linear-gradient(90deg,#00c853,#ffd400);color:#000}
  #align-bande .flash.sl{background:linear-gradient(90deg,#ff1744,#ff8a65);color:#fff;text-shadow:0 2px 3px rgba(0,0,0,.45)}
  #align-bande .flash.membre{background:linear-gradient(90deg,#8a2be2,#ff2d95);color:#fff;text-shadow:0 2px 3px rgba(0,0,0,.45)}
  #align-bande .flash.proche{background:linear-gradient(90deg,#1e90ff,#00e5ff);color:#000}
  #align-bande .flash.alerte{background:linear-gradient(90deg,#ff9100,#ffd400);color:#000}
  #align-bande .flash span{display:inline-block;will-change:transform}
  #align-bande.on .piste{visibility:hidden} #align-bande.on .flash{display:flex}
  [class*="common-tooltip__body"]{background:#ffc0dc!important;color:#000!important;max-width:330px!important;
    width:330px!important;font-weight:600!important;border:2px solid #ff4fa3!important;border-radius:10px!important}
  [class*="common-tooltip__body"] *{color:#000!important}`;
  document.head.appendChild(css);

  // ───── bande ─────
  const bande = document.createElement('div');
  bande.id = 'align-bande';
  bande.innerHTML = '<div class="piste"></div><div class="flash"></div>';
  document.body.appendChild(bande);
  const piste = bande.querySelector('.piste'), flash = bande.querySelector('.flash');
  let extra = [];
  // v4.8 : la bande dit toujours ce qu'on regarde (marché + unité), mise à jour dès que la vue change
  function vueTxt() {
    const c = chart(); if (!c) return '';
    const s = String(c.symbol() || ''), r = String(c.resolution() || '');
    const m = /BTC/i.test(s) ? '🟠 BTC' : /XAU|GOLD/i.test(s) ? '🥇 GOLD' : /NAS|NQ|US100/i.test(s) ? '🟣 NASDAQ' : s.split(':').pop();
    const u = /^\d+$/.test(r) ? (+r >= 60 ? (+r / 60) + 'H' : r + ' MIN') : r === 'D' || r === '1D' ? '1 JOUR' : r;
    return '📺 VUE : ' + m + ' • ' + u;
  }
  let vueVue = '';
  setInterval(() => { const v = vueTxt(); if (v !== vueVue) { vueVue = v; remplir(); } }, 2000);
  function remplir() {
    const v = vueTxt();
    const items = (v ? [v] : []).concat(BASE, extra.slice(-3));
    const html = items.map(t => '<span>' + esc(t) + '</span>').join('');
    piste.innerHTML = html + html;
  }
  function esc(s) { return String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c])); }
  remplir();

  function zoneGraphique() {
    const c = document.querySelector('.chart-markup-table') || document.querySelector('.chart-container');
    return c ? c.getBoundingClientRect() : { left: 0, top: 0, width: innerWidth };
  }
  let x = 0, last = performance.now(), raf;
  function anim(now) {
    const r = zoneGraphique();
    const axe = 70;    // à droite : la bande s'arrête au début des prix
    const marge = 40;  // à gauche : un peu plus large (v5.2) tout en restant dans la zone filmée par TikTok
    bande.style.left = (r.left + marge) + 'px';
    bande.style.top = r.top + 'px';
    bande.style.width = Math.max(200, r.width - axe - marge) + 'px';
    const dt = Math.min(64, now - last); last = now;
    x -= dt * 0.09;
    const demi = piste.scrollWidth / 2;
    if (demi > 0 && -x >= demi) x += demi;
    piste.style.transform = 'translateX(' + x + 'px)';
    raf = requestAnimationFrame(anim);
  }
  raf = requestAnimationFrame(anim);

  // ───── messages (dans la bande, plus de fenêtre au centre) ─────
  const file = []; let occupe = false;
  // v5.1 : chaque info du bot (TP, SL, entrée, zone, pulsion…) passe 2 fois de suite dans la bande puis disparaît
  // (plus rien n'est ajouté pour toujours à la bande qui défile)
  // v5.4 : une couleur par type, et les infos importantes (TP, SL, entrée, nouvel abonné, prépare-toi) passent DEVANT la file
  function genre(t) {
    if (/TP\d? TOUCH|OBJECTIF FINAL|BRAVO/i.test(t)) return 'tp';
    if (/stop touch|SL TOUCH/i.test(t)) return 'sl';
    if (/REJOINT LA TEAM|BIENVENUE|nouvel abonn/i.test(t)) return 'membre';
    if (/FRÔLÉ|FROLE|DIRECTION TP|approche du TP|vers le TP/i.test(t)) return 'proche';
    if (/prépare-toi|ENTRE EN POSITION|zone clé|pas de panique|revient vers l'entrée|NEWS/i.test(t)) return 'alerte';
    return '';
  }
  function montrer(texte, bulle, fois) {
    const g = genre(texte), urgent = g && g !== 'proche' ? 1 : 0;
    const items = []; for (let i = 0; i < (fois || 1); i++) items.push({ texte, bulle, g });
    if (urgent) { let k = 0; while (k < file.length && file[k].g && file[k].g !== 'proche') k++; file.splice(k, 0, ...items); }
    else file.push(...items);
    suivant();
  }
  function suivant() {
    if (occupe || !file.length) return;
    occupe = true;
    const m = file.shift();
    flash.innerHTML = '<span>' + esc(m.texte) + '</span>';   // le message défile vite (lisible sur téléphone, même si TikTok coupe les bords)
    flash.className = 'flash' + (m.g ? ' ' + m.g : m.bulle ? ' bulle' : '');
    bande.classList.add('on');
    const sp = flash.firstChild, W = bande.clientWidth, w = sp.offsetWidth;
    const dur = Math.max(4000, (W + w) / 0.38);      // v5.4 : plus rapide (info en temps réel), toujours lisible
    sp.animate([{ transform: 'translateX(' + W + 'px)' }, { transform: 'translateX(' + (-w) + 'px)' }], { duration: dur, easing: 'linear' });
    setTimeout(() => { bande.classList.remove('on'); occupe = false; suivant(); }, dur);
  }

  // v5.3 : de temps en temps une astuce (2 passages) pour apprendre à lire le graphique, sans aucun prix ni sens
  // (les prix diffèrent d'un broker à l'autre : on montre OÙ regarder, la suite est « lien en bio »)
  const ASTUCES = [
    "👀 Astuce : mets-toi en vue 15 min et repère le dernier plus haut • c'est souvent là que le prix réagit • les infos en temps réel : lien en bio 🎁",
    "📉 Astuce : en vue 15 min, repère le dernier plus bas • s'il casse en CLÔTURE, le mouvement peut continuer • lien en bio 🎁",
    "🟨 Astuce : la ligne jaune ENTRÉE = la zone que le coach surveille • on attend la clôture 15 min • lien en bio 🎁",
    "🕯 Astuce : une mèche seule ne suffit pas • c'est la CLÔTURE de la bougie 15 min qui décide • lien en bio 🎁",
    "🔵 Astuce : ligne bleue = TP • ligne rouge = SL • le coach te dit quand ça s'approche • lien en bio 🎁",
    "📊 Astuce : regarde le tableau en bas • plus il y a d'unités alignées, plus le mouvement est solide • lien en bio 🎁"
  ];
  let astuceN = 0;
  const astuceT = setInterval(() => {
    if (occupe || file.length) return;            // jamais par-dessus une vraie info (TP, SL, news…)
    montrer(ASTUCES[astuceN++ % ASTUCES.length], true, 2);
  }, 20 * 60 * 1000);

  // ───── télécommande 15 s ─────
  let retour = null;
  // zoom lisible sur téléphone (TikTok) : grosses bougies, prix au-dessus du tableau, place pour la bande
  // petites unités (1m à 5m) : prix cadré serré autour du dernier cours pour que ENTRÉE / SL / ZONE ne se chevauchent pas
  const SPAN = {};   // désactivé : le cadrage serré cachait ENTRÉE / SL (v67 : les étiquettes gênantes sont masquées sous 15 min)
  function dernierPrix() {
    const m = document.title.match(/\d[\d\s\u00a0\u202f]*,\d+/);
    return m ? parseFloat(m[0].replace(/[\s\u00a0\u202f]/g, '').replace(',', '.')) : NaN;
  }
  // v5.2 : si Adel change le zoom / la hauteur des prix, c'est retenu (même après rechargement) et le script ne le défait plus
  let PREF = { bar: 18, off: 10, manuelPrix: false };
  try { PREF = Object.assign(PREF, JSON.parse(localStorage.getItem('alignBandePref') || '{}')); } catch (e) {}
  function sauverPref() { try { localStorage.setItem('alignBandePref', JSON.stringify(PREF)); } catch (e) {} }
  function memoriser() { try {
    const c = chart(); if (!c) return;
    const ts = c.getTimeScale(), b = ts.barSpacing(), o = ts.rightOffset();
    if (b > 1 && b < 80) PREF.bar = b;
    if (o >= 0 && o <= 80) PREF.off = o;          // un retour dans l'historique n'est pas une préférence
    PREF.manuelPrix = !c.getPanes()[0].getMainSourcePriceScale().isAutoScale();
    sauverPref();
  } catch (e) {} }
  function cadrerPrix(c) {
    const ps = c.getPanes()[0].getMainSourcePriceScale();
    const k = SPAN[c.resolution()], p = dernierPrix();
    if (k && p > 0) { const e = p * k; ps.setAutoScale(false); ps.setVisiblePriceRange({ from: p - e * 0.55, to: p + e * 0.45 }); }
    else if (!ps.isAutoScale() && !PREF.manuelPrix) ps.setAutoScale(true);
  }
  function zoom(delai) {
    setTimeout(() => { try {
      const c = chart(); if (!c) return;
      c.applyOverrides({ 'scalesProperties.scaleSeriesOnly': false, 'paneProperties.topMargin': 16, 'paneProperties.bottomMargin': 38 });   // v5.0 : SL / TP inclus dans l'échelle, place pour le tableau en bas
      const ts = c.getTimeScale(); ts.setBarSpacing(PREF.bar); ts.setRightOffset(PREF.off);
      cadrerPrix(c);
      // l'indicateur ALIGN toujours DEVANT les bougies (étiquettes lisibles)
      const al = c.getAllStudies().filter(x => /^ALIGN/.test(x.name)).map(x => x.id); if (al.length) c.bringToFront(al);
    } catch (e) {} }, delai || 900);
  }
  zoom(300);
  // suivi automatique : même cadrage sur toutes les unités et marchés, le graphique suit le prix tout seul
  // (si Adel bouge le graphique à la souris, on lui laisse la main 20 s puis on recadre)
  let mainUser = 0;
  ['wheel', 'mousedown', 'touchstart'].forEach(ev => document.addEventListener(ev, e => {
    if (e.target && e.target.closest && (e.target.closest('.chart-markup-table') || e.target.closest('.price-axis') || e.target.closest('.time-axis'))) {
      mainUser = Date.now(); clearTimeout(memoriser.t); memoriser.t = setTimeout(memoriser, 1500);
    }
  }, { passive: true, capture: true }));
  // nouveau marché = autre échelle de prix → prix en automatique ; le zoom des bougies d'Adel est gardé
  try { const c0 = chart(); c0.onIntervalChanged().subscribe(null, () => zoom(1200)); c0.onSymbolChanged().subscribe(null, () => { PREF.manuelPrix = false; sauverPref(); zoom(1200); }); } catch (e) {}
  const suivi = setInterval(() => { try {
    if (Date.now() - mainUser < 20000) return;
    const c = chart(); if (!c) return;
    cadrerPrix(c);
    const ts = c.getTimeScale();
    if (Math.abs(ts.barSpacing() - PREF.bar) > 0.5) ts.setBarSpacing(PREF.bar);
    if (Math.abs(ts.rightOffset() - PREF.off) > 2) { ts.scrollToRealtime(); ts.setRightOffset(PREF.off); }
  } catch (e) {} }, 3000);
  function chart() { try { return window.TradingViewApi.activeChart(); } catch (e) { return null; } }
  function commande(sorte, valeur, prenom) {
    const c = chart(); if (!c) return;
    if (!retour) retour = { tf: c.resolution(), sym: c.symbol() };
    const nom = prenom ? prenom + ' a demandé ' : 'Vue ';
    const fin = ' • ⏳ 15 s • 📸 fais ta capture';
    if (sorte === 'tf') { c.setResolution(valeur); montrer('🎮 ' + nom + (valeur === '60' ? '1 h' : valeur + ' min') + fin, true); }
    else if (sorte === 'sym') { c.setSymbol(valeur); montrer('🎮 ' + nom + valeur.split(':').pop() + fin, true); }
    else return;
    zoom();
    clearTimeout(commande.t);
    commande.t = setTimeout(() => {
      const c2 = chart(); if (c2 && retour) { const r0 = retour; c2.setSymbol(r0.sym, () => { c2.setResolution(r0.tf); zoom(); }); }
      retour = null;
    }, DUREE_MAIN);
  }

  // v4.9 : TP touché = explosion à l'écran (aucune info d'entrée : juste la fête, le coach reste dans le bot)
  const cssFeu = document.createElement('style');
  cssFeu.textContent = `#align-feu{position:fixed;inset:0;z-index:10000;pointer-events:none;display:flex;align-items:center;justify-content:center}
  #align-feu .titre{font:900 78px/1 system-ui,Segoe UI,Arial,sans-serif;color:#fff;text-shadow:0 0 18px #ff2d95,0 0 36px #1e90ff;animation:feuZoom 1.2s ease-out}
  #align-feu .eclat{position:absolute;font-size:46px;animation:feuVol 1.8s ease-out forwards}
  @keyframes feuZoom{0%{transform:scale(.2);opacity:0}60%{transform:scale(1.25);opacity:1}100%{transform:scale(1)}}
  @keyframes feuVol{0%{transform:translate(0,0) scale(.4);opacity:1}100%{transform:translate(var(--dx),var(--dy)) scale(1.3);opacity:0}}`;
  document.head.appendChild(cssFeu);
  function feuArtifice(titre) {
    try {
      document.getElementById('align-feu')?.remove();
      const f = document.createElement('div'); f.id = 'align-feu';
      f.innerHTML = '<div class="titre">' + esc(titre) + '</div>';
      const em = ['🎆', '🎇', '✨', '🔥', '💥', '🥳'];
      for (let i = 0; i < 28; i++) {
        const e = document.createElement('span'); e.className = 'eclat'; e.textContent = em[i % em.length];
        const a = (i / 28) * Math.PI * 2, d = 220 + Math.random() * 260;
        e.style.setProperty('--dx', Math.cos(a) * d + 'px'); e.style.setProperty('--dy', Math.sin(a) * d + 'px');
        e.style.animationDelay = (Math.random() * 0.4) + 's'; f.appendChild(e);
      }
      document.body.appendChild(f);
      setTimeout(() => f.remove(), 4500);
    } catch (e) {}
  }
  window.__ALIGN_FEU__ = feuArtifice;

  function recu(txt) {
    txt = String(txt || '').trim(); if (!txt) return;
    if (txt.startsWith('CMD:')) {
      const p = txt.split(':');               // CMD:sorte:valeur(:avec:deux-points):prénom
      const sorte = p[1], prenom = p[p.length - 1], valeur = p.slice(2, -1).join(':');
      commande(sorte, valeur, prenom); return;
    }
    const bulle = txt.startsWith('BULLE:');
    if (bulle) txt = txt.slice(6).trim();
    if (/TP\d? TOUCH|OBJECTIF FINAL|TP2 TOUCH/i.test(txt)) feuArtifice(/TP2|FINAL/i.test(txt) ? '🏆 TP2 TOUCHÉ !' : '🎯 TP TOUCHÉ !');
    montrer(txt, bulle, 2);
  }

  // ───── écoute du canal ntfy (reconnexion automatique) ─────
  let es;
  function ecouter() {
    try { es && es.close(); } catch (e) {}
    es = new EventSource('https://ntfy.sh/' + SUJET + '/sse');
    es.onmessage = e => { try { const d = JSON.parse(e.data); if (d.event === 'message') recu(d.message); } catch (er) {} };
    es.onerror = () => { try { es.close(); } catch (e) {} setTimeout(ecouter, 5000); };
  }
  ecouter();

  // ───── infobulles : baissier → en haut, haussier → en bas, collées à gauche ─────
  const obs = new MutationObserver(() => {
    let survol = false;
    document.querySelectorAll('[class*="common-tooltip-"][class*="common-tooltip--"]').forEach(t => {
      const txt = t.innerText || '';
      if (!/[━]|ENTRÉE|SL|TP|ZONE|RETOURNEMENT|CONFIRMATION/.test(txt)) return;
      survol = true;
      const r = zoneGraphique();
      // v4.7 : toutes les infobulles (ENTRÉE, SL, TP, unités…) s'ouvrent TOUJOURS au même endroit : en haut à gauche, sous le nom de l'indicateur
      t.style.left = (r.left + 12) + 'px';
      t.style.right = 'auto';
      t.style.top = (r.top + 56) + 'px'; t.style.bottom = 'auto';
    });
    bande.style.opacity = survol ? '0' : '1';   // la bande s'efface pendant le survol d'une infobulle
  });
  obs.observe(document.body, { childList: true, subtree: true });

  // ───── v5.5 : LE SPECTACLE — la bande regarde l'écran elle-même ─────
  // Elle lit les bougies affichées (marché + unité de la vue) et anime le live : accélération, cassure, gros volume,
  // compte à rebours de clôture, tendance, cœurs qui montent. JAMAIS un prix ni un niveau, jamais le mot Telegram :
  // juste le spectacle + « lien en bio ». Les vraies infos précises restent dans le privé (bot).
  const cssShow = document.createElement('style');
  cssShow.textContent = `
  #align-show{position:fixed;z-index:10001;pointer-events:none;display:none;align-items:center;gap:14px;padding:10px 26px;
    border-radius:18px;font:900 40px/1.1 system-ui,Segoe UI,Arial,sans-serif;color:#fff;white-space:nowrap;
    text-shadow:0 3px 6px rgba(0,0,0,.55);box-shadow:0 8px 30px rgba(0,0,0,.55);transform:translateX(-50%)}
  #align-show.go{display:flex;animation:showPop 2.8s cubic-bezier(.2,1.4,.4,1) forwards}
  #align-show.bas{background:linear-gradient(90deg,#ff1744,#ff6d00)} #align-show.haut{background:linear-gradient(90deg,#00c853,#00e5ff);color:#000;text-shadow:none}
  #align-show.neutre{background:linear-gradient(90deg,#8a2be2,#ff2d95)}
  #align-show .emo{font-size:54px;animation:showBat .5s ease-in-out infinite alternate}
  @keyframes showPop{0%{opacity:0;transform:translateX(-50%) scale(.3)}15%{opacity:1;transform:translateX(-50%) scale(1.12)}
    25%{transform:translateX(-50%) scale(1)}85%{opacity:1}100%{opacity:0;transform:translateX(-50%) scale(.9) translateY(-14px)}}
  @keyframes showBat{from{transform:scale(1)}to{transform:scale(1.25)}}
  #align-cadre{position:fixed;z-index:9998;pointer-events:none;border-radius:8px;opacity:0}
  #align-cadre.go{animation:cadreFlash 1.6s ease-out 2}
  @keyframes cadreFlash{0%{opacity:0}20%{opacity:1}100%{opacity:0}}
  #align-chrono{position:fixed;z-index:10001;pointer-events:none;display:none;flex-direction:column;align-items:center;
    padding:8px 18px;border-radius:16px;background:rgba(0,0,0,.72);border:3px solid #ffd400;color:#ffd400;
    font:900 46px/1 system-ui,Segoe UI,Arial,sans-serif;text-align:center}
  #align-chrono small{font:800 17px/1.3 system-ui,Segoe UI,Arial,sans-serif;color:#fff}
  #align-chrono.urgent{border-color:#ff2d95;color:#ff2d95;animation:showBat .4s ease-in-out infinite alternate}
  .align-coeur{position:fixed;z-index:9997;pointer-events:none;font-size:38px;animation:coeurMonte 3.2s ease-out forwards}
  @keyframes coeurMonte{0%{opacity:0;transform:translate(0,0) scale(.5)}15%{opacity:1}
    100%{opacity:0;transform:translate(var(--dx),-340px) scale(1.3) rotate(var(--rot))}}`;
  document.head.appendChild(cssShow);
  const show = document.createElement('div'); show.id = 'align-show'; document.body.appendChild(show);
  const cadre = document.createElement('div'); cadre.id = 'align-cadre'; document.body.appendChild(cadre);
  const chrono = document.createElement('div'); chrono.id = 'align-chrono'; document.body.appendChild(chrono);

  function nomMarche() {
    const s = String((chart() && chart().symbol()) || '');
    return /BTC/i.test(s) ? '🟠 BTC' : /XAU|GOLD/i.test(s) ? '🥇 GOLD' : /NAS|NQ|US100/i.test(s) ? '🟣 NASDAQ' : '📊 ' + s.split(':').pop();
  }
  function barres(n) {
    try {
      const b = chart()._chartWidget.model().mainSeries().bars(), fin = b.lastIndex(), out = [];
      for (let i = Math.max(b.firstIndex(), fin - (n || 60) + 1); i <= fin; i++) { const v = b.valueAt(i); if (v) out.push(v); }
      return out;                                   // [temps, ouverture, haut, bas, clôture, volume]
    } catch (e) { return []; }
  }
  function pop(emo, texte, sens) {
    try {
      const r = zoneGraphique();
      show.className = sens === -1 ? 'bas' : sens === 1 ? 'haut' : 'neutre';
      show.innerHTML = '<span class="emo">' + esc(emo) + '</span><span>' + esc(texte) + '</span>';
      show.style.left = (r.left + r.width / 2 - 35) + 'px'; show.style.top = (r.top + 96) + 'px';
      void show.offsetWidth; show.classList.add('go');
      clearTimeout(pop.t); pop.t = setTimeout(() => show.classList.remove('go'), 2900);
    } catch (e) {}
  }
  function lueur(sens) {
    try {
      const r = zoneGraphique(), col = sens === -1 ? '#ff1744' : sens === 1 ? '#00e676' : '#ff2d95';
      Object.assign(cadre.style, { left: r.left + 'px', top: r.top + 'px', width: (r.width - 70) + 'px', height: (r.height || 600) + 'px',
        boxShadow: 'inset 0 0 60px 12px ' + col, border: '4px solid ' + col });
      cadre.classList.remove('go'); void cadre.offsetWidth; cadre.classList.add('go');
    } catch (e) {}
  }
  function coeurs(n, liste) {
    try {
      const r = zoneGraphique(), em = liste || ['❤️', '🔥', '🚀', '💜', '💙', '👆'];
      for (let i = 0; i < (n || 10); i++) setTimeout(() => {
        const e = document.createElement('span'); e.className = 'align-coeur'; e.textContent = em[(Math.random() * em.length) | 0];
        e.style.left = (r.left + r.width - 150 - Math.random() * 90) + 'px'; e.style.top = (r.top + (r.height || 600) * 0.62) + 'px';
        e.style.setProperty('--dx', (Math.random() * 120 - 60) + 'px'); e.style.setProperty('--rot', (Math.random() * 60 - 30) + 'deg');
        document.body.appendChild(e); setTimeout(() => e.remove(), 3400);
      }, i * 160);
    } catch (e) {}
  }
  window.__ALIGN_SHOW__ = { pop, lueur, coeurs };
  // une info du spectacle sur la bande : jamais par-dessus une vraie info du bot, et pas plus d'une par minute
  let dernierShow = 0;
  function bandeShow(txt) {
    if (occupe || file.length || Date.now() - dernierShow < 60000) return false;
    dernierShow = Date.now(); montrer(txt, false, 1); return true;
  }
  const deja = {};
  function uneFois(cle) { if (deja[cle]) return false; deja[cle] = 1; return true; }
  const PHRASES = {
    accel: [['💥', 'ÇA ACCÉLÈRE', ' accélère • jusqu\'où ? la suite en temps réel : lien en bio 🎁']],
    casseBas: [['🚨', 'ÇA CASSE !', ' casse le dernier plus bas 📉 • ça peut couler encore… infos en temps réel : lien en bio 🎁']],
    casseHaut: [['🚀', 'ÇA CASSE !', ' casse le dernier plus haut 📈 • ça peut décoller… infos en temps réel : lien en bio 🎁']],
    volume: [['🐋', 'LES BALEINES BOUGENT', ' : gros volume 👀 quelque chose se prépare • lien en bio 🎁']],
    hausse: ['📈 {m} veut remonter… jusqu\'où ? le coach le sait : lien en bio 🎁',
             '🟢 {m} reprend des forces 💪 le marché pourrait remonter • plus d\'infos : lien en bio 🎁',
             '🚀 Les acheteurs reviennent sur {m} 👀 la suite en temps réel : lien en bio 🎁'],
    baisse: ['📉 {m} sous pression… va-t-il couler ? réponse en temps réel : lien en bio 🎁',
             '🔴 Les vendeurs tiennent {m} 😬 ça peut encore descendre • plus d\'infos : lien en bio 🎁',
             '🌊 {m} glisse… le coach surveille chaque bougie : lien en bio 🎁'],
    range: ['😴 {m} se compresse… avant l\'explosion ? 💥 tiens-toi prêt • lien en bio 🎁',
            '🧲 {m} hésite… la prochaine clôture peut tout décider ⏱ lien en bio 🎁']
  };
  let tendN = 0, derniereTend = Date.now();
  function regarder() {
    try {
      if (retour) return;                                   // un abonné a la main : on ne parle pas par-dessus
      const B = barres(40); if (B.length < 25) return;
      const cur = B[B.length - 1], prev = B.slice(-21, -1), m = nomMarche();
      const moyR = prev.reduce((a, x) => a + (x[2] - x[3]), 0) / prev.length || 1;
      const moyV = prev.reduce((a, x) => a + (x[5] || 0), 0) / prev.length || 0;
      const corps = cur[4] - cur[1], sens = corps < 0 ? -1 : 1, id = m + cur[0];
      // 1) bougie qui accélère (corps > 1,6× la taille moyenne) : explosion visuelle + lueur rouge/verte
      if (Math.abs(corps) > 1.6 * moyR && uneFois('acc' + id)) {
        pop(sens === -1 ? '📉' : '📈', PHRASES.accel[0][1] + (sens === -1 ? ' ⬇️' : ' ⬆️'), sens); lueur(sens);
        bandeShow((sens === -1 ? '📉 ' : '📈 ') + m + PHRASES.accel[0][2]);
        return;
      }
      // 2) cassure du dernier plus haut / plus bas (20 bougies) : on le montre sans donner le prix
      const hh = Math.max(...prev.map(x => x[2])), ll = Math.min(...prev.map(x => x[3]));
      if (cur[4] < ll && uneFois('cb' + id)) { pop('🚨', 'ÇA CASSE ⬇️', -1); lueur(-1); bandeShow('🚨 ' + m + PHRASES.casseBas[0][2]); return; }
      if (cur[4] > hh && uneFois('ch' + id)) { pop('🚀', 'ÇA CASSE ⬆️', 1); lueur(1); bandeShow('🚀 ' + m + PHRASES.casseHaut[0][2]); return; }
      // 3) gros volume
      if (moyV > 0 && (cur[5] || 0) > 2.5 * moyV && uneFois('vol' + id)) { pop('🐋', 'GROS VOLUME', 0); coeurs(8, ['🐋', '💰', '👀']); bandeShow('🐋 ' + m + PHRASES.volume[0][2]); return; }
      // 4) toutes les ~7 min : la bande dit où le marché a l'air d'aller (sans prix) et renvoie vers le lien en bio
      if (Date.now() - derniereTend > 7 * 60000) {
        const c10 = B.slice(-10).map(x => x[4]), pente = (c10[9] - c10[0]) / moyR, larg = (Math.max(...B.slice(-10).map(x => x[2])) - Math.min(...B.slice(-10).map(x => x[3]))) / moyR;
        const L = larg < 3.2 ? PHRASES.range : pente > 1.2 ? PHRASES.hausse : pente < -1.2 ? PHRASES.baisse : PHRASES.range;
        if (bandeShow(L[tendN++ % L.length].replace('{m}', m))) { derniereTend = Date.now(); coeurs(6); }
      }
    } catch (e) {}
  }
  setTimeout(() => { barres(40).slice(-1).forEach(b => { const k = nomMarche() + b[0]; ['acc', 'cb', 'ch', 'vol'].forEach(p => deja[p + k] = 1); }); }, 1500);  // rien au démarrage
  const regardT = setInterval(regarder, 5000);

  // compte à rebours de la clôture 15 min : les 45 dernières secondes, gros chrono + « ça va se décider »
  const chronoT = setInterval(() => { try {
    const s = Math.floor(Date.now() / 1000), reste = 900 - (s % 900), r = zoneGraphique();
    if (reste <= 45 && !retour) {
      chrono.style.display = 'flex'; chrono.classList.toggle('urgent', reste <= 10);
      chrono.style.left = (r.left + 18) + 'px'; chrono.style.top = (r.top + 96) + 'px';
      chrono.innerHTML = '0:' + String(reste).padStart(2, '0') + '<small>⏱ CLÔTURE 15 MIN<br>ça va se décider 👀</small>';
      if (reste === 45 && uneFois('cl' + s)) bandeShow('⏱ Clôture 15 min dans 45 s sur ' + nomMarche() + ' • c\'est elle qui décide 👀 • la suite en temps réel : lien en bio 🎁');
    } else if (chrono.style.display !== 'none') {
      chrono.style.display = 'none';
      const b = barres(2)[0];                              // la bougie qui vient de clôturer
      if (b && reste > 880) { const v = b[4] >= b[1] ? 1 : -1; pop(v === 1 ? '🟢' : '🔴', 'BOUGIE CLÔTURÉE ' + (v === 1 ? '⬆️' : '⬇️'), v); }
    }
  } catch (e) {} }, 1000);
  // de temps en temps des cœurs qui montent : « tapote l'écran »
  const coeurT = setInterval(() => { if (!retour) coeurs(10); }, 100000);

  window.__ALIGN_BANDE__ = {
    version: VERSION, recu,
    stop() { cancelAnimationFrame(raf); clearInterval(suivi); clearInterval(astuceT); clearInterval(regardT); clearInterval(chronoT); clearInterval(coeurT);
      [show, cadre, chrono, cssShow].forEach(x => { try { x.remove(); } catch (e) {} }); document.querySelectorAll('.align-coeur').forEach(x => x.remove()); obs.disconnect(); try { es.close(); } catch (e) {} bande.remove(); css.remove(); }
  };
})();
