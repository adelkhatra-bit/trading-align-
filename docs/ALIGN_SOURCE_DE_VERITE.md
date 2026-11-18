# ALIGN — source de vérité unique (à lire AVANT toute action)

Ce fichier s'adresse à toute IA (Claude Code, Codex, Copilot, ChatGPT) et à tout humain.
Si une information ci-dessous contredit ce que tu crois savoir : **ce fichier gagne**.
Si une tâche ne correspond à aucune ligne de ce tableau : **arrête-toi et demande**.

## 1. Identité du projet

| Élément | Valeur canonique | Pièges connus (NE PAS utiliser) |
|---|---|---|
| Projet | **ALIGN TRADING** | Loki / KEEP, Inside Dombes, Nino & Luciole : autres projets |
| Dépôt | `adelkhatra-bit/trading-align-` | `trading-auto` (ancien nom), `trading-dashboard-4000` (autre projet) |
| Branche du code | `main` | — |
| Branche des données publiées | `live-data` (`live.json` à la racine) | Ne jamais y mettre de code, ne jamais la fusionner dans `main` |
| Indicateur actif | `align-bot/pine/ALIGN_MTF_PRO_v25.pine` | `ALIGN_MTF_PRO_v24*.pine`, `*_PROPOSITION*.pine`, `PROPOSITION_v25_sniper.diff` = historique |
| Titre TradingView | `ALIGN MTF PRO v25 (Inside)` (court : `ALIGN MTF v25`), Pine `//@version=6` | Tout autre titre = mauvais script |
| Marchés | BTC, GOLD, NASDAQ (`BTCUSD`, `XAUUSD`, `NAS100`) | — |
| Bot Telegram | `@align_mtf_adel_bot` | — |
| Bande live | `docs/live/align-bande-live.user.js` (Tampermonkey) | Copies locales anciennes (12.2.3, 12.2.4…) |
| Bridge TradingView | `align-bot/align_tv_bridge.py`, port **4100** | Ports 3000 / 4000 / 5001 et l'ancien tunnel `server.js` |

## 2. Chaîne de données (une seule)

```
TradingView (indicateur v25, alerte « Any alert() function call »)
  → bridge ROBOT V12 (align_tv_bridge.py, HTTPS dédié → 127.0.0.1:4100)
  → align-bot.yml (lit /bridge/robot-v12/mtf avec ALIGN_TV_READ_TOKEN)
  → align_bot.py (filtres news / R:R / risque)
  → Telegram (@align_mtf_adel_bot) + live-data/live.json
  → bande live (texte, animations, voix)
```

Règle : quand `ALIGN_REQUIRE_TV_BRIDGE=1`, **aucun repli** sur des niveaux calculés ailleurs.

## 3. Règles d'unité de temps (confusion connue)

- Le **plan** (Entry / SL / TP1 / TP2) est calculé sur **M15 clôturé**.
- Le **déclencheur** dépend de la stratégie : SCALPING = M1, DAY = M5, SWING = H1.
- Un même timeframe ne doit avoir **qu'une seule** direction dans un message.
  Écart connu à corriger (non encore prouvé en direct) : dans le payload bridge du v25,
  `lecture_5m` / `lecture_15m` utilisent la bougie clôturée (`d5Fermee`, `d15Fermee`)
  alors que `mtf.M5` / `mtf.M15` utilisent `d5Strat` / `d15Strat`, la bougie courante pour BTC.
- Un TP déjà touché ne redevient jamais un objectif ; un signal dont le SL est dépassé n'est jamais réémis.

## 4. Fusion : qui peut fusionner quoi

- Règle GitHub active sur `main` : **aucune fusion sans le contrôle `validate` vert** sur le dernier commit,
  suppression et réécriture forcée interdites. Elle s'applique à tout le monde, IA comprises.
- Seule la porte `.github/workflows/align-auto-merge.yml` fusionne automatiquement, et seulement si :
  dépôt identique, contrôles verts sur le SHA exact, revue Codex de ce SHA sans remarque, état `clean`.
- Une PR = un sujet. Toujours partir de `main` à jour. Ne jamais réutiliser une branche d'une autre PR.

## 5. Secrets (noms seulement — jamais les valeurs)

| Secret | Rôle | État au 18/11/2026 |
|---|---|---|
| `TELEGRAM_TOKEN` | Bot Telegram | présent |
| `GROQ_API_KEY`, `ANTHROPIC_API_KEY` | IA des commentaires | présents |
| `GEMINI_API_KEY`, `OPENAI_API_KEY` | IA de secours | absents |
| `METAAPI_TOKEN`, `TOPSTEP_API_KEY`, `TOPSTEP_USERNAME` | Comptes (mode test) | présents |
| `ALIGN_TV_API_URL`, `ALIGN_TV_READ_TOKEN` | Bridge TradingView | **absents → le bot s'arrête au préflight** |
| `COPILOT_GITHUB_TOKEN` | Relais / assignation Copilot | **absent → Copilot ne peut pas être assigné** |

## 6. Interdits absolus

- Aucun ordre broker réel ; `AUTO_TRADE` et `TOPSTEP_REEL` restent à `0` tant que le propriétaire ne dit pas « réel ».
- Ne jamais afficher, copier ou committer la valeur d'un secret.
- Ne jamais modifier le design, les animations ou l'indicateur sans demande explicite.
- Ne jamais supprimer un fichier, une branche ou une PR d'un autre agent.

## 7. Limite honnête

Les IA qui travaillent **dans** le dépôt (Copilot, Codex, Claude Code) lisent ce fichier.
Une conversation ChatGPT ouverte ailleurs ne le lit pas d'elle-même : colle-lui ce lien en premier message.
Ce qui protège vraiment `main`, c'est la règle GitHub du point 4, pas ce texte.
