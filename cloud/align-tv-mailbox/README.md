# ALIGN — boîte aux lettres TradingView (Cloudflare Worker)

Un seul bridge, une seule validation : `align-bot/align_tv_bridge.py`.

```
TradingView (Pine v25, alerte JSON)
  → Worker align-tv-mailbox  (Durable Object : dernier message par marché, toujours à jour, ne valide rien)
  → align_tv_mailbox_feeder.py dans GitHub Actions
  → align_tv_bridge.py sur 127.0.0.1:4100 dans le même runner (validation unique)
  → align_bot.py (lit le bridge comme avant, aucun changement)
```

Pourquoi : le bridge n'a plus besoin d'un PC allumé ni d'un tunnel, et il n'existe
qu'une seule logique de validation (pas de copie JavaScript à maintenir en parallèle).

Tests : `node test_worker.mjs` (8 vérifications) et
`align-bot/test_align_tv_mailbox_feeder.py` (5 tests contre le vrai BridgeStore).

Stockage : Durable Object (lecture toujours à jour). KV a été écarté : son cache peut dépasser
la fenêtre de fraîcheur de 30 s du bridge. Le namespace KV `align-tv-mailbox-kv` créé le 18/11 n'est plus utilisé.

Déploiement (non fait) : secrets Worker
`ALIGN_TV_INGEST_TOKEN` et `ALIGN_TV_MAILBOX_TOKEN`, puis secrets GitHub
`ALIGN_TV_MAILBOX_URL`, `ALIGN_TV_MAILBOX_TOKEN` et `ALIGN_TV_INGEST_TOKEN` (jeton d'entrée du bridge
local du runner, que le relais utilise pour lui transmettre les messages). Le branchement dans
`align-bot.yml` se fera dans une PR séparée, après déploiement et preuve réelle.

## Mise en route sans copier de jeton (18/11)
- Alertes TradingView : webhook `https://align-tv-mailbox.adel-khatra.workers.dev/ingest/tradingview`
  (aucun jeton dans l'URL ; seules les 4 IP officielles de TradingView sont acceptées).
- Lecture par le bot : jeton dérivé (HMAC-SHA256) du secret GitHub `CLOUDFLARE_API_TOKEN`,
  posé dans le Worker par le workflow « ALIGN boîte aux lettres — pose du jeton de lecture ».
  Personne ne copie ce jeton ; il n'est jamais affiché.
