# ALIGN TRADING

**ALIGN TRADING est le nom officiel du projet.**  
**Trading Auto** / `trading-auto` est un ancien nom technique du même projet, pas un second produit ni un second dépôt.

Il n'existe qu'une seule source de vérité :

- Dépôt : [adelkhatra-bit/trading-align-](https://github.com/adelkhatra-bit/trading-align-)
- Branche du code de production : `main`
- Branche de publication des données générées : `live-data` — ce n'est pas une branche de code et elle ne doit jamais être fusionnée dans `main`.

## Règle de maintenance

Toutes les demandes, corrections, tests et mises à jour mentionnant **ALIGN**, **ALIGN TRADING** ou **Trading Auto** concernent ce même projet. Ne pas créer de dépôt, branche principale, serveur ou pipeline parallèle sous le nom Trading Auto.

- Développer un correctif sur une branche ciblée créée depuis le `main` vérifié.
- Ouvrir une PR vers `main`.
- Comparer le diff et vérifier tous les contrôles requis sur le SHA exact.
- Ne jamais fusionner ni déployer si un contrôle échoue ou si le fonctionnement réel concerné n'est pas vérifié.
- Ne jamais supprimer une branche, PR, archive ou fichier historique sans inventaire de provenance et comparaison préalable.
- Aucun ordre broker réel dans le cadre de la maintenance.

## Documentation canonique

1. [Source de vérité du projet](docs/ALIGN_SOURCE_DE_VERITE.md) — identité, branches, indicateur canonique, chaîne de données, intégrations et règles de sécurité.
2. [Carte du système](docs/ALIGN_SYSTEM_MAP.md) — architecture, flux et contrôles de fiabilité.
3. [Règles pour les agents et mainteneurs](AGENTS.md) — méthode de travail, tests, zéro régression et conditions de fusion.

En cas de contradiction, suivre `docs/ALIGN_SOURCE_DE_VERITE.md` pour l'architecture et `AGENTS.md` pour la méthode de maintenance. Ne pas déduire qu'il existe deux projets à partir de l'ancien nom Trading Auto.
