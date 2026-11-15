// ==UserScript==
// @name         ALIGN Bande Live
// @namespace    align-live
// @version      7.4
// @description  Bande du live ALIGN sur TradingView : messages Telegram, bulles, télécommande 15 s, infobulles roses
// @match        https://*.tradingview.com/chart/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==
(function () {
  'use strict';
  if (window.__ALIGN_BANDE__) { try { window.__ALIGN_BANDE__.stop(); } catch (e) {} }
  const VERSION = '8.4';  // v8.4 : ligne du bas du tableau revenue à sa couleur d'origine (v8.2), texte 13 px ; v8.3  // v8.3 : (étiquettes posées par-dessus désactivées, à faire dans le Pine), ligne du bas du tableau en couleur neutre, plus grosse, « tu peux rentrer ? 👍 » ; v8.2  // v8.2 : prix cachés dans la ligne du bas du tableau (❓ + lien en bio) ; v8.1  // v8.1 : les pastilles de motivation descendent juste au-dessus du tableau des unités (petit écran TikTok), les infos du marché restent collées au prix ; v8.0  // v8.0 : boost du live tout de suite + feu d'artifice, « t'as envie de rentrer là ? », on fait commenter (ça monte ou ça descend ?) ; v7.9  // v7.9 : une fenêtre TradingView ouverte passe DEVANT la bande (on peut toujours la fermer) + la pub « sans publicité » se ferme toute seule ; v7.8  // v7.8 : la pastille suit la langue de la bande (FR/EN) ; v7.7  // v7.7 : pastilles sur 2 lignes collées au prix, animations +12 %, « tapote au lieu de regarder », plus de doublons après réinjection ; v7.6  // v7.6 : le marché PARLE (bulle près du prix, ping sur le prix, texte qui s'écrit), plus de « péter / explosion / branche » ; v7.5 : zones cliquables, plus de contre-sens, pastilles côté prix (haut si ça baisse, bas si ça monte), « connecté depuis ton portable »
  // v7.2 : bandes du haut un peu plus grosses (86 px, texte 40 px)
  const SUJET = 'align-live-2a4bccafd9548d93';
  const BASE = [
    '🟢 LIVE ALIGN 24/7 • BTC • GOLD • NASDAQ',
    '👉 ABONNE-TOI • PARTAGE • TAPOTE L\'ÉCRAN',
    '🔗 LIEN EN BIO : COACH EN DIRECT',
    '📲 CONNECTÉ AU MARCHÉ EN TEMPS RÉEL DEPUIS TON PORTABLE • chaque bougie expliquée en direct • lien en bio 🎁',
    '🧭 CHEZ ALIGN ON NE VA JAMAIS CONTRE LA TENDANCE • on suit le marché, on ne le combat pas 💪',
    '⚠️ CECI N\'EST PAS UN CONSEIL EN INVESTISSEMENT • fais tes propres recherches (DYOR)',
    '⚠️ NOT FINANCIAL ADVICE • do your own research (DYOR)',
    '📲 Le coach ALIGN en direct • lien en bio 🎁 gratuit',
    '📲 RESTE CONNECTÉ • CONNECTE-TOI : LIEN EN BIO 🎁',
    '🎁 TOUTES LES POSITIONS SONT GRATUITES • les annonces arrivent en temps réel sur ton portable • lien en bio',   // v7.6 (demande d'Adel)
    '📢 ANNONCE À VENIR… 😏 tu veux savoir avant que ça parte ? • lien en bio 🎁',
    '⚡ DÉPÊCHE-TOI : UNE ENTRÉE SE PRÉPARE • ABONNE-TOI, LIEN EN BIO • LES RETARDATAIRES ONT TOUJOURS TORT 😉',
    '🔔 ACTIVE TES NOTIFICATIONS • lien en bio : on te prévient dès que le marché se prépare 🎁',
    '📩 VA DANS LE LIEN EN BIO • tu reçois l\'alerte en temps réel sur le marché, avec les détails et les news 🎁',   // v7.3 : l'avantage de venir chez nous
    '⚠️ Le trading comporte un risque élevé de perte en capital • Contenu à caractère informatif et éducatif uniquement, qui ne constitue ni un conseil en investissement ni une recommandation personnalisée • Les performances passées ne préjugent pas des performances futures',
    // v6.4 : la même bande en anglais (FR + EN pour toucher tout le monde)
    '👉 FOLLOW • SHARE • TAP THE SCREEN',
    '🔗 LINK IN BIO: LIVE COACH',
    '📲 STAY CONNECTED • CONNECT: LINK IN BIO 🎁',
    '🎁 ALL POSITIONS ARE FREE • announcements land in real time on your phone • link in bio',
    '📢 ANNOUNCEMENT COMING… 😏 want to know before it moves? • link in bio 🎁',
    '⚡ HURRY: AN ENTRY IS GETTING READY • FOLLOW, LINK IN BIO • LATECOMERS ARE ALWAYS WRONG 😉',
    '📩 GO TO THE LINK IN BIO • get real-time market alerts with the details and the news 🎁',
    '🔔 TURN ON YOUR NOTIFICATIONS • link in bio: we\'ll tell you as soon as the market gets ready 🎁',
    '📲 CONNECTED TO THE MARKET IN REAL TIME FROM YOUR PHONE • every candle explained live • link in bio 🎁',
    '🧭 AT ALIGN WE NEVER TRADE AGAINST THE TREND • we follow the market, we don\'t fight it 💪',
    '⚠️ Trading involves a high risk of capital loss • Informational and educational content only, it is neither investment advice nor a personalised recommendation • Past performance is not indicative of future results'
  ];
  // v6.4 : traduction anglaise des messages de la bande (chaque info passe en FR puis en EN)
  const EN = [
    ['pas de panique • le marché respire, il est comme vous 😅 • patience, la suite en temps réel', 'don\'t panic • the market is breathing, just like you 😅 • patience, what\'s next live'],
    ['le marché prépare quelque chose', 'the market is preparing something'], ['la suite en temps réel', 'what\'s next, live'],
    ['infos en temps réel', 'live info'], ['plus d\'infos en temps réel', 'more live info'], ['plus d\'infos', 'more info'],
    ['connecte-toi au marché depuis ton portable', 'connect to the market from your phone'], ['branche-toi au marché', 'plug into the market'],
    ['Ton portable connecté au marché en temps réel : chaque bougie expliquée en direct', 'Your phone connected to the market in real time: every candle explained live'],
    ['Connecté au marché depuis ton portable : le coach lit chaque bougie avec toi', 'Connected to the market from your phone: the coach reads every candle with you'],
    ['CHANGEMENT DE PROGRAMME', 'CHANGE OF PLAN'], ['le marché a changé d\'avis', 'the market changed its mind'], ['on suit le marché, on ne le combat pas', 'we follow the market, we don\'t fight it'], ['lien en bio', 'link in bio'], ['abonne-toi, partage', 'follow, share'],
    ['abonne-toi', 'follow'], ['partage', 'share'], ['la team', 'team'], ['pas de panique', 'don\'t panic'], ['pourquoi ?', 'why?'],
    ['COMPTE À REBOURS sur', 'COUNTDOWN on'], ['GROSSE DISTRIBUTION', 'BIG SELL-OFF'], ['GROSSE ACCUMULATION', 'BIG ACCUMULATION'],
    ['min max', 'min max'], ['dans', 'in'], ['ÇA ACCÉLÈRE', 'IT\'S SPEEDING UP'], ['jusqu\'où ?', 'how far?'], ['ÇA CASSE', 'BREAKOUT'],
    ['dernier plus bas cassé', 'last low broken'], ['dernier plus haut cassé', 'last high broken'], ['ça peut couler encore…', 'it can drop further…'],
    ['ça peut décoller…', 'it can take off…'], ['LES BALEINES BOUGENT sur', 'WHALES ARE MOVING on'], ['gros volume', 'big volume'],
    ['quelque chose se prépare', 'something is brewing'], ['LA PRESSION MONTE sur', 'PRESSURE IS BUILDING on'], ['MANIPULATION sur', 'MANIPULATION on'],
    ['les gros piègent les acheteurs… la belle distribution', 'big players trap the buyers… the sell-off'],
    ['les gros piègent les vendeurs… le rechargement', 'big players trap the sellers… the reload'],
    ['ANNONCÉ !', 'CALLED IT!'], [' a coulé ', ' dropped '], [' a décollé ', ' took off '], ['la team ALIGN l\'a vu venir', 'team ALIGN saw it coming'],
    ['REBOND sur une ligne clé', 'BOUNCE on a key level'], ['arrive sur une zone clé', 'reaches a key zone'], ['Zone clé du marché', 'Key market zone'],
    ['ce qu\'elle annonce', 'what it means'],
    ['À toi de jouer :', 'Your turn:'], ['va MONTER 📈 ou DESCENDRE 📉 ? Écris-le en commentaire, on verra qui a raison 😏', 'going UP 📈 or DOWN 📉? Write it in the comments, we\'ll see who\'s right 😏'],
    ['Sondage express :', 'Quick poll:'], ['⬆️ ou ⬇️ dans 15 min ? Commente « haut » ou « bas »', '⬆️ or ⬇️ in 15 min? Comment "up" or "down"'],
    ['Les meilleurs pronostics en commentaire…', 'Best predictions in the comments…'], ['continue ou retrace ? Montre que t\'as le flair', 'keeps going or pulls back? Show your instinct'],
    ['Celui qui devine la prochaine bougie de', 'Whoever guesses the next candle of'], ['gagne… notre respect éternel', 'wins… our eternal respect'], ['commente !', 'comment!'],
    ['touche son dernier plus haut', 'hits its last high'], ['touche son dernier plus bas', 'hits its last low'], ['t\'as envie de rentrer là ?', 'tempted to jump in here?'],
    ['Ça continue ou ça retrace ?', 'Keeps going or pulls back?'], ['dis-le en commentaire', 'say it in the comments'], ['le scénario complet est déjà prêt', 'the full scenario is already set'],
    ['MERCI', 'THANKS'], ['BOOSTE LE LIVE', 'BOOSTS THE LIVE'], ['ABONNE-TOI • PARTAGE', 'FOLLOW • SHARE'],
    ['Au lieu de regarder sans rien faire… le marché n\'a pas encore de point d\'entrée 😅 tapote l\'écran pour le réveiller', 'Instead of just watching… the market has no entry point yet 😅 tap the screen to wake it up'],
    ['Pas d\'entrée pour l\'instant : la team patiente… toi tu tapotes, nous on surveille', 'No entry for now: the team waits… you tap, we watch'], ['Zone clé : le marché pourrait y souffler… ce qu\'il prépare', 'Key zone: the market may pause here… what\'s next'],
    ['Zone clé : le marché teste la patience de tout le monde…', 'Key zone: the market is testing everyone\'s patience…'],
    ['BOUGIE 15 MIN CLÔTURÉE', '15 MIN CANDLE CLOSED'], ['Clôture 15 min dans', '15 min close in'], ['c\'est elle qui décide', 'it decides everything'],
    ['veut remonter… jusqu\'où ? le coach le sait', 'wants to bounce… how far? the coach knows'], ['reprend des forces', 'is regaining strength'],
    ['le marché pourrait remonter', 'the market could go up'], ['Les acheteurs reviennent sur', 'Buyers are back on'],
    ['sous pression… va-t-il couler ? réponse en temps réel', 'under pressure… will it drop? live answer'],
    ['Les vendeurs tiennent', 'Sellers are holding'], ['ça peut encore descendre', 'it can still go down'],
    ['glisse… le coach surveille chaque bougie', 'is sliding… the coach watches every candle'],
    ['se compresse… avant le gros mouvement ? ⚡ tiens-toi prêt', 'is squeezing… before the big move? ⚡ get ready'],
    ['hésite… la prochaine clôture peut tout décider', 'hesitates… the next close can decide everything'],
    ['est posé sur une zone clé en bas', 'sits on a key zone below'], ['rebond ou cassure ?', 'bounce or break?'],
    ['teste le bas de sa zone… les acheteurs vont-ils tenir ?', 'tests the bottom of its zone… will buyers hold?'],
    ['touche le haut de sa zone', 'touches the top of its zone'], ['cassure ou rejet ?', 'break or rejection?'],
    ['bute sous un plafond… les vendeurs vont-ils frapper ?', 'is stuck under a ceiling… will sellers strike?'],
    ['au milieu de sa zone : il cherche sa direction… le coach te dit quand ça part', 'in the middle of its zone: looking for direction… the coach tells you when it moves'],
    ['en équilibre : acheteurs et vendeurs se regardent… qui va craquer ?', 'in balance: buyers and sellers stare each other down… who breaks first?'],
    ['Le lien en bio = ton câble branché sur le marché : chaque bougie expliquée en direct', 'The link in bio = your cable plugged into the market: every candle explained live'],
    ['Comme si tu étais connecté au marché : le coach lit chaque bougie avec toi', 'Like being wired to the market: the coach reads every candle with you'],
    ['Tu vois les bougies, le coach te dit ce qu\'elles préparent', 'You see the candles, the coach tells you what they\'re preparing'],
    ['Ressens le marché en direct : pression, pièges, accélérations… tout est dans le', 'Feel the market live: pressure, traps, accelerations… it\'s all in the'],
    ['objectif TOUCHÉ', 'target HIT'], ['On protège', 'We protect'], ['risque zéro', 'zero risk'], ['ÇA ENCAISSE', 'CASHING IN'],
    ['PASSE À L\'ACTION sur', 'TAKES ACTION on'], ['rejoint la team ALIGN, viens nous rejoindre', 'joined team ALIGN, come join us'],
    ['prépare-toi', 'get ready'], ['ça peut couler', 'it may drop'], ['ça peut décoller', 'it may take off'], ['verdict dans', 'verdict in'],
    ['Astuce', 'Tip'], ['Le trading comporte un risque de perte', 'Trading involves a risk of loss'], ['gratuit', 'free'], ['en direct', 'live'],
    ['Bravo à ceux qui ont suivi', 'Well done to everyone who followed'], ['Abonne-toi', 'Follow'], ['ABONNE-TOI', 'FOLLOW'],
    ['protection touché', 'protection hit'], ['on coupe petit, on va se refaire', 'we cut small, we\'ll bounce back'],
    ['objectif frôlé à un cheveu', 'target missed by a hair'], ['petit recul, on garde le cap', 'small pullback, we stay on course'],
    ['ça devrait reprendre', 'it should resume'], ['clôture dans', 'close in'], ['le coach l\'a déjà annoncé', 'the coach already called it'],
    ['JEU : tapote l\'écran si tu penses que', 'GAME: tap the screen if you think'], ['va couler', 'will drop'], ['va monter', 'will rise'],
    ['réponse dans', 'answer in'], ['les niveaux en privé', 'levels in private'], ['Le coach ALIGN', 'The ALIGN coach'],
    ['risque de perte, pas un conseil', 'risk of loss, not advice'],
    ['Ceci n\'est pas un conseil en investissement, fais tes propres recherches (DYOR)', 'This is not financial advice, do your own research (DYOR)'],
    ['risque de perte', 'risk of loss'],
    ['ATTENTION LA FEINTE sur', 'WATCH THE FAKE-OUT on'],
    ['le marché fait semblant de remonter… beaucoup vont acheter trop tôt et y laisser des plumes', 'the market is faking a bounce… many will buy too early and lose feathers'],
    ['le marché fait semblant de chuter… beaucoup vont vendre trop tôt et y laisser des plumes', 'the market is faking a drop… many will sell too early and lose feathers'],
    ['Ne te fais pas piéger', 'Don\'t get trapped'], ['ne cours pas après la bougie', 'don\'t chase the candle'],
    ['les gros adorent ce genre de piège', 'big players love this kind of trap'], ['qui va mordre à l\'hameçon ?', 'who\'s going to take the bait?'],
    ['Pfff… on s\'ennuie,', 'Ugh… so boring,'], ['est trop calme', 'is way too calm'], ['pense à tapoter l\'écran', 'remember to tap the screen'],
    ['et à t\'abonner', 'and follow'], ['Marché ennuyant sur', 'Boring market on'], ['allez, tapote l\'écran pour le réveiller', 'come on, tap the screen to wake it up'],
    ['et abonne-toi', 'and follow'],
    ['est tout calme… va te faire un café tranquille, on te prévient quand ça bouge', 'is super calm… go grab a coffee, we\'ll ping you when it moves'],
    ['Petit-déj time :', 'Breakfast time:'], ['se réveille doucement… le coach veille pour toi', 'is slowly waking up… the coach is watching for you'],
    ['fait la sieste… va manger un bout, le coach surveille pour toi', 'is napping… go grab a bite, the coach is watching for you'],
    ['Pause déj :', 'Lunch break:'], ['bouge pas d\'un poil… on te ping dès que ça part', 'isn\'t moving an inch… we\'ll ping you when it goes'],
    ['chill grave… prends une pause, le marché te fera signe', 'is chilling hard… take a break, the market will let you know'],
    ['Café de l\'aprèm ?', 'Afternoon coffee?'], ['est en mode tranquille… le coach reste connecté', 'is in chill mode… the coach stays connected'],
    ['est calme ce soir… va dîner, le coach garde un œil', 'is calm tonight… go have dinner, the coach keeps an eye on it'],
    ['Soirée chill :', 'Chill evening:'], ['ne fait rien de fou… on te prévient si ça s\'énerve', 'isn\'t doing anything crazy… we\'ll tell you if it heats up'],
    ['Il est tard et', 'It\'s late and'], ['dort à moitié… va te reposer, le coach veille', 'is half asleep… go get some rest, the coach is on watch'],
    ['roupille… recharge les batteries, le marché sera encore là demain', 'is snoozing… recharge your batteries, the market will still be here tomorrow'],
    ['sur ', 'on ']
  ].sort((a, b) => b[0].length - a[0].length);
  function enAnglais(t) { let x = String(t); for (const [fr, en] of EN) x = x.split(fr).join(en); return x; }
  const DUREE_MAIN = 15000, DUREE_MSG = 8000;

  // ───── style ─────
  const css = document.createElement('style');
  css.id = 'align-bande-css';
  css.textContent = `
  #align-bande{position:fixed;z-index:9999;height:86px;overflow:hidden;pointer-events:none;
    background:linear-gradient(90deg,#ff2d95,#8a2be2 50%,#1e90ff);border-radius:0 0 10px 10px;
    box-shadow:0 4px 14px rgba(0,0,0,.5);font:900 40px/86px system-ui,Segoe UI,Arial,sans-serif;color:#fff;
    text-shadow:0 2px 3px rgba(0,0,0,.45);transition:opacity .2s}
  #align-bande .piste{position:absolute;white-space:nowrap;will-change:transform}
  #align-bande .piste span{margin-right:70px}
  #align-bande .flash{position:absolute;inset:0;display:none;align-items:center;justify-content:flex-start;
    padding:0;white-space:nowrap;overflow:hidden;font:900 40px/86px system-ui,Segoe UI,Arial,sans-serif;
    background:linear-gradient(90deg,#ff4fa3,#ffd400);color:#000;text-shadow:none;text-transform:uppercase}   /* v7.4 : même rendu que la bande d'accueil (majuscules, 86 px, 40 px) */
  /* v5.4 : même taille d'écriture que la bande normale, une couleur par type d'info (plus de bande blanche) */
  #align-bande .flash.bulle{background:linear-gradient(90deg,#ff7ab8,#ffb3d6);color:#000}
  #align-bande .flash.tp{background:linear-gradient(90deg,#00c853,#ffd400);color:#000}
  #align-bande .flash.sl{background:linear-gradient(90deg,#ff1744,#ff8a65);color:#fff;text-shadow:0 2px 3px rgba(0,0,0,.45)}
  #align-bande .flash.membre{background:linear-gradient(90deg,#8a2be2,#ff2d95);color:#fff;text-shadow:0 2px 3px rgba(0,0,0,.45)}
  #align-bande .flash.proche{background:linear-gradient(90deg,#1e90ff,#00e5ff);color:#000}
  #align-bande .flash.bas{background:linear-gradient(90deg,#ff1744,#ff6d00);color:#fff;text-shadow:0 2px 3px rgba(0,0,0,.45)}
  #align-bande .flash.haut{background:linear-gradient(90deg,#00c853,#00e5ff);color:#000}
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
  // v6.7 : TikTok ≠ YouTube. TikTok = « tapote l'écran », « lien en bio » ; YouTube = « like 👍 », « active la cloche 🔔 »,
  // « lien en description ». Réglage gardé dans le navigateur ; « les deux » = un texte qui marche partout (un seul écran filmé).
  let PLATEFORME = 'tiktok';
  try { PLATEFORME = localStorage.getItem('alignPlateforme') || 'tiktok'; } catch (e) {}
  function plateforme(t) {
    t = String(t);
    if (PLATEFORME === 'youtube') return t
      .replace(/TAPOTE L'ÉCRAN/g, 'LIKE 👍 • ACTIVE LA CLOCHE 🔔').replace(/tapote(r)? (sur )?l'écran/gi, 'mettre un like 👍')
      .replace(/TAP THE SCREEN/g, 'LIKE 👍 • TURN ON THE BELL 🔔').replace(/tap the screen/gi, 'hit like 👍')
      .replace(/LIEN EN BIO/g, 'LIEN EN DESCRIPTION').replace(/lien en bio/gi, 'lien en description')
      .replace(/LINK IN BIO/g, 'LINK IN DESCRIPTION').replace(/link in bio/gi, 'link in description');
    if (PLATEFORME === 'les2') return t
      .replace(/TAPOTE L'ÉCRAN/g, 'TAPOTE / LIKE 👍').replace(/tapote(r)? (sur )?l'écran/gi, 'tapoter / liker 👍')
      .replace(/TAP THE SCREEN/g, 'TAP / LIKE 👍').replace(/tap the screen/gi, 'tap / like 👍')
      .replace(/LIEN EN BIO/g, 'LIEN EN BIO / DESCRIPTION').replace(/lien en bio/gi, 'lien en bio / description')
      .replace(/LINK IN BIO/g, 'LINK IN BIO / DESCRIPTION').replace(/link in bio/gi, 'link in bio / description');
    return t;
  }
  function remplir() {
    const v = vueTxt();
    const iEN = BASE.indexOf('👉 FOLLOW • SHARE • TAP THE SCREEN');   // v7.8 : on repère les phrases anglaises de la bande d'accueil
    const items = (v ? [[v, 0]] : []).concat(BASE.map((t, i) => [t, iEN >= 0 && i >= iEN]), extra.slice(-3).map(t => [t, 0]));
    const html = items.map(([t, en]) => '<span' + (en ? ' class="en"' : '') + '>' + esc(plateforme(t)) + '</span>').join('');
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
    const axe = 0;     // v7.6 (demande d'Adel) : la bande couvre aussi l'échelle de prix en haut (plus propre)
    const marge = 40;  // à gauche : un peu plus large (v5.2) tout en restant dans la zone filmée par TikTok
    bande.style.left = (r.left + marge) + 'px';
    bande.style.top = r.top + 'px';
    bande.style.width = Math.max(200, r.width - axe - marge) + 'px';
    const dt = Math.min(64, now - last); last = now;
    x -= dt * 0.09;
    const demi = piste.scrollWidth / 2;
    if (demi > 0 && -x >= demi) x += demi;
    piste.style.transform = 'translateX(' + x + 'px)';
    // v7.9 (demande d'Adel : « je n'arrive pas à fermer la fenêtre à cause de la bande ») : toutes les 0,4 s,
    // si une fenêtre / un menu TradingView est ouvert, la bande et les pastilles se cachent ; la pub « Go Pro » est fermée toute seule
    if (now - (anim.vu || 0) > 400) { anim.vu = now; try {
      const pub = document.querySelector('[data-dialog-name="gopro"] button[aria-label="Fermeture"]'); if (pub) pub.click();
      document.documentElement.classList.toggle('align-cache', !!document.querySelector('[role="dialog"], [data-dialog-name], [data-name="menu-inner"]'));
    } catch (e) {} }
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
  // v6.3 (règle d'Adel) : AUCUN chiffre de prix sur la bande — on intrigue, le détail est dans le lien en bio
  // v6.3 : ni prix, ni ENTRÉE / SL / TP / stop sur la bande (risque TikTok + on garde le détail pour le lien en bio)
  function sansPrix(t) { return String(t)
    .replace(/ENTRE EN POSITION/gi, 'PASSE À L\'ACTION').replace(/SL (à|a) l['’]entrée/gi, 'risque zéro').replace(/l['’]entrée/gi, 'la zone').replace(/\bTP\s?\d?\b/g, 'objectif').replace(/\bSL\b|\bstop\b/gi, 'protection')
    .replace(/\bENTRÉE\b|\bentrée\b/g, 'zone').replace(/\(ligne (bleue|rouge|jaune)\)/gi, '').replace(/\d{1,3}(?:[\s\u202f\u00a0]\d{3})+(?:[.,]\d+)?|\d{3,}(?:[.,]\d+)?/g, '').replace(/\(\s*\)|:\s*(?=•)/g, '').replace(/\s{2,}/g, ' ').trim(); }
  function montrer(texte, bulle, fois, couleur, devant) {
    const g = couleur || genre(texte);
    texte = sansPrix(texte);
    const urgent = g && g !== 'proche' ? 1 : 0;
    // v6.4 : chaque info passe en français PUIS en anglais (au moins 2 passages)
    // v6.5 (règle d'Adel) : chaque info rappelle le risque, en français puis en anglais
    if (!/risque|risk/i.test(texte)) texte += ' • ⚠️ Ceci n\'est pas un conseil en investissement, fais tes propres recherches (DYOR) • risque de perte';
    // v7.3 (règle d'Adel, 15/11) : chaque info passe 2 fois en français PUIS 2 fois en anglais
    const nPass = Math.max(4, 2 * (fois || 1)), items = []; for (let i = 0; i < nPass; i++) items.push({ texte: (i >= nPass / 2 ? '🇬🇧 ' : '🇫🇷 ') + plateforme(i >= nPass / 2 ? enAnglais(texte) : texte), bulle, g, en: i >= nPass / 2 });   // v7.4 : jamais FR et EN mélangés, drapeau + teinte
    if (devant) { file.splice(0, file.length, ...items, ...file.filter(m => m.g && m.g !== 'proche')); couper(); }   // v7.5 : clic sur une zone = la bande en parle TOUT DE SUITE
    else if (urgent) { let k = 0; while (k < file.length && file[k].g && file[k].g !== 'proche') k++; file.splice(k, 0, ...items); }
    else file.push(...items);
    suivant();
  }
  let animCur = null, timerCur = null;
  function couper() { if (!occupe) return; try { animCur && animCur.cancel(); } catch (e) {} clearTimeout(timerCur); bande.classList.remove('on'); occupe = false; }
  function suivant() {
    if (occupe || !file.length) return;
    occupe = true;
    const m = file.shift();
    flash.innerHTML = '<span>' + esc(m.texte) + '</span>';   // le message défile vite (lisible sur téléphone, même si TikTok coupe les bords)
    flash.className = 'flash' + (m.g ? ' ' + m.g : m.bulle ? ' bulle' : '') + (m.en ? ' en' : '');
    bande.classList.add('on');
    const sp = flash.firstChild, W = bande.clientWidth, w = sp.offsetWidth;
    const dur = Math.max(4000, (W + w) / 0.38);      // v5.4 : plus rapide (info en temps réel), toujours lisible
    animCur = sp.animate([{ transform: 'translateX(' + W + 'px)' }, { transform: 'translateX(' + (-w) + 'px)' }], { duration: dur, easing: 'linear' });
    timerCur = setTimeout(() => { bande.classList.remove('on'); occupe = false; if (!file.length) x = 0; suivant(); }, dur);   // v7.4 : après les infos, la bande d'accueil repart du DÉBUT (en français)
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
  // v5.7 : TP touché = pluie de billets et de pièces sur l'écran, « ÇA ENCAISSE 💰 »
  const cssBillet = document.createElement('style');
  cssBillet.textContent = `.align-billet{position:fixed;z-index:10000;pointer-events:none;font-size:44px;top:-60px;animation:billetTombe var(--t) linear forwards}
  @keyframes billetTombe{0%{transform:translate(0,0) rotate(0)}100%{transform:translate(var(--dx),var(--h)) rotate(var(--rot));opacity:.2}}`;
  document.head.appendChild(cssBillet);
  function pluieBillets(n) {
    try {
      const r = zoneGraphique(), H = (r.height || 700) + 120, em = ['💵', '💰', '💸', '🪙', '💶', '🤑'];
      for (let i = 0; i < (n || 40); i++) setTimeout(() => {
        const e = document.createElement('span'); e.className = 'align-billet'; e.textContent = em[(Math.random() * em.length) | 0];
        e.style.left = (r.left + Math.random() * (r.width - 90)) + 'px'; e.style.top = r.top + 'px';
        e.style.setProperty('--t', (2.2 + Math.random() * 1.6) + 's'); e.style.setProperty('--h', H + 'px');
        e.style.setProperty('--dx', (Math.random() * 120 - 60) + 'px'); e.style.setProperty('--rot', (Math.random() * 720 - 360) + 'deg');
        document.body.appendChild(e); setTimeout(() => e.remove(), 4200);
      }, i * 70);
    } catch (e) {}
  }
  window.__ALIGN_BILLETS__ = pluieBillets;
  // v6.8 (demande d'Adel) : prix sur l'objectif = EXPLOSION D'ARGENT dans le sens du marché
  //   marché qui coule (sens -1) → éclat au niveau du prix puis l'argent retombe en pluie ;
  //   marché qui monte (sens +1) → éclat puis l'argent s'envole vers le haut. Jamais de fusée quand ça coule.
  const cssArgent = document.createElement('style');
  cssArgent.textContent = `.align-argent{position:fixed;z-index:10001;pointer-events:none;font-size:46px;animation:argentVole var(--t) cubic-bezier(.15,.8,.3,1) forwards}
  @keyframes argentVole{0%{transform:translate(0,0) scale(.3) rotate(0);opacity:1}25%{transform:translate(var(--ex),var(--ey)) scale(1.2)}
    100%{transform:translate(var(--dx),var(--dy)) scale(1) rotate(var(--rot));opacity:0}}
  #align-flash-or{position:fixed;inset:0;z-index:9999;pointer-events:none;background:radial-gradient(circle at var(--x) var(--y),rgba(255,215,0,.55),rgba(255,215,0,0) 45%);animation:flashOr 1.2s ease-out forwards}
  @keyframes flashOr{from{opacity:1}to{opacity:0}}`;
  document.head.appendChild(cssArgent);
  function explosionArgent(sens) {
    try {
      const r = zoneGraphique(), x0 = r.left + r.width * 0.72, y0 = r.top + (r.height || 700) * 0.55, em = ['💵', '💰', '💸', '🪙', '💶', '🤑', '💎'];
      const f = document.createElement('div'); f.id = 'align-flash-or'; f.style.setProperty('--x', x0 + 'px'); f.style.setProperty('--y', y0 + 'px');
      document.getElementById('align-flash-or')?.remove(); document.body.appendChild(f); setTimeout(() => f.remove(), 1300);
      for (let i = 0; i < 46; i++) {
        const e = document.createElement('span'); e.className = 'align-argent'; e.textContent = em[i % em.length];
        const a = Math.random() * Math.PI * 2, rr = 60 + Math.random() * 140;
        e.style.left = x0 + 'px'; e.style.top = y0 + 'px';
        e.style.setProperty('--ex', Math.cos(a) * rr + 'px'); e.style.setProperty('--ey', Math.sin(a) * rr + 'px');
        e.style.setProperty('--dx', (Math.cos(a) * rr * 1.6) + 'px');
        e.style.setProperty('--dy', (sens === -1 ? 380 + Math.random() * 260 : -(380 + Math.random() * 260)) + 'px');
        e.style.setProperty('--rot', (Math.random() * 540 - 270) + 'deg'); e.style.setProperty('--t', (2.2 + Math.random() * 1.2) + 's');
        e.style.animationDelay = (Math.random() * 0.25) + 's';
        document.body.appendChild(e); setTimeout(() => e.remove(), 3800);
      }
    } catch (e) {}
  }
  window.__ALIGN_ARGENT__ = explosionArgent;

  function recu(txt) {
    txt = String(txt || '').trim(); if (!txt) return;
    if (txt.startsWith('CMD:plateforme:')) {          // le bot peut basculer la bande : tiktok / youtube / les2
      const v = txt.split(':')[2]; if (['tiktok', 'youtube', 'les2'].includes(v)) choisirPlateforme(v); return;
    }
    if (txt.startsWith('CMD:')) {
      const p = txt.split(':');               // CMD:sorte:valeur(:avec:deux-points):prénom
      const sorte = p[1], prenom = p[p.length - 1], valeur = p.slice(2, -1).join(':');
      commande(sorte, valeur, prenom); return;
    }
    const bulle = txt.startsWith('BULLE:');
    if (bulle) txt = txt.slice(6).trim();
    // v8.0 (demande d'Adel) : un abonné booste le live depuis le bot → son prénom passe TOUT DE SUITE, avec feu d'artifice et merci
    if (/BOOSTE LE LIVE/i.test(txt)) { const pr = ((txt.match(/MERCI\s+([^!]+)!/i) || [])[1] || '').trim(); montrer(txt, false, 1, 'membre', true); feuArtifice('🚀 MERCI ' + pr.toUpperCase() + ' !'); setTimeout(() => coeurs(1, ['🙏']), 2500); return; }
    if (/TP\d? TOUCH|OBJECTIF FINAL|TP2 TOUCH/i.test(txt)) { feuArtifice(/TP2|FINAL/i.test(txt) ? '🏆 ÇA ENCAISSE !' : '💰 ÇA ENCAISSE !'); pluieBillets(45); }
    if (/\bSL\b[^\n]{0,12}TOUCH|STOP TOUCH/i.test(txt)) setTimeout(() => coeurs(1, ['😢']), 3600);   // v7.1 : smiley triste, on se refait
    montrer(txt, bulle, 2);
    const em = (txt.slice(0, 4).match(/🔮|🧱|🛏/) || [])[0]; if (em) setTimeout(() => coeurs(1, [em]), 1500);   // v7.3 : animation « le graphique parle »
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
  // v6.2 (demande d'Adel) : plus de petite fenêtre au survol : l'explication de la ligne (ENTRÉE, SL, TP, ZONE…)
  // passe dans la BANDE qui défile, 2 fois, avec la couleur de la ligne (TP vert/or, SL rouge, entrée orange)
  const vuTT = {};
  function teaserLigne(t) {
    const c = couleurLigne(t);
    return c === 'tp' ? '👀 Zone clé : le marché pourrait y souffler… ce qu\'il prépare : 📲 lien en bio 🎁'
      : c === 'sl' ? '👀 Zone clé : le marché teste la patience de tout le monde… 📲 lien en bio 🎁'
      : '👀 Zone clé du marché • ce qu\'elle annonce : 📲 lien en bio 🎁';
  }
  function couleurLigne(t) { const h = String(t).slice(0, 28); return /\bSL\b|STOP/.test(h) ? 'sl' : /TP/.test(h) ? 'tp' : /ENTR/.test(h) ? 'alerte' : 'membre'; }   // la couleur suit le DÉBUT du texte (le nom de la ligne)
  function texteLigne(t) { return String(t || '').replace(/[━─]+/g, ' ').replace(/\s*\n+\s*/g, ' • ').replace(/(\s•\s)+/g, ' • ').replace(/^\s*•\s*|\s*•\s*$/g, '').trim(); }
  const obs = new MutationObserver(() => {
    document.querySelectorAll('[class*="common-tooltip-"][class*="common-tooltip--"]').forEach(t => {
      const txt = t.innerText || '';
      if (!/[━]|ENTRÉE|SL|TP|ZONE|RETOURNEMENT|CONFIRMATION/.test(txt)) return;
      t.style.visibility = 'hidden';                 // la fenêtre ne s'affiche plus : tout passe dans la bande
      const ligne = texteLigne(txt), now = Date.now();
      if (ligne && now - (vuTT[ligne] || 0) > 45000 && now - (window.__alignExpl || 0) > 5000) { vuTT[ligne] = now; montrer(teaserLigne(ligne), false, 2, couleurLigne(ligne)); }
    });
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
  #align-chrono small{font:800 17px/1.3 system-ui,Segoe UI,Arial,sans-serif;color:#fff;animation:chronoClignote .8s steps(2,start) infinite}
  @keyframes chronoClignote{to{visibility:hidden}}
  #align-chrono.urgent{border-color:#ff2d95;color:#ff2d95;animation:showBat .4s ease-in-out infinite alternate}
  .align-coeur{position:fixed;z-index:9997;pointer-events:none;font-size:38px;animation:coeurMonte 3.2s ease-out forwards}
  @keyframes coeurMonte{0%{opacity:0;transform:translate(0,0) scale(.5)}15%{opacity:1}
    100%{opacity:0;transform:translate(var(--dx),-340px) scale(1.3) rotate(var(--rot))}}`;
  document.head.appendChild(cssShow);
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
  // v5.5 (demande d'Adel) : le spectacle passe DANS la bande, en défilant comme les autres infos (rouge = ça baisse, vert = ça monte)
  function pop(emo, texte, sens, suite) {
    montrer(emo + ' ' + texte + (suite ? ' • ' + suite : ''), false, 1, sens === -1 ? 'bas' : sens === 1 ? 'haut' : 'membre');
  }
  function lueur(sens) {
    try {
      const r = zoneGraphique(), col = sens === -1 ? '#ff1744' : sens === 1 ? '#00e676' : '#ff2d95';
      Object.assign(cadre.style, { left: r.left + 'px', top: r.top + 'px', width: (r.width - 70) + 'px', height: (r.height || 600) + 'px',
        boxShadow: 'inset 0 0 60px 12px ' + col, border: '4px solid ' + col });
      cadre.classList.remove('go'); void cadre.offsetWidth; cadre.classList.add('go');
    } catch (e) {}
  }
  // v6.9 (demande d'Adel) : plus de petits émojis qui s'envolent (on ne comprend pas ce que c'est) → UNE punchline pro
  // dans une pastille qui monte doucement, en français avec l'anglais dessous. Le contexte choisit la phrase.
  // v7.0 (demande d'Adel) : quand le marché se réveille, on remercie les tapotements avec un petit mot qui fait sourire (jamais 2 fois le même d'affilée) ;
  // quand le prix arrive sur une zone clé : « rentrer ou couper ? » + abonne-toi, lien en bio (jamais de prix ni TP/SL sur la bande).
  const PUNCH = [
    [/💥/, ['🎯 Objectif atteint d\'un coup !', '🎯 Target hit in one go!'], ['🚀 Objectif pris, la team encaisse !', '🚀 Target taken, the team cashes in!'], ['🔥 On a encaissé, c\'est le feu', '🔥 Cashed in, it\'s fire']],
    // v7.4 : position en cours dans le bon sens → on fait sourire (sans prix)
    [/😊/, ['😊 Vous êtes contents ? Je vous demande rien…', '😊 Happy? I ask for nothing…'], ['🙏 Juste tapoter l\'écran et partager', '🙏 Just tap the screen and share'], ['😄 Ça roule pour la team ALIGN', '😄 Smooth ride for team ALIGN']],
    [/😏/, ['😏 Je plains ceux en contre-tendance…', '😏 Feeling sorry for the counter-trend crowd…'], ['💪 On continue dans le sens du marché', '💪 We keep riding the trend'], ['🤭 Pendant ce temps, à contre-sens…', '🤭 Meanwhile, the wrong-way crowd…']],
    // v7.3 : le graphique « parle » quand le coach annonce une zone (🔮 approche, 🧱 / 🛏 contact)
    [/🔮/, ['🔮 Ça va tester !', 'Testing soon!'], ['👀 Zone en approche', 'Zone incoming'], ['🎯 Le marché vise une zone', 'Market eyeing a zone']],
    [/🧱|🛏/, ['🧱 Ça bute !', 'Hitting a wall!'], ['🎯 Zone touchée', 'Zone touched'], ['😮 Contact !', 'Contact!']],
    // v7.1 : objectif de protection touché → un smiley triste qui relativise (jamais le mot SL ni de prix sur la bande)
    [/😢/, ['😢 Pas cette fois…', 'Not this time…'], ['😔 Ça arrive, on se refait 💪', 'It happens, we bounce back 💪'],
      ['🥲 Le marché a gagné cette manche', 'The market won this round'], ['🧠 Le bot apprend de chaque trade', 'The bot learns from every trade'],
      ['🙃 C\'est pas grave, on le récupère', 'No big deal, we\'ll get it back']],
    [/⏰/, ['⏰ Vos tapotements ont réveillé le marché 😄', 'Your taps woke up the market'], ['👆 Continuez de tapoter, ça le réveille 😜', 'Keep tapping, it wakes it up'],
      ['😳 Le marché s\'est réveillé !', 'The market just woke up!'], ['⚡ La team ALIGN a remis le courant 😎', 'Team ALIGN turned the power back on'],
      ['🥁 Ça bouge enfin ! Merci les tapoteurs 😁', 'Finally moving! Thanks, tappers'], ['☕ Le marché a bu son café 😅', 'The market had its coffee'],
      ['🔔 Debout là-dedans ! 🤣', 'Wakey wakey! 🤣'], ['😏 Vous l\'avez secoué !', 'You shook it up 😏']],
    [/🤔/, ['🤔 Rentrer ou couper ? 😏', 'In or out? • abonne-toi / follow : lien en bio 🎁'], ['👀 Tu dois couper ta position ? 😬', 'Cut or hold? • abonne-toi / follow : lien en bio 🎁'],
      ['🎯 Rentrer maintenant ou attendre ? 🤫', 'Enter now or wait? • abonne-toi / follow : lien en bio 🎁'], ['😅 Garder ou couper ? Le coach sait 😉', 'Hold or cut? The coach knows • lien en bio 🎁']],
    [/🪤|🎣|🪶/, ['🪤 Piège en cours', 'Trap in progress'], ['🎣 Qui va mordre ?', 'Who takes the bait?']],
    [/🐋|💰/, ['🐋 Les baleines arrivent', 'Whales incoming'], ['👀 Gros volume', 'Big volume']],
    [/📉|🔴|🌊/, ['📉 La pression vend', 'Sellers in control'], ['🔴 Ça pousse en bas', 'Pushing lower']],
    [/🙏/, ['🙏 Merci pour le boost !', '🙏 Thanks for the boost!'], ['🚀 Le live décolle grâce à toi', '🚀 The live takes off thanks to you'], ['💜 Toi t\'es un vrai', '💜 You\'re a real one']],
    // v8.0 : on fait parler le public (commentaires)
    [/💬/, ['💬 Tu rentres ou t\'attends ?', '💬 In or wait?'], ['😏 Envie de rentrer là ?', '😏 Tempted to jump in?'], ['📝 Ça monte ou ça descend ? Commente !', '📝 Up or down? Comment!'], ['🎯 Le plan est déjà prêt 😉', '🎯 The plan is already set 😉']],
    [/📈|🟢|🚀/, ['📈 Les acheteurs poussent', 'Buyers in control'], ['🟢 Ça pousse en haut', 'Pushing higher']],
    [/📲|🔌|📡|🧠/, ['📲 Connecté en temps réel', '📲 Connected in real time'], ['📡 En direct sur ton portable', '📡 Live on your phone']],
    [/🔄/, ['🔄 Changement de programme !', '🔄 Change of plan!'], ['🧭 On suit le marché', '🧭 We follow the market']],
    [/🏦/, ['🏦 Les gros sont là', '🏦 Big players here'], ['👀 Zone des gros', '👀 Smart-money zone']],
    [/🧲/, ['🧲 Le marché comble le trou', '🧲 Filling the gap'], ['👀 Zone aimant', '👀 Magnet zone']],
    // v7.6 (demande d'Adel) : on nargue avec humour quand une annonce se prépare (pro, sûr de lui)
    [/📢/, ['📢 Annonce à venir… 😏', '📢 Announcement coming… 😏'], ['🤫 Le coach sait déjà où ça va', '🤫 The coach already knows'], ['😎 Toi tu regardes, eux ils sont prévenus', '😎 You watch, they get the alert'], ['🧐 Décision prise. Lien en bio', '🧐 Decision made. Link in bio'], ['🏃 Les retardataires ont toujours tort 😉', '🏃 Latecomers are always wrong 😉'], ['⚡ Dépêche-toi, une entrée arrive', '⚡ Hurry, an entry is coming']],
    [/↩️/, ['↩️ Rebond sur zone clé', 'Bounce on key zone'], ['👀 Réaction du marché', 'Market reaction']],
    [/👆/, ['👆 Tapote, le marché dort encore 😴', '👆 Tap, the market is still asleep 😴'], ['😅 Pas d\'entrée ? Tapote en attendant', '😅 No entry yet? Tap meanwhile'], ['🫵 Toi là, tapote un peu 😄', '🫵 Hey you, give it a tap 😄']],
    [/./, ['❤️ Tapote l\'écran', 'Tap the screen'], ['🔔 Abonne-toi', 'Follow'], ['💪 La team ALIGN', 'Team ALIGN'], ['🎯 Reste concentré', 'Stay focused']]
  ];
  const cssPunch = document.createElement('style');
  cssPunch.textContent = `.align-punch{position:fixed;z-index:9997;pointer-events:none;padding:10px 22px;border-radius:999px;text-align:center;white-space:normal;max-width:min(430px,62vw);box-sizing:border-box;
    background:linear-gradient(90deg,#ff2d95,#8a2be2,#1e90ff);color:#fff;font:900 30px/1.15 system-ui,Segoe UI,Arial,sans-serif;
    box-shadow:0 6px 18px rgba(0,0,0,.45);text-shadow:0 2px 3px rgba(0,0,0,.4);animation:punchMonte 7.9s ease-out forwards}
  .align-punch.en{background:linear-gradient(90deg,#0d47a1,#1e88e5,#00bcd4)}
  #align-bande .flash.en{filter:hue-rotate(35deg) saturate(1.15)}
  .align-punch .emo{display:inline-block;animation:emoDanse .45s ease-in-out infinite alternate}
  @keyframes emoDanse{0%{transform:rotate(-14deg) scale(1)}100%{transform:rotate(14deg) scale(1.3)}}
  .align-punch small{display:block;font:700 17px/1.2 system-ui,Segoe UI,Arial,sans-serif;opacity:.9}
  @keyframes punchMonte{0%{opacity:0;transform:translateY(20px) scale(.7)}15%{opacity:1;transform:translateY(0) scale(1.05)}
    25%{transform:scale(1)}80%{opacity:1}100%{opacity:0;transform:translateY(-12px)}}
  /* v7.6 (demande d'Adel) : on a l'impression de PARLER avec le marché : bulle de BD qui pointe vers le prix, le texte s'écrit */
  .align-punch{border-radius:22px;animation:punchMonte 7.9s ease-out forwards,bulleRespire 1.6s ease-in-out .9s infinite alternate}
  .align-punch .qui{display:block;font:900 15px/1.2 system-ui,Segoe UI,Arial,sans-serif;letter-spacing:1px;opacity:.95;margin-bottom:2px}
  .align-punch .txt{display:inline-block;animation:sEcrit 1.1s steps(26,end) both}
  @keyframes sEcrit{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
  @keyframes bulleRespire{from{filter:brightness(1)}to{filter:brightness(1.18)}}
  .align-punch::after{content:'';position:absolute;right:var(--q,60px);border:14px solid transparent}
  .align-punch.dessus::after{top:100%;border-top-color:#1e90ff}
  .align-punch.dessous::after{bottom:100%;border-bottom-color:#1e90ff}
  .align-punch.en.dessus::after{border-top-color:#00bcd4} .align-punch.en.dessous::after{border-bottom-color:#00bcd4}
  .align-ping{position:fixed;z-index:9996;pointer-events:none;width:26px;height:26px;margin:-13px 0 0 -13px;border-radius:50%;
    border:4px solid #ffd400;box-shadow:0 0 18px #ffd400;animation:pingPrix 1.1s ease-out 3 forwards}
  @keyframes pingPrix{0%{transform:scale(.4);opacity:1}100%{transform:scale(2.6);opacity:0}}`;
  cssPunch.textContent += `
  html.align-cache #align-bande,html.align-cache .align-punch,html.align-cache .align-ping,html.align-cache #align-chrono,html.align-cache #align-show,html.align-cache #align-cadre{visibility:hidden!important}`;   // v7.9
  document.head.appendChild(cssPunch);
  let punchN = 0, punchTok = 0;   // v7.5 : l'anglais d'une ancienne pastille n'efface plus la nouvelle
  // v7.5 (demande d'Adel) : sens de la pastille = celui de l'info (📉 baisse → en HAUT, 📈 hausse → en BAS), sinon la pente récente
  function sensPastille(cle) {
    if (/📉|🔴|🌊|😢|🚨/.test(cle)) return -1; if (/📈|🟢|🚀|💥|😊/.test(cle)) return 1;
    try { const B = barres(10); return B[B.length - 1][4] >= B[0][4] ? 1 : -1; } catch (e) { return 1; }
  }
  // v7.6 (demande d'Adel) : la pastille se met DANS la zone du prix (pas sur le côté, coupé sur téléphone) :
  // ça baisse → juste AU-DESSUS du prix (les bougies descendent), ça monte → juste EN DESSOUS ; jamais sur le chrono ni sur une autre info
  function pointPrix() {
    try { const r = zoneGraphique(), ser = chart()._chartWidget.model().mainSeries(), ps = ser.priceScale(), fv = ser.firstValue(), b = ser.bars();
      const last = b.valueAt(b.lastIndex()); let x = null;
      try { x = r.left + chart()._chartWidget.model().timeScale().indexToCoordinate(b.lastIndex()); } catch (er) {}
      return { x: isFinite(x) ? x : r.left + r.width - 220, y: r.top + ps.priceToCoordinate(last[4], fv) }; } catch (e) { return null; }
  }
  function chevauche(a, b) { return a.left < b.right + 8 && a.right > b.left - 8 && a.top < b.bottom + 8 && a.bottom > b.top - 8; }
  function placerPastille(e, sens) {
    const r = zoneGraphique(), H = r.height || 600, w = e.offsetWidth, h = e.offsetHeight, haut = r.top + 96, bas = r.top + H - 205 - h;
    const P = pointPrix();
    let left = Math.max(r.left + 10, r.left + r.width - 70 - w - 14);
    if (P && P.x > r.left + 60 && P.x < r.left + r.width - 70) left = Math.max(r.left + 10, Math.min(P.x - w + 70, r.left + r.width - 70 - w - 14));   // la pointe vise la dernière bougie
    let top = P ? (sens < 0 ? P.y - 46 - h : P.y + 46) : (sens < 0 ? haut : bas);
    if (top < haut) top = P ? P.y + 46 : haut; if (top > bas) top = P ? P.y - 46 - h : bas;   // pas de place d'un côté → de l'autre côté du prix
    if (e.dataset.bas) { top = bas; left = Math.max(r.left + 10, r.left + r.width - 70 - w - 14); }   // v8.1 (demande d'Adel) : motivation = en bas, juste au-dessus du tableau des unités, côté prix
    top = Math.max(haut, Math.min(top, bas));
    const obst = [chrono, document.getElementById('align-show')].filter(o => o && getComputedStyle(o).display !== 'none').map(o => o.getBoundingClientRect());
    for (let k = 0; k < 4; k++) { const box = { left, right: left + w, top, bottom: top + h }, o = obst.find(c => chevauche(box, c)); if (!o) break;
      top = sens < 0 ? o.top - h - 10 : o.bottom + 10; if (top < haut || top > bas) { left = Math.max(r.left + 10, o.left - w - 12); top = Math.max(haut, Math.min(top, bas)); } }
    e.style.left = left + 'px'; e.style.top = top + 'px';
    const dessus = P ? top + h / 2 < P.y : sens < 0; e.classList.toggle('dessus', dessus); e.classList.toggle('dessous', !dessus);
    if (P) e.style.setProperty('--q', Math.max(18, Math.min(w - 46, left + w - P.x - 14)) + 'px');
  }
  function ping() {   // v7.6 : un cercle jaune « bat » sur le prix quand le marché parle
    const P = pointPrix(); if (!P) return; document.querySelectorAll('.align-ping').forEach(x => x.remove());
    const d = document.createElement('div'); d.className = 'align-ping'; d.style.left = P.x + 'px'; d.style.top = P.y + 'px'; document.body.appendChild(d); setTimeout(() => d.remove(), 3500);
  }
  // v7.8 : langue de la bande du haut en ce moment (l'info qui défile, sinon la phrase d'accueil au milieu de la bande)
  function langueBande() {
    try { if (bande.classList.contains('on')) return flash.classList.contains('en') ? 'en' : 'fr';
      const b = bande.getBoundingClientRect(), cx = b.left + b.width * 0.35;
      for (const sp of piste.children) { const q = sp.getBoundingClientRect(); if (q.left <= cx && q.right >= cx) return sp.classList.contains('en') ? 'en' : 'fr'; } } catch (e) {}
    return 'fr';
  }
  function coeurs(n, liste, sensForce) {
    try {
      const cle = (liste || []).join(''), g = PUNCH.find(x => x[0].test(cle)) || PUNCH[PUNCH.length - 1];
      const [fr, en] = g[1 + (punchN++ % (g.length - 1))], tok = ++punchTok;
      const e = document.createElement('div'); e.className = 'align-punch';
      if (g === PUNCH[PUNCH.length - 1] || /😊|😏|⏰|👆|🙏|💬|📢/.test(cle)) e.dataset.bas = '1';   // v8.1 : pastille de motivation → en bas vers le tableau de bord
      // v7.8 (demande d'Adel) : la pastille parle la MÊME langue que la bande du haut (FR avec FR, EN avec EN) pour éviter les confusions
      const parts = (txt, defEmo) => { const m = txt.split(' '); const em = /^\p{Extended_Pictographic}/u.test(m[0]) ? m.shift() : defEmo; return [em, m.join(' ')]; };
      const [emoFr, txtFr] = parts(fr, '💬'), [emoEn, txtEn] = parts(en, emoFr);
      let lgCour = null;
      const affiche = lg => { lgCour = lg; e.classList.toggle('en', lg === 'en'); const [em, tx] = lg === 'en' ? [emoEn, txtEn] : [emoFr, txtFr];
        e.innerHTML = '<span class="qui">' + (lg === 'en' ? '🗣️ THE MARKET IS TALKING' : '🗣️ LE MARCHÉ TE PARLE') + '</span><span class="emo">' + esc(em) + '</span> <span class="txt">' + esc(tx) + '</span>';
        e.style.animation = 'none'; void e.offsetWidth; e.style.animation = ''; };
      document.querySelectorAll('.align-punch').forEach(x => x.remove());
      affiche(langueBande()); document.body.appendChild(e);
      const sensP = sensForce || sensPastille(cle); placerPastille(e, sensP); ping();
      const debut = Date.now(), veille = setInterval(() => { try {
        if (tok !== punchTok || Date.now() - debut > 16000) { clearInterval(veille); e.remove(); return; }
        const lg = langueBande(); if (lg !== lgCour) { affiche(lg); placerPastille(e, sensP); } } catch (er) { clearInterval(veille); } }, 700);
    } catch (e) {}
  }
  function choisirPlateforme(v) { PLATEFORME = v; try { localStorage.setItem('alignPlateforme', v); } catch (e) {} remplir(); }
  // v6.7 : marché ennuyant → une grosse tête qui bâille traverse l'écran (😴 ↔ 🥱), puis des cœurs
  const cssEnnui = document.createElement('style');
  cssEnnui.textContent = `#align-ennui{position:fixed;z-index:10002;pointer-events:none;font-size:120px;animation:ennuiPasse 6s ease-in-out forwards}
  @keyframes ennuiPasse{0%{transform:translateX(0) rotate(-8deg);opacity:0}10%{opacity:1}50%{transform:translateX(var(--w)) rotate(8deg) scale(1.15)}
    90%{opacity:1}100%{transform:translateX(calc(var(--w) * 2)) rotate(-8deg);opacity:0}}`;
  document.head.appendChild(cssEnnui);
  function teteEnnui() {
    try {
      const r = zoneGraphique(), e = document.createElement('div'); e.id = 'align-ennui'; e.textContent = '🥱';
      e.style.left = (r.left + 20) + 'px'; e.style.top = (r.top + (r.height || 700) * 0.35) + 'px';
      e.style.setProperty('--w', ((r.width - 260) / 2) + 'px');
      document.getElementById('align-ennui')?.remove(); document.body.appendChild(e);
      let n = 0; const t = setInterval(() => { e.textContent = (++n % 2) ? '😴' : '🥱'; }, 700);
      setTimeout(() => { clearInterval(t); e.remove(); coeurs(10, ['❤️', '👆', '💜']); }, 6000);
    } catch (e) {}
  }
  window.__ALIGN_SHOW__ = { ennui: teteEnnui, pop, lueur, coeurs, lignes: () => lignesAlign() };
  // une info du spectacle sur la bande : jamais par-dessus une vraie info du bot, et pas plus d'une par minute
  let dernierShow = 0;
  function bandeShow(txt) {
    if (occupe || file.length || Date.now() - dernierShow < 52000) return false;
    dernierShow = Date.now(); montrer(txt, false, 1); return true;
  }
  // v5.9 : chaque événement vu à l'écran part aussi au bot → message détaillé dans la chaîne Telegram du marché
  function codeMarche() { const s = String((chart() && chart().symbol()) || ''); return /BTC/i.test(s) ? 'BTC' : /XAU|GOLD/i.test(s) ? 'GOLD' : /NAS|NQ|US100/i.test(s) ? 'NASDAQ' : ''; }
  function versBot(typ, d, minutes, ligne) {
    const mk = codeMarche(); if (!mk) return;
    try { fetch('https://ntfy.sh/' + SUJET + '-ecran', { method: 'POST', body: ['EVT', mk, typ, d, minutes || '', ligne || ''].join('|') }); } catch (e) {}
  }
  // v6.2 : les lignes ALIGN du graphique (ENTRÉE, SL, TP1, TP2) lues directement dans l'indicateur
  function lignesAlign() {
    const res = {};
    try {
      const mod = chart()._chartWidget.model().model();
      for (const ds of mod.dataSources()) {
        if (!/ALIGN/.test(String(ds.title && ds.title()))) continue;
        const vu = new Set();
        (function walk(o, d, dansData) {
          if (!o || d > 8 || typeof o !== 'object' || vu.has(o)) return; vu.add(o);
          if (o instanceof Map) { o.forEach(v => walk(v, d + 1, dansData)); return; }
          if (dansData && typeof o.t === 'string' && typeof o.y === 'number') {
            const n = (o.t.match(/^\s*(ENTRÉE|SL|TP1|TP2)\b/) || [])[1];
            if (n && (!res[n] || o.id > res[n].id)) res[n] = { id: o.id, y: o.y, tt: o.tt || o.t };
            return;
          }
          for (const k of Object.keys(o)) walk(o[k], d + 1, dansData || k === '_primitivesDataById');
        })(ds.graphics()._primitivesCollection.dwglabels, 0, false);
      }
    } catch (e) {}
    return res;
  }

  // v7.5 (demande d'Adel) : les ZONES de l'indicateur (FVG, ORDER BLOCK) lues dans le graphique
  function zonesAlign() {
    const res = [];
    try {
      const mod = chart()._chartWidget.model().model();
      for (const ds of mod.dataSources()) {
        if (!/ALIGN/.test(String(ds.title && ds.title()))) continue;
        const vu = new Set();
        (function walk(o, d, dansData) {
          if (!o || d > 8 || typeof o !== 'object' || vu.has(o)) return; vu.add(o);
          if (o instanceof Map) { o.forEach(v => walk(v, d + 1, dansData)); return; }
          if (dansData && typeof o.y1 === 'number' && typeof o.y2 === 'number') { if (o.t) res.push({ id: o.id, t: String(o.t), hi: Math.max(o.y1, o.y2), lo: Math.min(o.y1, o.y2) }); return; }
          for (const k of Object.keys(o)) walk(o[k], d + 1, dansData || k === '_primitivesDataById');
        })(ds.graphics()._primitivesCollection.dwgboxes, 0, false);
      }
    } catch (e) {}
    return res;
  }
  function infosAlign() {   // v7.6 : les marqueurs ⓘ de l'indicateur (le plus récent de chaque sorte)
    const res = {};
    try { const mod = chart()._chartWidget.model().model();
      for (const ds of mod.dataSources()) { if (!/ALIGN/.test(String(ds.title && ds.title()))) continue; const vu = new Set();
        (function walk(o, d, dansData) { if (!o || d > 8 || typeof o !== 'object' || vu.has(o)) return; vu.add(o);
          if (o instanceof Map) { o.forEach(v => walk(v, d + 1, dansData)); return; }
          if (dansData && typeof o.t === 'string' && typeof o.y === 'number') { const e = (o.t.match(/^(✂️|↩️|✅)\s*ⓘ/) || [])[1]; if (e && (!res[e] || o.id > res[e].id)) res[e] = { e, id: o.id, y: o.y }; return; }
          for (const k of Object.keys(o)) walk(o[k], d + 1, dansData || k === '_primitivesDataById');
        })(ds.graphics()._primitivesCollection.dwglabels, 0, false); } } catch (e) {}
    return Object.values(res);
  }
  function texteZone(t, m) {
    return /FVG/i.test(t) ? '🧲 ' + m + ' • ZONE FVG : un trou laissé par le marché… il adore revenir le combler 👀 rebond ou cassure ? 📲 en temps réel sur ton portable : lien en bio 🎁'
      : /ORDER|OB\b/i.test(t) ? '🏦 ' + m + ' • ORDER BLOCK : la zone où les gros ont passé leurs ordres… ils la défendent souvent 👀 📲 en temps réel sur ton portable : lien en bio 🎁'
      : '👀 ' + m + ' • ' + String(t).toUpperCase() + ' : zone clé du marché • ce qu\'elle annonce : 📲 lien en bio 🎁';
  }
  // prix sous le doigt / la souris (coordonnées de la page → prix du graphique)
  function prixA(yPage) {
    try { const r = zoneGraphique(), ser = chart()._chartWidget.model().mainSeries(), ps = ser.priceScale(), fv = ser.firstValue();
      const p = ps.coordinateToPrice(yPage - r.top, fv), p2 = ps.coordinateToPrice(yPage - r.top + 12, fv); return { p, tol: Math.abs(p - p2) }; } catch (e) { return null; }
  }
  // v7.5 : clic / tap (ou souris posée) sur une ligne ALIGN ou une zone → l'explication défile TOUT DE SUITE dans la bande + pastille
  const vuClic = {};
  function expliquerSous(xPage, yPage, clic) {
    const r = zoneGraphique(); if (xPage < r.left || xPage > r.left + r.width - 70 || yPage < r.top + 86 || yPage > r.top + (r.height || 600)) return false;
    const q = prixA(yPage); if (!q || !isFinite(q.p)) return false;
    const m = nomMarche(), LG = lignesAlign(); let cle = null, txt = null, coul = 'alerte', emo = '👀';
    for (const n of ['ENTRÉE', 'SL', 'TP1', 'TP2']) { const l = LG[n]; if (l && Math.abs(l.y - q.p) <= q.tol) { cle = 'l' + n + Math.round(l.y); txt = teaserLigne(n); coul = couleurLigne(n); emo = n.startsWith('TP') ? '🎯' : n === 'SL' ? '🧱' : '🔮'; break; } }
    // v7.6 (demande d'Adel) : les petits ⓘ du graphique (✂️ trait de décision, ↩️ retournement, ✅ confirmation) sont expliqués aussi
    if (!cle) for (const o of infosAlign()) { if (Math.abs(o.y - q.p) <= q.tol * 1.5) { cle = 'i' + o.e + Math.round(o.y); emo = o.e === '↩️' ? '🔄' : o.e === '✂️' ? '🧱' : '🔮';
      txt = o.e === '✂️' ? '✂️ ' + m + ' • TRAIT BLANC = LIGNE DE DÉCISION : c\'est la clôture 15 min de l\'autre côté qui décide du sens 👀 • une mèche ne compte pas • 📲 lien en bio 🎁'
        : o.e === '↩️' ? '↩️ ' + m + ' • LIGNE DE RETOURNEMENT : si une bougie 15 min clôture de l\'autre côté, le plan s\'inverse 🔄 • le coach te prévient • 📲 lien en bio 🎁'
        : '✅ ' + m + ' • CONFIRMATION : les petites unités doivent aller dans le même sens avant d\'entrer 👀 • 📲 lien en bio 🎁'; break; } }
    if (!cle) for (const z of zonesAlign()) { if (q.p <= z.hi + q.tol / 2 && q.p >= z.lo - q.tol / 2) { cle = 'z' + z.id; txt = texteZone(z.t, m); emo = /FVG/i.test(z.t) ? '🧲' : /ORDER/i.test(z.t) ? '🏦' : '👀'; break; } }
    if (!cle) return false;
    const now = Date.now(); window.__alignExpl = now; if (now - (vuClic[cle] || 0) < (clic ? 4000 : 45000)) return true; vuClic[cle] = now;
    montrer(txt, false, 1, coul, true); coeurs(1, [emo]); lueur(0);   // pastille : en haut si le marché baisse, en bas s'il monte
    return true;
  }
  let posDown = null, survolT = null, vivant = true;   // v7.7 : une ancienne bande arrêtée ne réagit plus aux clics (plus de pastilles en double)
  document.addEventListener('pointerdown', e => { posDown = { x: e.clientX, y: e.clientY, t: Date.now() }; }, { passive: true, capture: true });
  document.addEventListener('pointerup', e => { try { if (!vivant) return;
    if (!posDown || Math.hypot(e.clientX - posDown.x, e.clientY - posDown.y) > 8 || Date.now() - posDown.t > 700) return;   // un glisser n'est pas un clic
    if (e.target && e.target.closest && e.target.closest('.chart-markup-table')) expliquerSous(e.clientX, e.clientY, true);
  } catch (er) {} }, { passive: true, capture: true });
  document.addEventListener('pointermove', e => { if (!vivant || e.pointerType !== 'mouse') return; clearTimeout(survolT); const x0 = e.clientX, y0 = e.clientY;
    survolT = setTimeout(() => { try { expliquerSous(x0, y0, false); } catch (er) {} }, 600); }, { passive: true, capture: true });   // souris posée 0,6 s sur ENTRÉE / SL / TP ou une zone
  const deja = {};
  function uneFois(cle) { if (deja[cle]) return false; deja[cle] = 1; return true; }
  const PHRASES = {
        casseBas: [['🚨', 'ÇA CASSE !', ' casse le dernier plus bas 📉 • ça peut couler encore… infos en temps réel : lien en bio 🎁']],
    casseHaut: [['🚀', 'ÇA CASSE !', ' casse le dernier plus haut 📈 • ça peut décoller… infos en temps réel : lien en bio 🎁']],
    volume: [['🐋', 'LES BALEINES BOUGENT', ' : gros volume 👀 quelque chose se prépare • lien en bio 🎁']],
    hausse: ['📈 {m} veut remonter… jusqu\'où ? le coach le sait : lien en bio 🎁',
             '🟢 {m} reprend des forces 💪 le marché pourrait remonter • plus d\'infos : lien en bio 🎁',
             '🚀 Les acheteurs reviennent sur {m} 👀 la suite en temps réel : lien en bio 🎁'],
    baisse: ['📉 {m} sous pression… va-t-il couler ? réponse en temps réel : lien en bio 🎁',
             '🔴 Les vendeurs tiennent {m} 😬 ça peut encore descendre • plus d\'infos : lien en bio 🎁',
             '🌊 {m} glisse… le coach surveille chaque bougie : lien en bio 🎁'],
    // v6.1 : où est le prix (sans le donner) + le lien en bio = être BRANCHÉ au marché
    bas_zone: ['📍 {m} est posé sur une zone clé en bas 👀 rebond ou cassure ? 📲 connecte-toi au marché depuis ton portable : lien en bio 🎁',
               '🧲 {m} teste le bas de sa zone… les acheteurs vont-ils tenir ? 📡 en direct : lien en bio 🎁'],
    haut_zone: ['📍 {m} touche le haut de sa zone 👀 cassure ou rejet ? 📲 connecte-toi au marché depuis ton portable : lien en bio 🎁',
                '🧱 {m} bute sous un plafond… les vendeurs vont-ils frapper ? 📡 en direct : lien en bio 🎁'],
    milieu: ['🧭 {m} au milieu de sa zone : il cherche sa direction… le coach te dit quand ça part 📡 lien en bio 🎁',
             '⚖️ {m} en équilibre : acheteurs et vendeurs se regardent… qui va craquer ? 👀 lien en bio 🎁'],
    branche: ['📲 Ton portable connecté au marché en temps réel : chaque bougie expliquée en direct • lien en bio 🎁',
              '📡 Connecté au marché depuis ton portable : le coach lit chaque bougie avec toi • lien en bio 🎁',
              '🧠 Tu vois les bougies, le coach te dit ce qu\'elles préparent • lien en bio 🎁',
              '⚡ Ressens le marché en direct : pression, pièges, accélérations… tout est dans le lien en bio 🎁'],
    // v6.5 : marché tout calme → on parle comme un pote, selon l'heure
    calme_matin: ['☕ {m} est tout calme… va te faire un café tranquille, on te prévient quand ça bouge 📲 lien en bio 🎁',
                  '🥐 Petit-déj time : {m} se réveille doucement… le coach veille pour toi • lien en bio 🎁'],
    calme_midi: ['🍔 {m} fait la sieste… va manger un bout, le coach surveille pour toi 👀 lien en bio 🎁',
                 '🥗 Pause déj : {m} bouge pas d\'un poil… on te ping dès que ça part • lien en bio 🎁'],
    calme_aprem: ['🧃 {m} chill grave… prends une pause, le marché te fera signe 😎 lien en bio 🎁',
                  '☕ Café de l\'aprèm ? {m} est en mode tranquille… le coach reste connecté • lien en bio 🎁'],
    calme_soir: ['🍕 {m} est calme ce soir… va dîner, le coach garde un œil 👀 lien en bio 🎁',
                 '🎮 Soirée chill : {m} ne fait rien de fou… on te prévient si ça s\'énerve • lien en bio 🎁'],
    calme_nuit: ['😴 Il est tard et {m} dort à moitié… va te reposer, le coach veille 🌙 lien en bio 🎁',
                 '🌙 {m} roupille… recharge les batteries, le marché sera encore là demain 💤 lien en bio 🎁'],
    // v7.7 (demande d'Adel) : marché calme = on taquine poliment, style jeune
    ennui: ['👀 Au lieu de regarder sans rien faire… le marché n\'a pas encore de point d\'entrée 😅 tapote l\'écran pour le réveiller 👆 • lien en bio 🎁',
            '😎 Pas d\'entrée pour l\'instant : la team patiente… toi tu tapotes, nous on surveille 😉 • lien en bio 🎁',
            '🥱 Pfff… on s\'ennuie, {m} est trop calme 😴 pense à tapoter l\'écran ❤️ et à t\'abonner • lien en bio 🎁',
            '😴 Marché ennuyant sur {m}… allez, tapote l\'écran pour le réveiller 👆❤️ et abonne-toi • lien en bio 🎁'],
    // v8.0 (demande d'Adel) : on pousse les gens à commenter, avec des vannes différentes
    commente: ['💬 À toi de jouer : {m} va MONTER 📈 ou DESCENDRE 📉 ? Écris-le en commentaire, on verra qui a raison 😏 • lien en bio 🎁',
               '📝 Sondage express : {m} ⬆️ ou ⬇️ dans 15 min ? Commente « haut » ou « bas » 👇 • lien en bio 🎁',
               '🧠 Les meilleurs pronostics en commentaire… {m} continue ou retrace ? Montre que t\'as le flair 😎 • lien en bio 🎁',
               '😂 Celui qui devine la prochaine bougie de {m} gagne… notre respect éternel 🙏 commente ! • lien en bio 🎁'],
    range: ['😴 {m} se compresse… avant le gros mouvement ? ⚡ tiens-toi prêt • lien en bio 🎁',
            '🧲 {m} hésite… la prochaine clôture peut tout décider ⏱ lien en bio 🎁']
  };
  let tendN = 0, derniereTend = Date.now(), arme = null;   // arme = mouvement annoncé à l'avance (chrono jusqu'à la clôture)
  function regarder() {
    try {
      if (retour) return;                                   // un abonné a la main : on ne parle pas par-dessus
      const B = barres(40); if (B.length < 25) return;
      const cur = B[B.length - 1], prev = B.slice(-21, -1), m = nomMarche();
      const moyR = prev.reduce((a, x) => a + (x[2] - x[3]), 0) / prev.length || 1;
      const moyV = prev.reduce((a, x) => a + (x[5] || 0), 0) / prev.length || 0;
      const corps = cur[4] - cur[1], sens = corps < 0 ? -1 : 1, id = m + cur[0];
      // v7.5 (constat d'Adel : « il dit que ça va chuter et le marché explose ») : une annonce contredite par le marché est ANNULÉE tout de suite
      if (arme && (cur[4] - arme.p) * arme.d < -0.6 * (arme.r || moyR)) {
        const d = -arme.d, am = arme.m; arme = null;
        montrer('🔄 CHANGEMENT DE PROGRAMME sur ' + am + ' : le marché a changé d\'avis ' + (d === 1 ? '📈' : '📉') + ' • on suit le marché, on ne le combat pas 💪 • la suite en temps réel : lien en bio 🎁', false, 1, d === 1 ? 'haut' : 'bas', true);
        lueur(d); setTimeout(() => coeurs(1, ['🔄'], d), 1500);
        return;
      }
      const pente40 = (cur[4] - B[0][4]) / moyR;   // v7.5 : la tendance de fond (40 bougies) doit être d'accord avant d'annoncer un sens
      // 0) v6.2 : le prix arrive sur une ligne ALIGN → son explication défile dans la bande (2 fois), une fois par quart d'heure
      const LG = lignesAlign(), q15 = Math.floor(Date.now() / 900000);
      for (const n of ['TP2', 'TP1', 'SL', 'ENTRÉE']) {
        const l = LG[n]; if (!l) continue;
        const traverse = B.length > 1 && (B[B.length - 2][4] - l.y) * (cur[4] - l.y) < 0;   // v7.4 : la ligne est traversée d'un coup
        if ((Math.abs(cur[4] - l.y) < 0.3 * moyR || traverse) && uneFois('ligne' + m + n + Math.round(l.y) + q15)) {
          const tete = '👀 ' + m + ' arrive sur une zone clé';
          montrer(tete + ' • le marché prépare quelque chose 👀 pourquoi ? 📲 lien en bio 🎁', false, 2, couleurLigne(n));
          versBot('ligne', cur[4] > l.y ? 1 : -1, '', n);
          setTimeout(() => coeurs(1, ['🤔']), 3600);   // v7.0 : « rentrer ou couper ? » + lien en bio
          if (n.startsWith('TP')) { explosionArgent(cur[4] > l.y ? -1 : 1); feuArtifice(traverse ? '🎯 OBJECTIF ATTEINT D\'UN COUP !' : '🍾 ÇA ENCAISSE !'); pluieBillets(35); setTimeout(() => coeurs(1, ['💥']), 2500); }   // v7.4 : ligne bleue touchée = champagne + billets + explosion   // v7.4 : TP traversé d'un coup = explosion   // objectif atteint : l'argent suit le sens du marché
          return;
        }
      }
      // 0b) v7.5 : le prix entre dans une zone FVG / ORDER BLOCK → explication dans la bande + pastille (une fois par quart d'heure)
      for (const z of zonesAlign()) {
        const dedans = cur[4] <= z.hi && cur[4] >= z.lo, avant = B[B.length - 2][4] > z.hi || B[B.length - 2][4] < z.lo;
        if (dedans && avant && uneFois('zone' + z.id + q15)) { montrer(texteZone(z.t, m), false, 1, 'alerte'); coeurs(1, [/FVG/i.test(z.t) ? '🧲' : '🏦'], cur[4] > B[B.length - 2][4] ? 1 : -1); lueur(0); versBot('ligne', cur[4] > B[B.length - 2][4] ? 1 : -1, '', /FVG/i.test(z.t) ? 'FVG' : 'OB'); return; }
      }
      // 0c) v8.0 (demande d'Adel) : le prix touche son dernier plus haut / plus bas alors que le plan attend ailleurs → on taquine + on fait commenter
      { const hh0 = Math.max(...prev.map(x => x[2])), ll0 = Math.min(...prev.map(x => x[3])), versHaut = (hh0 - cur[4]) < 0.4 * moyR, versBas = (cur[4] - ll0) < 0.4 * moyR;
        if (LG['ENTRÉE'] && (versHaut || versBas) && uneFois('tente' + m + q15)) {
          montrer('🤔 ' + m + (versHaut ? ' touche son dernier plus haut' : ' touche son dernier plus bas') + '… t\'as envie de rentrer là ? 😏 Ça continue ou ça retrace ? 💬 dis-le en commentaire • le scénario complet est déjà prêt : lien en bio 🎁', false, 1, 'alerte');
          setTimeout(() => coeurs(1, ['💬'], versHaut ? 1 : -1), 1500); return; } }
      // 1) bougie qui accélère (corps > 1,6× la taille moyenne) : explosion visuelle + lueur rouge/verte
      if (Math.abs(corps) > 1.6 * moyR && uneFois('acc' + id)) {
        pop(sens === -1 ? '📉' : '📈', 'ÇA ACCÉLÈRE ' + (sens === -1 ? '🔴 ' : '🟢 ') + m, sens, 'jusqu\'où ? la suite en temps réel : lien en bio 🎁'); lueur(sens); versBot('acc', sens); setTimeout(() => coeurs(1, ['⏰']), 3600);
        return;
      }
      // 2) cassure du dernier plus haut / plus bas (20 bougies) : on le montre sans donner le prix
      const hh = Math.max(...prev.map(x => x[2])), ll = Math.min(...prev.map(x => x[3]));
      if (cur[4] < ll && uneFois('cb' + id)) { pop('🚨', 'ÇA CASSE 🔴 ' + m, -1, 'dernier plus bas cassé 📉 ça peut couler encore… infos en temps réel : lien en bio 🎁'); lueur(-1); versBot('casse', -1); setTimeout(() => coeurs(1, ['⏰']), 3600); return; }
      if (cur[4] > hh && uneFois('ch' + id)) { pop('🚀', 'ÇA CASSE 🟢 ' + m, 1, 'dernier plus haut cassé 📈 ça peut décoller… infos en temps réel : lien en bio 🎁'); lueur(1); versBot('casse', 1); setTimeout(() => coeurs(1, ['⏰']), 3600); return; }
      // 3) gros volume
      if (moyV > 0 && (cur[5] || 0) > 2.5 * moyV && uneFois('vol' + id)) { pop('🐋', 'LES BALEINES BOUGENT sur ' + m, 0, 'gros volume 👀 quelque chose se prépare • lien en bio 🎁'); coeurs(8, ['🐋', '💰', '👀']); versBot('volume', sens); return; }
      // 5) v5.6 ANTICIPATION (demande d'Adel) : dire AVANT que ça accélère, avec le chrono jusqu'à la clôture 15 min
      //    pression = tendance nette + bougies qui se compressent ou prix collé au dernier plus bas/haut (la mèche va transpercer)
      const c10b = B.slice(-10).map(x => x[4]), pente10 = (c10b[9] - c10b[0]) / moyR;
      const dirT = pente10 > 0.8 ? 1 : pente10 < -0.8 ? -1 : 0;
      const comp = B.slice(-4).reduce((a, x) => a + (x[2] - x[3]), 0) / 4 < 0.75 * moyR;
      const colle = dirT === -1 ? (cur[4] - ll) < 0.6 * moyR : dirT === 1 ? (hh - cur[4]) < 0.6 * moyR : false;
      const quart = Math.floor(Date.now() / 900000), minRest = Math.max(1, Math.ceil((900 - Math.floor(Date.now() / 1000) % 900) / 60));
      const daccord = dirT && Math.sign(pente40) === dirT && Math.abs(pente40) > 1.5 && corps * dirT > -0.5 * moyR;   // v7.5 : jamais contre la tendance de fond ni contre la bougie en cours
      if (daccord && (comp || colle) && uneFois('pr' + m + quart)) {
        arme = { d: dirT, quart, m, p: cur[4], r: moyR };
        lueur(dirT); coeurs(8, dirT === -1 ? ['📉', '🌊', '⚡'] : ['📈', '🚀', '⚡']);
        pop('⏳', 'COMPTE À REBOURS sur ' + m + ' : ' + (dirT === -1 ? '🔴 GROSSE DISTRIBUTION' : '🟢 GROSSE ACCUMULATION'), dirT,
            'dans ' + minRest + ' min max ⏳ la team : abonne-toi, partage • lien en bio 🎁');
        versBot('pression', dirT, minRest); setTimeout(() => coeurs(1, ['📢'], dirT), 9000);   // v7.6 : « annonce à venir » en pastille, après la punchline
        return;
      }
      // 5b) v6.9 FEINTE : 3 bougies qui repartent contre la tendance → « beaucoup vont y laisser des plumes »
      const c3 = B.slice(-4).map(x => x[4]), contre = dirT ? (c3[3] - c3[0]) * -dirT / moyR : 0;
      if (dirT && contre > 1.0 && uneFois('fe' + m + quart)) {
        const PF = dirT === -1
          ? ['🪤 ATTENTION LA FEINTE sur ' + m + ' : le marché fait semblant de remonter… beaucoup vont acheter trop tôt et y laisser des plumes 🪶 • lien en bio 🎁',
             '🎣 ' + m + ' remonte… qui va mordre à l\'hameçon ? les gros adorent ce genre de piège 😏 • Ne te fais pas piéger : lien en bio 🎁']
          : ['🪤 ATTENTION LA FEINTE sur ' + m + ' : le marché fait semblant de chuter… beaucoup vont vendre trop tôt et y laisser des plumes 🪶 • lien en bio 🎁',
             '🎣 ' + m + ' recule… qui va mordre à l\'hameçon ? les gros adorent ce genre de piège 😏 • ne cours pas après la bougie : lien en bio 🎁'];
        montrer(PF[quart % 2], false, 2, 'alerte'); lueur(0); coeurs(8, ['🪤', '🎣', '🪶']);
        versBot('feinte', dirT, minRest);
        return;
      }
      // 6) manipulation : grosse mèche CONTRE la tendance (les gros piègent) → la vraie direction peut arriver
      const meche = dirT === -1 ? cur[2] - Math.max(cur[1], cur[4]) : dirT === 1 ? Math.min(cur[1], cur[4]) - cur[3] : 0;
      if (daccord && meche > 1.1 * moyR && uneFois('mn' + id)) {
        arme = { d: dirT, quart, m, p: cur[4], r: moyR };
        lueur(dirT);
        pop('🌀', 'MANIPULATION sur ' + m, dirT, (dirT === -1 ? 'les gros piègent les acheteurs… la belle distribution 📉' : 'les gros piègent les vendeurs… le rechargement 📈')
            + ' dans ' + minRest + ' min max ⏳ • abonne-toi, partage • lien en bio 🎁');
        versBot('manip', dirT, minRest);
        return;
      }
      // 4) toutes les ~7 min : la bande dit où le marché a l'air d'aller (sans prix) et renvoie vers le lien en bio
      // v6.1 : marché calme = on parle plus souvent (toutes les ~3 min) : direction, où est le prix, « branche-toi au marché »
      if (Date.now() - derniereTend > 2.4 * 60000) {   // v7.6 : spectacle +10 %
        const c10 = B.slice(-10).map(x => x[4]), pente = (c10[9] - c10[0]) / moyR, larg = (Math.max(...B.slice(-10).map(x => x[2])) - Math.min(...B.slice(-10).map(x => x[3]))) / moyR;
        const pos = (cur[4] - ll) / Math.max(hh - ll, 1e-9), tour = tendN % 4;   // v8.0 : 4e tour = on fait commenter
        // marché très calme (bougies récentes bien plus petites que d'habitude) → message « va te faire un café » selon l'heure
        const r10 = B.slice(-10).reduce((a, x) => a + (x[2] - x[3]), 0) / 10, r40 = B.reduce((a, x) => a + (x[2] - x[3]), 0) / B.length;
        const h = new Date().getHours(), calme = r10 < 0.6 * r40 && tour !== 2;
        const CAL = h < 6 || h >= 23 ? PHRASES.calme_nuit : h < 11 ? PHRASES.calme_matin : h < 14 ? PHRASES.calme_midi : h < 19 ? PHRASES.calme_aprem : PHRASES.calme_soir;
        const L = calme ? (tendN % 2 ? PHRASES.ennui : CAL) : tour === 3 ? PHRASES.commente : tour === 2 ? PHRASES.branche
          : tour === 1 ? (pos < 0.2 ? PHRASES.bas_zone : pos > 0.8 ? PHRASES.haut_zone : PHRASES.milieu)
          : larg < 3.2 ? PHRASES.range : pente > 1.2 ? PHRASES.hausse : pente < -1.2 ? PHRASES.baisse : PHRASES.range;
        if (bandeShow(L[Math.floor(tendN / 3) % L.length].replace('{m}', m))) {
          if (L === PHRASES.ennui) teteEnnui();
          if (L === PHRASES.bas_zone || L === PHRASES.haut_zone) versBot('zone', L === PHRASES.bas_zone ? -1 : 1);   // la vraie réponse part dans la chaîne du marché
          derniereTend = Date.now(); tendN++;
          coeurs(8, L === PHRASES.commente ? ['💬'] : L === PHRASES.branche ? ['📲', '📡', '⚡', '🧠'] : L === PHRASES.baisse ? ['🔴', '📉', '🌊'] : L === PHRASES.hausse ? ['🟢', '📈', '🚀'] : ['👀', '❤️', '🔥']);
        }
      }
    } catch (e) {}
  }
  setTimeout(() => { barres(40).slice(-1).forEach(b => { const k = nomMarche() + b[0]; ['acc', 'cb', 'ch', 'vol'].forEach(p => deja[p + k] = 1); }); }, 1500);  // rien au démarrage
  const regardT = setInterval(regarder, 5000);

  // compte à rebours de la clôture 15 min : les 45 dernières secondes, gros chrono + « ça va se décider »
  const chronoT = setInterval(() => { try {
    const s = Math.floor(Date.now() / 1000), reste = 900 - (s % 900), r = zoneGraphique();
    const enAttente = arme && arme.quart === Math.floor(s / 900);
    // v5.8 (demande d'Adel) : le chrono n'est pas là tout le temps : il surgit dans la DERNIÈRE MINUTE puis disparaît à la clôture
    if ((reste <= 45 || (enAttente && reste <= 60)) && !retour) {
      chrono.style.display = 'flex'; chrono.classList.toggle('urgent', reste <= (enAttente ? 30 : 10));
      // v6.6 : le texte clignote jusqu'à l'explosion et alterne français / anglais toutes les 3 s
      const fr = Math.floor(reste / 3) % 2 === 0;
      const lbl = enAttente
        ? (arme.d === -1 ? (fr ? '🔴 GROSSE DISTRIBUTION<br>' : '🔴 BIG SELL-OFF<br>') : (fr ? '🟢 GROSSE ACCUMULATION<br>' : '🟢 BIG ACCUMULATION<br>'))
          + (reste <= 20 ? (fr ? 'C\'EST MAINTENANT !' : 'IT\'S NOW!') : (fr ? 'abonne-toi • partage 🎁' : 'follow • share 🎁'))
        : (fr ? '⏱ CLÔTURE 15 MIN<br>ça va se décider 👀' : '⏱ 15 MIN CLOSE<br>it\'s about to decide 👀');
      chrono.innerHTML = Math.floor(reste / 60) + ':' + String(reste % 60).padStart(2, '0') + '<small>' + lbl + '</small>';
      // v5.7 (demande d'Adel) : en bas à droite, côté prix, juste au-dessus du tableau de bord (TikTok coupe le haut gauche)
      // v8.3 (demande d'Adel) : le chrono se met en bas à GAUCHE du tableau, à côté de l'unité 1 min (plus jamais sur un message)
      const mq = masque.style.display === 'flex' ? masque.getBoundingClientRect() : null;
      if (!mq) chrono.style.left = (r.left + r.width - 70 - chrono.offsetWidth - 14) + 'px';
      // v5.7 : marché qui baisse → en haut à droite juste sous la bande (les bougies descendent, on ne les cache pas) ;
      //        marché qui monte → en bas à droite, un peu au-dessus du tableau de bord (sans le mordre)
      if (!mq) chrono.style.top = (enAttente && arme.d === -1 ? r.top + 82 : r.top + (r.height || 700) - 205 - chrono.offsetHeight) + 'px';
      else { chrono.style.left = Math.max(r.left + 10, mq.left - chrono.offsetWidth - 12) + 'px'; chrono.style.top = (mq.bottom - chrono.offsetHeight) + 'px'; }
      if (reste === 45 && uneFois('cl' + s)) bandeShow('⏱ Clôture 15 min dans 45 s sur ' + nomMarche() + ' • c\'est elle qui décide 👀 • la suite en temps réel : lien en bio 🎁');
    } else if (chrono.style.display !== 'none') {
      chrono.style.display = 'none';
      const b = barres(2)[0];                              // la bougie qui vient de clôturer
      if (b && reste > 880 && arme && arme.quart === Math.floor((s - 60) / 900)) {
        // v6.0 : « ANNONCÉ » seulement si le prix a VRAIMENT bougé dans le sens annoncé depuis l'annonce (au moins ½ bougie moyenne) ;
        // sinon pas de honte : on rassure (« le marché respire, il est comme vous ») et on n'en reparle plus
        const a = arme; arme = null; const pNow = (barres(1)[0] || b)[4]; const mv = (pNow - a.p) * a.d;
        if (mv < 0.5 * (a.r || 1)) {
          versBot('respire', a.d);                 // Telegram : le verdict honnête, pour que personne ne panique
          montrer('😮‍💨 ' + a.m + ' : pas de panique • le marché respire, il est comme vous 😅 • patience, la suite en temps réel : lien en bio 🎁', true, 1, 'proche');
          return;
        }
        { feuArtifice(a.d === -1 ? '📉 ANNONCÉ !' : '📈 ANNONCÉ !'); coeurs(14);
          versBot('annonce', a.d); pop('✅', 'ANNONCÉ ! ' + a.m + (a.d === -1 ? ' a coulé 📉' : ' a décollé 📈'), a.d, 'la team ALIGN l\'a vu venir • abonne-toi, partage • lien en bio 🎁'); return; }
      }
      if (b && reste > 880) {
        const LG = lignesAlign(), rg = Math.max(b[2] - b[3], 1e-9);
        for (const n of ['TP2', 'TP1', 'SL', 'ENTRÉE']) {
          const l = LG[n]; if (!l || !(b[3] <= l.y && l.y <= b[2]) || Math.abs(b[4] - l.y) < 0.25 * rg) continue;
          const dr = b[4] > l.y ? 1 : -1;            // touchée puis clôture loin de la ligne = rebond / rejet
          pop('↩️', 'REBOND sur une ligne clé ' + nomMarche(), dr, 'le marché prépare quelque chose 👀 pas de panique • pourquoi ? 📲 lien en bio 🎁');
          versBot('rebond', dr, '', n); coeurs(8, ['👀', '↩️', '⚡']);
          return;
        }
      }
      if (b && reste > 880) { const v = b[4] >= b[1] ? 1 : -1; if (!occupe && !file.length) pop(v === 1 ? '🟢' : '🔴', 'BOUGIE 15 MIN CLÔTURÉE ' + (v === 1 ? '⬆️' : '⬇️') + ' ' + nomMarche(), v, 'la suite en temps réel : lien en bio 🎁'); }
    }
  } catch (e) {} }, 1000);
  // de temps en temps des cœurs qui montent : « tapote l'écran »
  const coeurT = setInterval(() => { if (!retour) coeurs(10); }, 80000);   // v7.7 : +12 %

  // v7.4 (demande d'Adel) : position en cours dans le bon sens → petits mots qui font sourire, toutes les 4 min (sans prix)
  const posT = setInterval(() => { try {
    if (retour) return; const LG = lignesAlign(), E = LG['ENTRÉE'], S = LG.SL; if (!E || !S) return;
    const B = barres(3); if (!B.length) return; const p = B[B.length - 1][4], sens = S.y > E.y ? -1 : 1;
    if (sens * (p - E.y) <= 0) return;
    coeurs(1, ['😊']); setTimeout(() => coeurs(1, ['😏']), 16600);
  } catch (e) {} }, 190000);   // v7.7 : +12 %
  // v8.2 (demande d'Adel) : en live, la ligne du bas du tableau (▼ SHORT E … TP … SL …) ne montre plus les prix :
  // un cache de la même couleur se pose exactement dessus (repéré dans l'image du graphique), sens gardé, prix → « ? » + lien en bio
  const masque = document.createElement('div'); masque.id = 'align-masque'; document.body.appendChild(masque);
  cssPunch.textContent += `
  #align-masque{position:fixed;z-index:140;pointer-events:none;display:none;align-items:center;justify-content:center;gap:10px;color:#fff;
    font:900 13px/1 system-ui,Segoe UI,Arial,sans-serif;   /* v8.4 (Adel) : on garde la couleur d'origine de la ligne, comme en v8.2 (« c'était nickel »), texte un peu plus gros */white-space:nowrap;overflow:hidden;letter-spacing:.3px}
  #align-masque .cle{display:inline-block;animation:emoDanse .6s ease-in-out infinite alternate}
  html.align-cache #align-masque{visibility:hidden!important}`;
  let masqueN = 0;
  function celluleSens() {
    try { const mod = chart()._chartWidget.model().model(); let res = null;
      for (const ds of mod.dataSources()) { if (!/ALIGN/.test(String(ds.title && ds.title()))) continue; const vu = new Set();
        (function walk(o, d, dansData) { if (!o || d > 8 || typeof o !== 'object' || vu.has(o) || res) return; vu.add(o);
          if (o instanceof Map) { o.forEach(v => walk(v, d + 1, dansData)); return; }
          if (dansData && typeof o.t === 'string' && typeof o.bgc === 'number') { if (/\b(SHORT|LONG)\b/.test(o.t) && /\d{3,}/.test(o.t)) res = o; return; }
          for (const k of Object.keys(o)) walk(o[k], d + 1, dansData || k === '_primitivesDataById');
        })(ds.graphics()._primitivesCollection.dwgtablecells, 0, false); }
      return res; } catch (e) { return null; }
  }
  function poserMasque() {
    try {
      const cel = celluleSens(); if (!cel) { masque.style.display = 'none'; return; }
      const R0 = cel.bgc & 255, G0 = (cel.bgc >> 8) & 255, B0 = (cel.bgc >> 16) & 255;
      const cv = document.querySelector('.chart-markup-table .chart-gui-wrapper canvas'); if (!cv) return;
      const R = cv.getBoundingClientRect(), k = cv.width / R.width, W = cv.width, y0 = Math.floor(cv.height * 0.55);
      const d = cv.getContext('2d').getImageData(0, y0, W, cv.height - y0).data; let top = -1, bas = -1, g = 0, dr = 0;
      for (let y = cv.height - y0 - 1; y >= 0; y--) { let n = 0, mi = 1e9, ma = -1;   // v8.3 : on part du BAS (la ligne SHORT/LONG est la dernière du tableau)
        for (let x = 0; x < W; x += 2) { const j = (y * W + x) * 4; if (Math.abs(d[j] - R0) < 8 && Math.abs(d[j + 1] - G0) < 8 && Math.abs(d[j + 2] - B0) < 8) { n++; if (x < mi) mi = x; if (x > ma) ma = x; } }
        if (ma - mi > W * 0.3 && n * 2 > 0.6 * (ma - mi)) { if (bas < 0) { bas = y; g = mi; dr = ma; } top = y; } else if (bas >= 0 && top - y > 1) break; }   // s'arrête au trait entre deux lignes du tableau   // le texte blanc au milieu ne coupe pas la ligne
      if (bas < 0) { masque.style.display = 'none'; return; }
      Object.assign(masque.style, { display: 'flex', left: (g / k + R.left) + 'px', top: ((top + y0) / k + R.top) + 'px', width: ((dr - g + 2) / k) + 'px',
        height: ((bas - top + 1) / k) + 'px', background: 'rgb(' + R0 + ',' + G0 + ',' + B0 + ')' });
      const en = langueBande() === 'en', sens = (cel.t.match(/[▼▲]?\s*(SHORT|LONG)[^E\d]*/) || [''])[0].trim();
      masque.innerHTML = (masqueN++ % 4 < 2)
        ? esc(sens) + ' • ' + (en ? 'ENTRY' : 'ENTRÉE') + ' <span class="cle">❓</span> • TP <span class="cle">❓</span> • SL <span class="cle">❓</span>'
        : (arme ? '<span class="cle">⏳</span> ' + (en ? 'IT\'S ALMOST TIME… CAN YOU GET IN? 👍 LINK IN BIO, HURRY!' : 'ÇA VA ÊTRE LE MOMENT… TU PEUX RENTRER ? 👍 LIEN EN BIO, VITE !')
          : '<span class="cle">🤔</span> ' + (en ? 'WANT TO KNOW IF YOU CAN GET IN? 👍 LINK IN BIO' : 'TU VEUX SAVOIR SI TU PEUX RENTRER ? 👍 LIEN EN BIO'));   // v8.3 : « vite » seulement quand le spectacle a vraiment annoncé un mouvement (pas de fake)
    } catch (e) {}
  }
  // v8.3 (demande d'Adel) : les GROSSES étiquettes ENTRÉE / SL / TP1 / TP2 (à gauche, avec les prix) sont recouvertes
  // et remplacées par des étiquettes courtes « ❓ », toutes de la même taille, alignées sur la colonne du TP2, juste sous leur ligne
  const etiqBox = document.createElement('div'); etiqBox.id = 'align-etiq'; document.body.appendChild(etiqBox);
  cssPunch.textContent += `
  #align-etiq .cache{position:fixed;z-index:139;pointer-events:none;background:rgb(15,15,15);display:flex;align-items:center;justify-content:center;overflow:hidden;
    white-space:nowrap;border-radius:6px;font:900 13px/1 system-ui,Segoe UI,Arial,sans-serif}
  #align-etiq .etq span{display:inline-block;animation:emoDanse .9s ease-in-out infinite alternate}
  #align-etiq .etq.chaud{animation:chaud .6s ease-in-out infinite alternate}
  @keyframes chaud{from{filter:brightness(1)}to{filter:brightness(1.7) saturate(1.4)}}
  #align-etiq .etq{position:fixed;z-index:139;pointer-events:none;box-sizing:border-box;display:flex;align-items:center;justify-content:center;gap:6px;white-space:nowrap;overflow:hidden;padding:0 8px;border-radius:6px;
    font:900 14px/1.15 system-ui,Segoe UI,Arial,sans-serif;box-shadow:0 2px 6px rgba(0,0,0,.45)}
  #align-etiq .etq b{display:inline-block;animation:emoDanse .7s ease-in-out infinite alternate}
  html.align-cache #align-etiq{visibility:hidden!important}`;
  function grossesEtiquettes() {
    const res = [];
    try { const mod = chart()._chartWidget.model().model();
      for (const ds of mod.dataSources()) { if (!/ALIGN/.test(String(ds.title && ds.title()))) continue; const vu = new Set();
        (function walk(o, d, dansData) { if (!o || d > 8 || typeof o !== 'object' || vu.has(o)) return; vu.add(o);
          if (o instanceof Map) { o.forEach(v => walk(v, d + 1, dansData)); return; }
          if (dansData && typeof o.t === 'string' && typeof o.y === 'number') { const n = (o.t.match(/^\s*(ENTRÉE|SL|TP1|TP2)\b/) || [])[1]; if (n && o.st === 'lrg') res.push({ n, o }); return; }
          for (const k of Object.keys(o)) walk(o[k], d + 1, dansData || k === '_primitivesDataById');
        })(ds.graphics()._primitivesCollection.dwglabels, 0, false); } } catch (e) {}
    return res;
  }
  let etiqN = 0;
  const ETIQ_ACTIVES = false;   // v8.3 (décision d'Adel) : PAS d'étiquette posée par-dessus celles du graphique → les étiquettes ENTRÉE/SL/TP se changent dans le script Pine
  function poserEtiquettes() {
    if (!ETIQ_ACTIVES) { etiqBox.innerHTML = ''; return; }
    try {
      const E = grossesEtiquettes(); if (!E.length) { etiqBox.innerHTML = ''; return; }
      const cv = document.querySelector('.chart-markup-table .chart-gui-wrapper canvas'); if (!cv) return;
      const R = cv.getBoundingClientRect(), k = cv.width / R.width, ctx = cv.getContext('2d');
      const ser = chart()._chartWidget.model().mainSeries(), ps = ser.priceScale(), fv = ser.firstValue();
      const boites = [];
      for (const { n, o } of E) {
        const y = ps.priceToCoordinate(o.y, fv); if (!isFinite(y)) continue;
        const fond = ctx.getImageData(Math.round(3 * k), Math.round(y * k), 1, 1).data;   // v8.3 : la vraie couleur de fond de l'écran (plus de tache noire)
        const a = ((o.ci >>> 24) & 255) / 255, col = [o.ci & 255, (o.ci >> 8) & 255, (o.ci >> 16) & 255].map((v, i) => Math.round(a * v + (1 - a) * fond[i]));
        const y0 = Math.max(0, Math.round((y - 18) * k)), hh = Math.round(36 * k), W = Math.round(cv.width * 0.75), d = ctx.getImageData(0, y0, W, hh).data;
        // v8.3 : on mesure le CORPS de l'étiquette (colonnes colorées sur au moins 9 px de haut) : la ligne fine de même couleur ne compte pas
        const ok = j => Math.abs(d[j] - col[0]) < 14 && Math.abs(d[j + 1] - col[1]) < 14 && Math.abs(d[j + 2] - col[2]) < 14;
        const cnt = new Uint16Array(W); for (let yy = 0; yy < hh; yy++) for (let x = 0; x < W; x++) if (ok((yy * W + x) * 4)) cnt[x]++;
        const minH = Math.round(9 * k); let mi = -1, ma = -1;
        for (let x = 0; x < W; x++) { if (cnt[x] >= minH) { if (mi < 0) mi = x; ma = x; } else if (mi >= 0 && x - ma > Math.round(8 * k)) break; }
        let yt = 1e9, yb = -1;
        if (mi >= 0) for (let yy = 0; yy < hh; yy++) { let n = 0; for (let x = mi; x <= ma; x++) if (ok((yy * W + x) * 4)) n++; if (n > (ma - mi + 1) * 0.5) { if (yy < yt) yt = yy; if (yy > yb) yb = yy; } }
        if (mi < 0 || yb < 0) { mi = 1e9; ma = -1; }
        boites.push({ n, o, y, fond: 'rgb(' + fond[0] + ',' + fond[1] + ',' + fond[2] + ')', col: 'rgb(' + col.join(',') + ')', tc: (o.tci & 255) > 128 ? '#fff' : '#111', box: ma > mi + 20 ? { l: mi / k + R.left, t: (y0 + yt) / k + R.top, r: (ma + 1) / k + R.left, b: (y0 + yb + 1) / k + R.top } : null });
      }
      // v8.3 (demande d'Adel : « j'ai l'impression que tu en as mis deux » + « petites bandes noires ») : UNE seule étiquette par ligne,
      // posée exactement sur l'étiquette d'origine (plus de doublon, plus de cache noir), toutes alignées et de la même largeur,
      // le prix remplacé par « ❓ » + un petit défi qui change, qui clignote quand le prix s'approche
      const vis = boites.filter(x => x.box); if (!vis.length) { etiqBox.innerHTML = ''; return; }
      const xCol = Math.min(...vis.map(x => x.box.l)), larg = Math.max(...vis.map(x => x.box.r)) - xCol, en = langueBande() === 'en';
      const pNow = ((barres(1)[0]) || [])[4] || 0; etiqN++;
      const proche = x => pNow && Math.abs(pNow - x.o.y) / pNow < 0.002;
      const defi = x => { const L = proche(x) ? (en ? ['⚡ GETTING CLOSE!', '👉 LINK IN BIO, HURRY!'] : ['⚡ ÇA APPROCHE !', '👉 LIEN EN BIO, VITE !'])
        : (en ? ['👀 LINK IN BIO', '🤔 WANNA KNOW?', '😏 DARE YOU?'] : ['👀 LIEN EN BIO', '🤔 T\'AS ENVIE DE SAVOIR ?', '😏 CAP OU PAS CAP ?']); return L[Math.floor(etiqN / 12) % L.length]; };
      etiqBox.innerHTML = vis.map(x => '<div class="etq' + (proche(x) ? ' chaud' : '') + '" style="left:' + (xCol - 2) + 'px;top:' + (x.box.t - 2) + 'px;width:' + (larg + 4) + 'px;height:' + (x.box.b - x.box.t + 4) + 'px;background:' + x.col + ';color:' + x.tc + '">'
        + (x.n === 'ENTRÉE' && en ? 'ENTRY' : x.n) + ' <b>❓</b> <span>' + defi(x) + '</span></div>').join('');
    } catch (e) {}
  }
  const etiqT = setInterval(poserEtiquettes, 300);
  // v8.3 (demande d'Adel) : quand tu bouges / zoomes le graphique, les étiquettes et le cache suivent tout de suite
  let suitT = 0; ['wheel', 'pointermove'].forEach(ev => document.addEventListener(ev, e => { if (!vivant || (ev === 'pointermove' && !e.buttons) || suitT) return;
    suitT = requestAnimationFrame(() => { suitT = 0; poserEtiquettes(); poserMasque(); }); }, { passive: true, capture: true }));   // v8.3 : suit le graphique quand tu bouges la souris poserEtiquettes();
  const masqueT = setInterval(poserMasque, 300); poserMasque();
  window.__ALIGN_BANDE__ = {
    version: VERSION, recu, punch: c => coeurs(1, [c]), plateforme: v => choisirPlateforme(v),
    stop() { vivant = false; clearTimeout(survolT); cancelAnimationFrame(raf); clearInterval(suivi); clearInterval(astuceT); clearInterval(regardT); clearInterval(chronoT); clearInterval(coeurT); clearInterval(posT); clearInterval(masqueT); masque.remove(); clearInterval(etiqT); etiqBox.remove(); try { cssEnnui.remove(); document.getElementById('align-ennui')?.remove(); } catch (e) {}
      [cadre, chrono, cssShow].forEach(x => { try { x.remove(); } catch (e) {} }); document.querySelectorAll('.align-coeur,.align-billet,.align-argent,.align-punch,.align-ping').forEach(x => x.remove()); try { cssBillet.remove(); } catch (e) {} obs.disconnect(); try { es.close(); } catch (e) {} bande.remove(); css.remove(); }
  };
})();
