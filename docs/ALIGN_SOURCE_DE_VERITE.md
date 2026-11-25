# ALIGN — source de vérité unique (à lire AVANT toute action)

Ce fichier définit la source de vérité du projet pour les mainteneurs humains et les outils explicitement autorisés.
System map (flows, component roles, folders and reliability checks): `docs/ALIGN_SYSTEM_MAP.md`.

Si une information ci-dessous contredit ce que tu crois savoir : **ce fichier gagne**.
Si l'**identité du projet** est ambiguë (autre dépôt, autre branche de production, autre indicateur, autre projet) : **arrête-toi et demande**. Une tâche de maintenance ALIGN normale (test, workflow, bot) se traite normalement.

## 1. Identité du projet

**Un seul projet, deux appellations historiques :** `ALIGN TRADING` est le nom canonique du produit et `Trading Auto` / `trading-auto` est un ancien nom technique du même projet. Ce n'est ni un second dépôt, ni un second serveur à maintenir, ni une version concurrente. Toute demande ou trace mentionnant Trading Auto doit être rattachée à ce dépôt canonique après vérification de la branche et du SHA. Pour toute nouvelle mise à jour, utiliser exclusivement ce dépôt et une PR vers `main`. Ne jamais créer de copie parallèle ni supprimer de code historique sans inventaire de provenance et comparaison.

| Élément | Valeur canonique | Pièges connus (NE PAS utiliser) |
|---|---|---|
| Projet | **ALIGN TRADING** | Loki / KEEP, Inside Dombes, Nino & Luciole : autres projets |
| Dépôt | `adelkhatra-bit/trading-align-` | `trading-dashboard-4000` (autre projet) |
| Branche du code | `main` | — |
| Branche des données publiées | `live-data` (racine : `live.json` et, si créé, `fermes.json` uniquement) | Aucun code/HTML/docs/workflow/Pine/JS ; ne jamais la fusionner dans `main` |
| Indicateur de données/bridge (unique) | `align-bot/pine/ALIGN_MTF_PRO_v25.pine` | Tout autre script ne peut alimenter le BOT ou le bridge |
| Compagnon visuel (clôtures de bougies) | `align-bot/pine/ALIGN_MTF_PRO_v24.pine` | Visuel uniquement : aucune alerte sortante, aucun bridge, aucune donnée consommée par ROBOT V12 ; autres `v24*`, propositions et diffs = historique |
| Titre TradingView | `ALIGN MTF PRO v25 (Inside)` (court : `ALIGN MTF v25`), Pine `//@version=6` | Tout autre titre = mauvais script |
| Marchés actifs | BTC, GOLD (`BTCUSD`, `XAUUSD`) uniquement | NASDAQ retiré de l'analyse, des entrées, de la surveillance et du suivi des positions ; toute ancienne mémoire NASDAQ est archivée pour audit et jamais rejouée |
| Bot Telegram | `@align_mtf_adel_bot` | — |
| Bande live | `docs/live/align-bande-live.user.js` (Tampermonkey) | Copies locales anciennes (12.2.3, 12.2.4…) |
| Bridge TradingView canonique | Worker mailbox Cloudflare → `align_tv_mailbox_feeder.py` → `align-bot/align_tv_bridge.py` dans le runner GitHub (`127.0.0.1:4100`) | Ancien cache Node `server.js` / port 4000, extension `tradingview-analyzer`, tunnel historique |

### Périmètre strict de `live-data`

La branche `live-data` ne transporte que les données générées à la racine : `live.json` et `fermes.json` (ce dernier est créé par le BOT au besoin). Elle ne contient aucun code, page HTML, workflow, documentation ou indicateur. Le code et la page live restent exclusivement dans `main`. Le snapshot `archive/live-data-full-tree-20261125` est une sauvegarde historique de l'ancien arbre complet : il n'est ni une branche de développement ni une source de déploiement. Le contrôle CI vérifie automatiquement le contenu distant de `live-data`.

