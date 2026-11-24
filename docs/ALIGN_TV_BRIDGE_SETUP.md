# ALIGN — configuration canonique Pine v25 → mailbox Cloudflare → ROBOT V12

## Périmètre et source de vérité

Indicateur actif : \`align-bot/pine/ALIGN_MTF_PRO_v25.pine\` (\`ALIGN MTF PRO v25 (Inside)\`).

Marchés actifs : BTC (\`BTCUSD\`) et GOLD (\`XAUUSD\`) uniquement. Le bridge ne place aucun ordre broker.

**Il n'y a qu'une seule validation MTF canonique :** \`align-bot/align_tv_bridge.py\` dans le runner GitHub Actions. Le Worker Cloudflare transporte le JSON brut ; le relais le transmet sans compléter ni réécrire les unités de temps.

## Chaîne réellement utilisée par le BOT

\`\`\`
TradingView · Pine v25
  → alerte « Any alert() function call » pour BTCUSD et pour XAUUSD
  → Worker Cloudflare align-tv-mailbox · POST /ingest/tradingview
  → Durable Object · dernier payload brut par symbole
  → align_tv_mailbox_feeder.py · GET /mailbox?symbol=... puis POST inchangé
  → align_tv_bridge.py · GitHub runner, 127.0.0.1:4100
  → GET /bridge/robot-v12/mtf?symbol=... par align-bot.yml
  → align_bot.py · verdict, filtres et signaux autorisés
  → Telegram @align_mtf_adel_bot + live-data/live.json
\`\`\`

Le bridge Python sur 4100 est **éphémère, dans le même runner que le BOT**. Ce n'est pas le serveur local permanent du PC. Aucun tunnel public vers 4100 n'est requis par ce chemin ; le PC n'a pas besoin de rester allumé pour assurer le relais.

Le workflow de production démarre le bridge et le feeder quand il n'y a pas de secret \`ALIGN_TV_API_URL\` externe configuré et que le secret Cloudflare est disponible. Il crée alors des jetons aléatoires propres au run, masqués dans les logs. Le feeder lit l'URL mailbox configurée (défaut : Worker ALIGN), utilise \`ALIGN_TV_MAILBOX_TOKEN\` s'il est fourni ou dérive le jeton de lecture HMAC depuis \`CLOUDFLARE_API_TOKEN\`, puis pousse le payload inchangé vers le bridge local.

**Cas particulier :** si \`ALIGN_TV_API_URL\` et \`ALIGN_TV_READ_TOKEN\` sont configurés comme secrets, le BOT utilise ce bridge externe à la place de la mailbox/du bridge runner. Il s'agit d'une autre route. Ne pas renseigner une URL simplement parce qu'elle répond sur \`/bridge/robot-v12/mtf\` : identifier d'abord le serveur et son stockage. Le run BOT #1075 du 24/11/2026 a emprunté la voie mailbox → relais → runner 4100.

## Les deux alertes TradingView

Configurer exactement une alerte de snapshots par marché actif :

1. Ouvrir le graphique réel correspondant à BTCUSD ou XAUUSD.
2. Ajouter l'indicateur canonique **ALIGN MTF PRO v25 (Inside)**.
3. Dans les paramètres, développer **Bridge ALIGN (optionnel)**.
4. Activer **Envoyer les snapshots au ROBOT V12**.
5. Régler **Marché ALIGN** sur le symbole correspondant au graphique : \`BTCUSD\` ou \`XAUUSD\`.
6. Créer une alerte avec la condition **Any alert() function call**.
7. Utiliser le webhook Cloudflare :
   \`https://align-tv-mailbox.adel-khatra.workers.dev/ingest/tradingview\`

Le Worker accepte cette route webhook uniquement depuis les quatre adresses IP officielles de TradingView. Aucun jeton d'ingestion n'est à ajouter à l'URL TradingView. Ne pas configurer de webhook direct vers \`127.0.0.1:4100\` et ne pas utiliser le tunnel historique du serveur Node.

Il faut deux alertes distinctes : une pour BTCUSD et une pour XAUUSD. Ne pas créer une alerte par unité de temps : les douze unités sont transportées dans le même JSON.

### Important : copie serveur des alertes

TradingView conserve une copie serveur du script, de ses paramètres et du contexte du graphique au moment de la création de l'alerte. Une alerte existante n'hérite pas automatiquement des changements du Pine ni des paramètres Bridge.

Après une modification du Pine ou du paramètre Bridge, remplacer **uniquement l'alerte ALIGN du marché concerné** par une nouvelle alerte créée depuis le script v25 et les bons paramètres. Ne pas toucher aux autres alertes TradingView ni aux favoris.

## Contrat MTF exigé

Le payload \`mtf\` doit contenir douze entrées indépendantes et fraîches :

\`M1, M3, M5, M10, M15, M30, M45, H1, H2, H4, D1, W1\`.

Les neuf unités autorisées comme UT active du graphique BOT sont :

\`M1, M5, M15, M30, H1, H2, H4, D1, W1\`.

Cette liste active de neuf UT ne réduit **pas** le contrat MTF de douze UT. M3, M10 et M45 restent obligatoires dans chaque snapshot. Le bridge ne les remplace pas par M5, M15 ou M30.

Le bridge rejette un payload incomplet avec une erreur telle que :

\`\`\`text
missing_mtf_timeframe:tf=M3
\`\`\`

Cette erreur signifie que le JSON arrivé au bridge ne contient pas la clé requise dans \`payload.mtf\`. Le Worker conserve le JSON brut et le feeder le transmet sans le transformer : ils ne peuvent pas inventer ce champ. Quand le Pine canonique contient bien la construction M3, vérifier en premier la version du script et les paramètres enregistrés dans les alertes serveur TradingView, puis vérifier le payload exact à la sortie de l'alerte, sans l'exposer dans les logs publics.

Le comportement correct en cas de donnée manquante est \`WAIT\` : aucun signal ne doit être construit à partir d'une unité de remplacement.

## Serveurs à ne pas confondre

| Élément | Rôle réel | Données / contrat |
|---|---|---|
| Worker Cloudflare \`align-tv-mailbox\` | Réception webhook et stockage brut par symbole | Aucun calcul ni validation MTF ; TTL du message : 10 minutes |
| Feeder \`align_tv_mailbox_feeder.py\` | Lecture mailbox puis transfert JSON inchangé | Pas de synthèse ni de correction MTF |
| Bridge Python \`align_tv_bridge.py\` | Unique validation ROBOT V12 utilisée par le chemin mailbox du BOT | 12 UT ; cache mémoire local au runner |
| Serveur Node \`server.js\`, port 4000 | Ancien cache alimenté par l'extension \`tradingview-analyzer\` | Autre stockage \`tradingview-mtf-cache.json\`, autre flux, 9 UT |
| Extension \`tradingview-analyzer\` | Scrape le graphique et POSTe vers \`127.0.0.1:4000/tradingview/live\` | Ne transmet pas les snapshots à la mailbox Cloudflare du BOT |

**Piège critique :** le serveur Node 4000 expose lui aussi la route \`/bridge/robot-v12/mtf\`, mais son cache n'est pas celui du bridge Python. Une URL qui répond sur ce chemin ne prouve pas que le BOT lit les snapshots Cloudflare/Pine. Le healthcheck ne doit jamais considérer le cache 4000 comme preuve du bridge de production. Le port 4000 et le Worker Cloudflare ne doivent pas être arrêtés, reconfigurés ou redéployés pour corriger le flux canonique.

## Vérifications et critères de fonctionnement

Le diagnostic doit établir, pour BTCUSD et XAUUSD, dans le même run :

- réception récente par le Worker de l'alerte du bon symbole ;
- lecture HTTP 200 de la mailbox par le feeder ;
- transfert accepté par le bridge Python ;
- présence et fraîcheur des douze clés MTF ;
- prix TradingView actif positif et frais ;
- snapshot ROBOT V12 actif avec les lectures attendues ;
- préflight du BOT réussi, puis calcul de signal ou état explicite WAIT ;
- réception Telegram par le poller, dispatch d'un callback quand un bouton est réellement utilisé, et réponse Telegram confirmée ;
- publication fraîche de \`live-data/live.json\`.

Un contrôle Telegram \`getMe\` ou \`getWebhookInfo\` ne prouve pas le fonctionnement des boutons. Un message Telegram livré n'est pas nécessairement un signal de trading. Un run de validation vert ne prouve pas le fonctionnement live.

## Sécurité et limites

- Ne jamais afficher ou committer les secrets \`CLOUDFLARE_API_TOKEN\`, \`ALIGN_TV_MAILBOX_TOKEN\`, \`ALIGN_TV_INGEST_TOKEN\`, \`ALIGN_TV_READ_TOKEN\`, \`TELEGRAM_TOKEN\` ni les URLs contenant un jeton.
- Ne pas lancer d'ordre broker réel.
- Ne pas remplir les unités manquantes ou utiliser un cache issu d'une autre source.
- Aucun tunnel vers 4100 n'est requis dans le flux runner.
- Ne pas modifier le serveur 4000 ou le Worker pour diagnostiquer un payload M3 manquant.
- La CI ne compile pas Pine dans TradingView et ne prouve pas qu'une alerte serveur est créée avec le script courant.
