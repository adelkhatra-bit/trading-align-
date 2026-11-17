# Bridge TradingView ROBOT V12 isolé — préparation

Date : 2026-11-17  
Dépôt : `adelkhatra-bit/trading-align-`  
Branche dédiée : `feat/align-robot-v12-bridge-isolated-20261117`  
Base exacte : `main` — `2219ae7334eb405205bb8e4ad0a121d597d39108`

## Statut

Préparation documentaire uniquement. Aucun serveur, tunnel, service Windows, port, secret ou workflow n'a été créé, démarré ou modifié. Aucun ordre broker n'est possible par ce composant.

## Contrat de lecture attendu par ALIGN MTF BOT

Le workflow `.github/workflows/align-bot.yml` appelle :

`GET /bridge/robot-v12/mtf?symbol=BTCUSD|XAUUSD|NAS100`

Authentification attendue : `Authorization: Bearer <ALIGN_TV_READ_TOKEN>`.

La réponse doit être un JSON avec, au minimum :

- `ok: true`
- `symbol` correspondant exactement au symbole demandé
- `activeTimeframe` parmi M1, M5, M15, M30, H1, H2, H4, D1, W1
- `activeTimeframeFresh: true`
- `activeTimeframeAgeMs` et `receivedTimeframes`
- `snapshots` contenant M5, M15, H1, H4, D1 et W1, chacun avec `fresh: true`
- pour le snapshot actif : `price` strictement positif, `updatedAt` interprétable en epoch ms ou s et âgé de 30 secondes maximum, et un objet `robotV12` non vide
- les lectures ROBOT V12 attendues comprennent notamment `lecture_1m`, `lecture_5m`, `lecture_15m` et `lecture_60m`

Le bridge ne doit jamais fabriquer un prix, une bougie, une confirmation, un horodatage récent ou un snapshot manquant. Une donnée absente, périmée, incohérente ou d'un autre symbole doit rester explicitement invalide et bloquer le préflight.

## Constats techniques vérifiés

1. Le fichier Pine v25 actif dans le dépôt, SHA blob `1eccc8c8d989ade8677ff8e3d80251da464ba496`, utilise des appels `alert()` textuels et des `alertcondition()` statiques. Il ne fournit pas, dans ce fichier, le JSON structuré multi-timeframe requis par le workflow.
2. `bridge/mt5_bridge.py` est un autre composant : API MetaTrader 5 sur le port 5001, CORS wildcard, sans authentification Bearer sur ses routes, et transfert POST vers `127.0.0.1:4000/mt5`. Il ne doit pas être recyclé pour le bridge TradingView.
3. `scripts/cloudflare-oneclick.ps1` écrit dans le `config.yml` Cloudflare du profil Windows, peut arrêter ngrok, créer une route DNS et démarrer un tunnel. Il n'est pas adapté à un déploiement isolé sans refonte préalable et ne doit pas être exécuté.
4. Le clone local du PC est sur `fix/align-groq-primary-disable-gemini-20261117`, SHA `ba8ba5031c5725b8e07079e44599195aa3a6725a`, arbre de travail propre au contrôle. Ce commit est derrière `main` de 7 commits et n'est pas la base de travail du bridge.
5. Le dépôt GitHub a pour `main` le SHA `2219ae7334eb405205bb8e4ad0a121d597d39108`. La branche de préparation a été créée à partir de ce SHA exact.

## Architecture cible, à implémenter après identification du producteur de données

- Service dédié ALIGN, répertoire, identité de service, journaux et stockage propres.
- Écoute sur loopback uniquement derrière un tunnel TLS dédié ; port dédié choisi après inventaire d'occupation. Ne pas utiliser les ports 3000, 4000 ou 5001.
- Endpoint de lecture `/bridge/robot-v12/mtf`, authentification Bearer, comparaison de jeton en temps constant, taille de requête limitée, validation stricte des symboles et timeframes.
- Endpoint d'ingestion privé distinct, à définir selon le producteur TradingView réellement identifié. Ne pas accepter un texte d'alerte Pine comme substitut aux snapshots structurés.
- Cache par symbole et timeframe, horodatages UTC explicites, TTL et invalidation stricte ; aucune réutilisation silencieuse de données périmées.
- Aucun endpoint de trading, aucune fonction de passage d'ordre, aucune dépendance broker.
- Secrets conservés uniquement dans le gestionnaire approuvé et dans les GitHub Actions Secrets du dépôt ALIGN. Aucun secret dans les fichiers, commits ou logs.
- Tunnel Cloudflare ALIGN séparé, hostname appartenant à l'équipe, configuration dédiée hors du `~/.cloudflared/config.yml` partagé. Aucun tunnel ou domaine d'un autre projet ne doit être réutilisé.

## Bloqueur avant implémentation du service

Il faut identifier et vérifier le producteur réel qui observe TradingView et fournit les snapshots ROBOT V12 structurés pour BTCUSD, XAUUSD et NAS100 sur M5/M15/H1/H4/D1/W1. Le Pine v25 seul, dans son état vérifié, ne constitue pas cette source.

L'identification nécessite une inspection autorisée et en lecture seule de l'intégration TradingView locale (notamment le userscript/extension éventuellement installé), sans lire ni exporter de cookies, mots de passe ou secrets.

## Tests obligatoires avant toute exposition

- Tests unitaires du schéma, symboles, timeframes, authentification, limites de taille et timestamps.
- Rejet des données manquantes, périmées (>30 s pour le prix actif), futures, dupliquées ou d'un symbole différent.
- Tests de non-régression du préflight exact du workflow sur BTCUSD, XAUUSD et NAS100.
- Vérification TLS, rotation du token, logs sans secret, health check et redémarrage du service.
- Test end-to-end comparant chaque snapshot au graphique TradingView correspondant.
- Aucun merge ni déploiement avant revue du diff, tests verts et validation explicite.

## Hors périmètre

Ne pas modifier Pine v25, le robot de signaux, les règles MTF, Telegram, l'IA, `main` ou `live-data` dans cette phase. Ne pas arrêter ni réutiliser les services existants d'autres applications.
