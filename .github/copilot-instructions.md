# Instructions Copilot — ALIGN TRADING

Avant toute action, lis `docs/ALIGN_SOURCE_DE_VERITE.md` puis `AGENTS.md`.

- Dépôt unique : `adelkhatra-bit/trading-align-`. Code sur `main`, données sur `live-data`.
- Indicateur actif : `align-bot/pine/ALIGN_MTF_PRO_v25.pine` (« ALIGN MTF PRO v25 (Inside) »). Les fichiers v24 et `*_PROPOSITION*` sont de l'historique.
- Vérifie dépôt, branche, PR, SHA, symbole et version de l'indicateur avant d'écrire. Si l'identité du projet est ambiguë ou concerne un autre projet : arrête-toi et commente.
- Une issue = une branche partie de `main` = une PR minimale. Lance `PYTHONPATH=. python -m unittest discover -s align-bot -p 'test_*.py'` avant de pousser.
- Ne fusionne jamais toi-même. La fusion dépend de la règle de `main` (`validate` vert) et de la décision du propriétaire, ou de la porte automatique une fois la PR #539 fusionnée.
- Jamais de secret en clair, jamais d'ordre broker réel, jamais de changement de design ou d'animation non demandé.