## 2. Chaîne de données de production

```
TradingView · Pine v25 · 2 alertes (BTCUSD et XAUUSD)
  → Cloudflare Worker `align-tv-mailbox` · POST /ingest/tradingview
  → Durable Object · dernier payload brut par symbole (pas de validation MTF)
  → `align_tv_mailbox_feeder.py` · GET /mailbox puis POST inchangé
  → `align_tv_bridge.py` · runner GitHub, 127.0.0.1:4100 (unique validation)
  → `align-bot.yml` · GET /bridge/robot-v12/mtf
  → `align-bot/align_bot.py` · filtres news / R:R / risque / mémoire
  → Telegram (@align_mtf_adel_bot) + publication live-data/live.json
  → bande live (texte, animations, voix)
```

Le script compagnon `ALIGN_MTF_PRO_v24.pine` peut rester chargé sur le graphique pour ses visuels de clôture de bougie. Il ne fait pas partie de la chaîne de données : aucune alerte sortante, aucun webhook, aucun bridge et aucune lecture par ROBOT V12. Le v25 reste l'unique source des snapshots et décisions transmises au BOT.

Le bridge Python est éphémère dans le runner du workflow : **4100 n'est pas un service permanent du PC** et ne doit pas être exposé par un tunnel public. Le Worker ne remplace pas le bridge : il transporte et conserve le JSON brut. Le feeder le transmet sans compléter ni réécrire ses champs ; `BridgeStore` dans `align_tv_bridge.py` est l'unique validateur MTF.

Le BOT peut aussi être configuré pour lire un bridge HTTPS externe via les secrets `ALIGN_TV_API_URL` et `ALIGN_TV_READ_TOKEN`. Cette voie remplace la voie mailbox dans le workflow ; elle ne doit être activée que si l'URL et le stockage visés ont été explicitement vérifiés. Ne jamais déduire l'identité du serveur à partir du seul chemin HTTP.

### Deux routes identiques à ne pas confondre

Le serveur historique `server.js` écoute par défaut sur **4000** et expose lui aussi `/bridge/robot-v12/mtf`. Ce nom de route identique masque deux stockages différents :

- chemin canonique du BOT : mailbox Cloudflare → relais → BridgeStore Python du runner (12 UT : M1, M3, M5, M10, M15, M30, M45, H1, H2, H4, D1, W1) ;
- chemin historique : extension `tradingview-analyzer` → `POST /tradingview/live` sur `server.js:4000` → cache Node `tradingview-mtf-cache.json` (9 UT : M1, M5, M15, M30, H1, H2, H4, D1, W1).

Le serveur 4000 n'est pas le bridge utilisé dans les runs BOT #1074/#1075 : leurs journaux montrent le relais mailbox et le bridge runner 4100. Ce serveur et l'extension sont laissés en place, mais ne doivent pas servir à valider le BOT canonique ni à alimenter son healthcheck. Ne pas arrêter, modifier ou rediriger le port 4000 dans le cadre de ce flux.

Le bridge exige les 12 UT du contrat Python. L'UT active du graphique peut être l'une des 9 UT acceptées par le BOT (M1, M5, M15, M30, H1, H2, H4, D1, W1) ; cela ne dispense jamais le payload de contenir M3, M10 et M45.

Règle : quand `ALIGN_REQUIRE_TV_BRIDGE=1`, **aucun repli** sur des niveaux calculés ailleurs. Si une UT manque ou est périmée, le BOT reste en `WAIT` et n'émet aucun signal.

### Telegram : chemin applicatif unique

