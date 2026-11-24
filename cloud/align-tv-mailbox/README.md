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

## Intégration au workflow de production

L'intégration du relais dans `.github/workflows/align-bot.yml` est présente sur `main`.
Quand `ALIGN_TV_API_URL` n'est pas fourni et que `CLOUDFLARE_API_TOKEN` est disponible dans le runner,
le workflow démarre pour ce run :
- un bridge `align_tv_bridge.py` éphémère sur `127.0.0.1:4100` ;
- le relais `align_tv_mailbox_feeder.py`, qui lit les symboles BTCUSD et XAUUSD dans la boîte
  et transmet chaque payload inchangé vers ce bridge.

Le workflow génère/masque les jetons locaux d'entrée et de lecture propres à ce run.
Le jeton de lecture de la boîte est dérivé du secret GitHub `CLOUDFLARE_API_TOKEN`
(sauf configuration d'un jeton direct `ALIGN_TV_MAILBOX_TOKEN`). Les alertes TradingView
n'ont aucun jeton à inclure dans l'URL standard : le Worker accepte `/ingest/tradingview`
uniquement depuis les IP TradingView autorisées.

Si `ALIGN_TV_API_URL` est fourni, le workflow choisit le mode bridge HTTPS externe et ne démarre
pas le relais Worker ni le bridge local. Les deux modes sont alternatifs, pas des étapes à chaîner.

Le endpoint public `/health` du Worker a répondu pendant le contrôle du 24/11/2026.
Cela prouve que le Worker répond, pas que des alertes TradingView récentes arrivent,
que le Durable Object est alimenté, ni que les snapshots contiennent les 12 UT MTF.
La preuve de bout en bout reste : payload frais BTC/GOLD → acceptation du bridge → BOT réussi
→ `live-data/live.json` récent.

## Mise en route sans copier de jeton (18/11)
- Alertes TradingView : webhook `https://align-tv-mailbox.adel-khatra.workers.dev/ingest/tradingview`
  (aucun jeton dans l'URL ; seules les 4 IP officielles de TradingView sont acceptées).
- Lecture par le bot : jeton dérivé (HMAC-SHA256) du secret GitHub `CLOUDFLARE_API_TOKEN`,
  posé dans le Worker par le workflow « ALIGN boîte aux lettres — pose du jeton de lecture ».
  Personne ne copie ce jeton ; il n'est jamais affiché.
