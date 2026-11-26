# ALIGN — animations et coach vocal sur TradingView

## Règle d'interprétation

Pour toute demande du propriétaire mentionnant les animations ALIGN, les bulles, la bande live ou le coach vocal **sur TradingView**, la cible est l'overlay Tampermonkey `docs/live/align-bande-live.user.js`. Il s'exécute sur les pages `https://*.tradingview.com/chart/*` et superpose directement le rendu au graphique TradingView.

Le propriétaire utilise l'indicateur ALIGN et la plateforme TradingView. La page HTTPS `/live/` n'est pas son interface d'animation ni son panneau de commande quotidien. Ne pas la confondre avec l'overlay.

## Rôles des composants

| Composant | Rôle | Règle |
|---|---|---|
| `docs/live/align-bande-live.user.js` | Overlay Tampermonkey TradingView : bande, bulles, effets, boutons, commentaires IA et voix navigateur | Surface principale à vérifier et préserver |
| `docs/live/index.html` | Scène transparente ALIGN LIVE, prévue pour TikTok LIVE Studio, avec Thomas/Leïla et animation des avatars | Auxiliaire ; pas l'overlay TradingView |
| `cloud/align-tv-mailbox/worker.js` | Worker et Durable Object `LIVE_SHOW` : relais de dialogues, état du coach et événements START/STOP | Dépendance technique à préserver tant que le producteur de dialogues l'utilise |
| `live-data/live.json` sur `live-data` | Résumé public de marché lu par la scène auxiliaire | Ne pas confondre avec les données privées de signal ni avec le script d'animation |

## Chemin vocal réel

1. Le script Tampermonkey s'exécute sur le graphique TradingView.
2. L'utilisateur active explicitement `COACH VOCAL ON` dans les commandes de l'overlay.
3. Le navigateur prononce les commentaires avec `window.speechSynthesis` et les voix système compatibles, après activation utilisateur.
4. Le script publie les événements vocaux START/STOP vers `LIVE_SHOW` ; la scène auxiliaire lit ces événements pour synchroniser l'animation de la bouche des avatars.
5. La scène `/live/` n'envoie pas le son vers TradingView : l'audio est produit localement par le navigateur qui exécute le userscript.

## Contrôles obligatoires

- Vérifier le dépôt `adelkhatra-bit/trading-align-`, la branche `main`, le SHA, la version du userscript publié et la version réellement installée dans Tampermonkey.
- Vérifier que le script est activé pour `https://*.tradingview.com/chart/*`, que le graphique affiche l'overlay et que le bouton d'animations est ON.
- Vérifier les voix réellement exposées par `speechSynthesis.getVoices()` dans le navigateur, pour `fr-FR` et `en-US` et pour les deux locuteurs. La présence d'une voix Windows dans System.Speech ne prouve pas qu'elle est exposée par Chrome.
- Vérifier l'activation ON/OFF, la réception d'un commentaire IA pour le symbole affiché, la lecture complète de la phrase, puis la séquence Thomas/Leïla si un dialogue est disponible.
- Vérifier `/show/state`, l'état `voiceEnabled` et la fraîcheur de `LIVE_SHOW`. Un état ON sans événement START ne prouve pas que la synthèse a commencé.
- Distinguer explicitement : tests de code, santé du Worker, version Tampermonkey installée, synthèse vocale démarrée et son effectivement entendu. Ne jamais déclarer la voix fonctionnelle sur la seule base d'un endpoint HTTP 200.

## Interdictions

- Ne pas supprimer `/live/`, son producteur de dialogues ou `LIVE_SHOW` simplement parce que le propriétaire n'utilise pas la page comme interface.
- Ne pas détourner une demande « animations sur TradingView » vers la page `/live/`.
- Ne pas remplacer, simplifier, renommer ou repositionner les animations et contrôles existants sans autorisation explicite.
- Ne pas substituer une voix robot ou une voix d'un autre locuteur si la voix naturelle attendue manque ; signaler la voix manquante et corriger à la source.
- Ne pas fusionner ni déployer tant que les tests concernés et le contrôle réel TradingView ne sont pas concluants.
