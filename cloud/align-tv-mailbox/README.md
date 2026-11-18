# ALIGN — boîte aux lettres TradingView (Cloudflare Worker)

Un seul bridge, une seule validation : `align-bot/align_tv_bridge.py`.

```
TradingView (Pine v25, alerte JSON)
  → Worker align-tv-mailbox  (stocke le dernier message par marché, ne valide rien)
  → align_tv_mailbox_feeder.py dans GitHub Actions
  → align_tv_bridge.py sur 127.0.0.1:4100 dans le même runner (validation unique)
  → align_bot.py (lit le bridge comme avant, aucun changement)
```

Pourquoi : le bridge n'a plus besoin d'un PC allumé ni d'un tunnel, et il n'existe
qu'une seule logique de validation (pas de copie JavaScript à maintenir en parallèle).

Tests : `node test_worker.mjs` (8 vérifications) et
`align-bot/test_align_tv_mailbox_feeder.py` (3 tests contre le vrai BridgeStore).

Déploiement (non fait) : namespace KV `ALIGN_TV_KV`, secrets Worker
`ALIGN_TV_INGEST_TOKEN` et `ALIGN_TV_MAILBOX_TOKEN`, puis secrets GitHub
`ALIGN_TV_MAILBOX_URL` et `ALIGN_TV_MAILBOX_TOKEN`. Le branchement dans
`align-bot.yml` se fera dans une PR séparée, après déploiement et preuve réelle.
