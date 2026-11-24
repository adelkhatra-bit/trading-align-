# ALIGN — mailbox TradingView (Worker Cloudflare)

## Rôle

Le Worker `align-tv-mailbox` est un **transport**, pas un second bridge de validation. Il reçoit l'alerte TradingView et conserve, dans un Durable Object distinct par marché, le dernier JSON brut reçu.

La seule validation MTF du BOT est dans `align-bot/align_tv_bridge.py` (`BridgeStore`). Le Worker ne calcule pas, ne complète pas, ne convertit pas et ne valide pas les timeframes.

## Chaîne runtime

```
TradingView · Pine v25 · BTCUSD / XAUUSD
  → POST /ingest/tradingview sur ce Worker
  → Durable Object · payload brut + receivedAt par symbole
  → align_tv_mailbox_feeder.py dans le runner GitHub
  → POST inchangé vers align_tv_bridge.py sur 127.0.0.1:4100
  → BridgeStore · validation unique des 12 UT
  → align_bot.py
```

Le bridge sur 4100 démarre dans le même runner GitHub que le BOT. Il est éphémère ; il n'exige ni PC allumé, ni service Node local, ni tunnel vers le port 4100. Les jetons du bridge local sont générés aléatoirement et masqués à chaque run.

## Routes du Worker

| Méthode / route | Appelant | Fonction |
|---|---|---|
| `POST /ingest/tradingview` | TradingView, depuis l'une des quatre IP officielles autorisées | Reçoit le JSON des alertes ; aucun jeton dans l'URL |
| `POST /ingest/<ALIGN_TV_INGEST_TOKEN>` | Envoi manuel ou tests autorisés | Route à jeton, pas l'URL webhook de production TradingView |
| `GET /mailbox?symbol=BTCUSD` | Feeder GitHub Actions, Bearer `ALIGN_TV_MAILBOX_TOKEN` | Lit le dernier payload brut du symbole ; idem pour `XAUUSD` |
| `GET /health` | Contrôle technique | Retourne l'identité et l'état du Worker, sans exposer de secret |

Webhook TradingView configuré dans les alertes v25 :

`https://align-tv-mailbox.adel-khatra.workers.dev/ingest/tradingview`

Les seuls symboles acceptés sont `BTCUSD` et `XAUUSD`. Le Worker rejette un symbole absent ou incohérent. Il ne remplace pas un payload MTF incomplet par une autre source.

## Stockage et fraîcheur

- Durable Object : un espace de stockage isolé par symbole, clé `latest`.
- Le JSON est conservé brut avec `receivedAt`.
- Le Worker ne sert pas un message de plus de **10 minutes** : il retourne `ok:false, error:"empty"`.
- La fraîcheur de 10 minutes est uniquement la durée de conservation mailbox. Le bridge Python applique ses propres exigences de fraîcheur, plus strictes, à chaque UT et au prix actif.
- KV n'est pas utilisé pour le dernier snapshot ; le namespace historique `align-tv-mailbox-kv` n'est pas la source du BOT.

## Configuration runtime du relais

`align_tv_mailbox_feeder.py` utilise :

- `ALIGN_TV_MAILBOX_URL` : URL de ce Worker (valeur par défaut dans le feeder).
- `ALIGN_TV_MAILBOX_TOKEN` : jeton de lecture direct si fourni ; sinon le feeder dérive le jeton HMAC-SHA256 depuis `CLOUDFLARE_API_TOKEN`.
- `CLOUDFLARE_API_TOKEN` : secret racine utilisé pour dériver le jeton de lecture lorsqu'aucun jeton direct n'est fourni. Sa valeur n'est jamais journalisée.
- `ALIGN_TV_LOCAL_URL` : bridge Python local au runner, par défaut `http://127.0.0.1:4100`.
- `ALIGN_TV_INGEST_TOKEN` : jeton aléatoire propre au run, utilisé par le feeder pour poster dans le bridge Python local.

Le workflow `.github/workflows/align-bot.yml` démarre le bridge et le feeder lorsqu'aucun override externe `ALIGN_TV_API_URL` n'est fourni et que le secret Cloudflare requis est disponible. Il génère séparément les jetons locaux de lecture et d'ingestion. Ces jetons ne doivent jamais être copiés dans TradingView, un commit, un log public ou un message.

Si `ALIGN_TV_API_URL` / `ALIGN_TV_READ_TOKEN` sont configurés comme secrets du BOT, le workflow peut utiliser un bridge HTTPS externe au lieu de la mailbox. Il faut alors vérifier explicitement l'identité de cet endpoint et de son stockage : le seul nom de route `/bridge/robot-v12/mtf` ne suffit pas.

## Contrat de données : 12 unités obligatoires

Le JSON `payload.mtf` transmis par Pine doit contenir douze snapshots indépendants :

`M1, M3, M5, M10, M15, M30, M45, H1, H2, H4, D1, W1`.

Le Worker ne modifie pas ces clés. Le feeder transmet le payload tel quel. Le bridge Python rejette la requête si une clé obligatoire manque ou si son snapshot est invalide/périmé.

Un message de rejet tel que `missing_mtf_timeframe:tf=M3` signifie que M3 manque déjà dans l'objet JSON reçu par le bridge. Ce n'est pas une erreur de validation du Worker, et le relais ne synthétise pas M3. Vérifier le script Pine et la copie serveur enregistrée dans l'alerte TradingView ; recréer uniquement l'alerte ALIGN du marché affecté après une modification du script ou de ses paramètres. Ne jamais substituer M5 à M3.

## Différence avec le serveur historique du port 4000

Le serveur Node `server.js` et l'extension `tradingview-analyzer` sont un chemin historique distinct :

```
Extension TradingView · scrape du graphique
  → POST http://127.0.0.1:4000/tradingview/live
  → cache Node tradingview-mtf-cache.json
  → route Node /bridge/robot-v12/mtf
```

Ce chemin n'est pas le Worker mailbox et son cache n'est pas le `BridgeStore` Python du runner. Il ne doit pas être utilisé comme preuve que le BOT consomme les snapshots mailbox. Le présent document ne demande aucun arrêt, changement de port, redirection ou modification du serveur 4000.

## Tests

- `node cloud/align-tv-mailbox/test_worker.mjs` : routes, authentification, isolement des marchés et fraîcheur mailbox.
- `python -m unittest discover -s align-bot -p "test_align_tv_mailbox_feeder.py" -v` : lecture, transfert inchangé et réponse BridgeStore.
- `python -m unittest discover -s align-bot -p "test_align_tv_bridge.py" -v` : contrat de validation unique, dont le rejet des UT manquantes.

Les tests locaux/CI valident le code et le contrat. Les journaux du BOT #1075 (24/11/2026) confirment la lecture mailbox et le transfert jusqu'au bridge runner ; ils montrent aussi que les deux payloads reçus ont été rejetés parce que M3 était absent. Cela ne valide pas les deux alertes TradingView : leur copie serveur doit être vérifiée séparément.