- **Bot applicatif** : `align-bot/align_bot.py` (`@align_mtf_adel_bot`).
- **Réception** : un seul thread `boucle_polling_telegram_tracee` appelle `getUpdates`, acquitte rapidement les callbacks et pousse les updates dans `TELEGRAM_UPDATES`; `recevoir_updates_telegram` dépile cette file sur le thread principal, puis `traiter` route les commandes et actions. La boucle principale ne lance pas un second `getUpdates`.
- **Sortie** : les appels applicatifs passent par `telegram()` puis `_telegram_sortant_autorise`; un blocage `TELEGRAM_PULL_BLOCK` n'est pas une livraison et ne doit jamais être compté comme telle.
- **Commandes de diagnostic** : `/statut` et `/audit` restent sur le chemin rapide; `/diag` est traité par `traiter`, uniquement en chat privé, avec expéditeur = chat = propriétaire. Il interroge en lecture la même route MTF que le bot pour BTC et GOLD, affiche l'UT active et le nombre d'UT fraîches, puis lit `RUNNER_TEMP/align_diag.json` pour les compteurs STALE. Aucune écriture, aucun payload ni secret n'est exposé.
- **Composants à ne pas confondre avec un second bot** : `server.js` expose des routes serveur/bridge mais ne contient pas d'appel direct à l'API Bot Telegram; `agent-bus.js` est un bus interne d'agents; l'extension `tradingview-analyzer` transmet des données au serveur mais n'appelle pas directement l'API Bot Telegram.
- Les contrôles `getMe` / `getWebhookInfo` des workflows sont des précontrôles d'identité et de réception; ils ne remplacent pas le chemin applicatif du bot ni un test de livraison.

## 3. Règles d'unité de temps (confusion connue)

- Le **plan** (Entry / SL / TP1 / TP2) est calculé sur **M15 clôturé**.
- Le **déclencheur** dépend de la stratégie : SCALPING = M1, DAY = M5, SWING = H1.
- Un même timeframe ne doit avoir **qu'une seule** direction dans un message.
  Écart connu à corriger (non encore prouvé en direct) : dans le payload bridge du v25,
  `lecture_5m` / `lecture_15m` utilisent la bougie clôturée (`d5Fermee`, `d15Fermee`)
  alors que `mtf.M5` / `mtf.M15` utilisent `d5Strat` / `d15Strat`, la bougie courante pour BTC.
- Un TP déjà touché ne redevient jamais un objectif ; un signal dont le SL est dépassé n'est jamais réémis.

## 4. Fusion : qui peut fusionner quoi

- Le ruleset GitHub `ALIGN main - aucune fusion sans tests verts` est actif sur la branche par défaut. Son état vérifié le 20/11/2026 bloque la suppression et les mises à jour non-fast-forward, exige le contrôle `validate` et ne déclare aucun acteur de contournement. Recontrôler le ruleset dans GitHub avant chaque release.
- **Fusion manuelle uniquement.** Aucun workflow, bot ou agent ne fusionne une PR automatiquement. Toute fusion exige l'approbation explicite du propriétaire, après revue complète du diff, validation des contrôles requis sur le SHA exact et vérification du fonctionnement réel concerné.
- Le contrôle `validate` vert est nécessaire, mais ne prouve pas à lui seul les connexions live ni le bon fonctionnement en production.
- Une PR = un sujet. Partir de `main` à jour ; ne jamais réutiliser une branche appartenant à une autre PR.
## 5. Secrets (noms et rôles uniquement — jamais les valeurs ni leur état)

| Secret | Rôle |
|---|---|
| `TELEGRAM_TOKEN` | Bot Telegram |
| `GROQ_API_KEY`, `ANTHROPIC_API_KEY` | Fournisseurs IA |
| `GEMINI_API_KEY`, `OPENAI_API_KEY` | Fournisseurs IA de secours |
| `METAAPI_TOKEN`, `TOPSTEP_API_KEY`, `TOPSTEP_USERNAME` | Intégrations de compte, mode test |
| `ALIGN_TV_API_URL`, `ALIGN_TV_READ_TOKEN` | Bridge TradingView |

