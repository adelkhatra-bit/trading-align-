# ALIGN — Passation réelle aux copilotes (état vérifié le 18/11 à 19 h 45)

Source de vérité : `docs/ALIGN_SOURCE_DE_VERITE.md`. Ce document liste **uniquement ce qui est vérifié**.
Aucune tâche n'est « validée » sans preuve réelle (run, URL, capture ou test).

## Vérifié (preuves)
- `main` = `79501c0` (PR #581). Suite unittest : 985 tests OK (sans modification).
- Worker `align-tv-mailbox` : `/health` = HTTP 200.
- Secrets bridge `ALIGN_TV_*` présents (valeurs masquées dans les logs).
- Run bot `44362234504` : échec volontaire à l'étape « Bridge TradingView obligatoire » (aucune donnée fraîche reçue).

## Non vérifié / à faire (par ordre)
1. **Indicateur sur TradingView** — P0
   - Graphique « Anonyme 3 » : porte l'ancien `ALIGN MTF` (réglages `8|4|0.5|1.5|20|50|20|14|5`), PAS le v25 canonique.
   - Canonique : `align-bot/pine/ALIGN_MTF_PRO_v25.pine` (titre « ALIGN MTF PRO v25 (Inside) »).
   - Action : layout séparé « ALIGN bridge » (Adel crée le layout vide), y coller le v25 avec `bridgeEnabled = true`.
   - Ne JAMAIS modifier le visuel d'« Anonyme 3 » (demande explicite d'Adel).
2. **Alertes webhook (18)** — P0
   - 3 marchés (BTCUSD, XAUUSD, NAS100) × 6 unités (5m, 15m, 1h, 4h, 1D, 1W).
   - Condition « Any alert() function call », webhook `https://align-tv-mailbox.adel-khatra.workers.dev/ingest/tradingview`.
   - Quota Essential = 20 alertes techniques : supprimer les 3 alertes de l'ancien script après.
3. **Relance du bot** — P0 : run `align-bot.yml` vert après réception des 18 snapshots.
4. **Telegram** — P1 : `setMyCommands` EN non confirmé ; boutons non testés de bout en bout ; messages et signaux à comparer à l'indicateur.
5. **IA** — P1 : tous les fournisseurs répondent 503 ou « offline » ; Anthropic : crédit épuisé. Décider d'un fournisseur de secours réel.
6. **TP et visuel** — P1 : vérifier que les TP (TP1/TP2) du graphique correspondent au plan Telegram ; NE RIEN changer au visuel.
7. **Zones / FVG / order blocks** — P2 : vérifier que le pourcentage « consommé » s'affiche comme la zone jaune.
8. **Commentaires et voix** — P2 : la voix ne doit lire que des informations réelles ; bouton « Activer le commentateur » à tester.

## Règles non négociables (Adel)
- Ne pas toucher au visuel, aux animations ni aux points d'entrée existants.
- Ne jamais quitter l'onglet TradingView d'Adel ; travailler dans un autre onglet.
- Aucune donnée inventée ; un signal n'est émis que si la confirmation est présente.
- Une PR = un problème ; merge seulement sur checks verts sur le SHA exact.
- Ne jamais créer de doublon : les copilotes et le watchdog existent déjà.