Ne jamais publier dans ce dépôt, les issues, les commentaires ou les logs publics la présence, l'absence, la validité ou la valeur d'un secret. Vérifier sa configuration uniquement dans l'environnement sécurisé prévu ; ne rapporter que le résultat strictement nécessaire, sans exposer sa valeur.
## 6. Interdits absolus

- **Aucune donnée inventée, simulée ou de remplacement** à la place d'une vraie donnée de l'indicateur v25.
  Si la vraie donnée manque ou est périmée : on n'émet rien (`WAIT`) et on signale la panne, on ne comble jamais le trou.
  Appliqué par les tests : `test_align_tv_bot_gate.py` (le bot exige le bridge TradingView par défaut)
  et `test_align_tv_bridge.py::test_rejects_missing_required_timeframe_instead_of_fabricating_it`.
- Aucun ordre broker réel ; `AUTO_TRADE` et `TOPSTEP_REEL` restent à `0` tant que le propriétaire ne dit pas « réel ».
- Ne jamais afficher, copier ou committer la valeur d'un secret.
- Ne jamais modifier le design, les animations ou l'indicateur sans demande explicite.
- Ne jamais supprimer un fichier, une branche ou une PR contenant du travail non intégré ou dont la provenance n'est pas établie.

## 7. Accès et automatisation de code

- Les relais Copilot CLI/cloud-agent, les profils GitHub Copilot personnalisés et l'assignation automatique d'agents de code sont retirés du périmètre actif ALIGN. Les signalements de panne restent des rapports destinés à un mainteneur humain.
- Les clés GROQ/ANTHROPIC/GEMINI/OPENAI restent des fournisseurs IA runtime du BOT pour les commentaires de marché, avec plafond journalier et repli interne. Elles ne donnent aucun accès d'écriture au dépôt.
- Le dépôt étant public, les fichiers restent lisibles par des services IA externes. Le code du dépôt ne peut pas interdire cette lecture ; cela nécessite de rendre le dépôt privé et de contrôler séparément les permissions GitHub. Ce changement de visibilité n'est pas effectué ici car il peut impacter Pages et la publication publique `live-data`.
- Le secret historique COPILOT_GITHUB_TOKEN n'est plus référencé par les workflows ALIGN. Sa suppression des paramètres GitHub Actions reste à effectuer par un propriétaire du dépôt.
- Le ruleset actif de `main` exige `validate` et aucun acteur ne peut le contourner ; les merges restent soumis à la revue humaine et à l'autorisation du propriétaire.


## 8. Branches, rôles, lecteurs et écrivains — proposition documentaire (23/11/2026)

| Branche | Rôle | Lecteurs / consommateurs | Écrivains |
|---|---|---|---|
| `main` | Code, workflows et validation canoniques | Workflow validation; worker `align-bot.yml` après validation push main; CI PR main | Mainteneurs via PR/merge; worker bot publie l'état sur `live-data` |
| `live-data` | Données publiques/live (`live.json`) | Pages et consommateurs externes (configuration exacte Pages/Cloudflare NON VÉRIFIÉE) | Worker `align-bot.yml` via publication data; aucun code |
| `audit/chatgpt-pilotage` | Rapports de vérification, audit, notes | Mainteneurs humains | Documentation audit seulement; aucun runtime |
| `fix/ci-triggers` | Correctif E1 désormais intégré (historique) | — | — |

**Précision:** Le code du Worker `align-tv-mailbox` et sa liaison à la mailbox sont présents dans le dépôt. Les journaux du BOT #1075 (24/11/2026) confirment une lecture mailbox réussie et un relais jusqu'au bridge runner ; cette preuve ne valide pas les alertes TradingView, dont les payloads ont ensuite été rejetés pour `missing_mtf_timeframe:tf=M3`. Les lecteurs externes de `live-data` et la configuration complète de GitHub Pages restent à inventorier.
