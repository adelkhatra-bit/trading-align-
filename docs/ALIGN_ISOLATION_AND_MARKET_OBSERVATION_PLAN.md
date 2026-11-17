# ALIGN — Plan directeur d’isolation et d’observation des marchés

Statut : plan de référence à mettre en œuvre par phases.
Périmètre exclusif : dépôt adelkhatra-bit/trading-align-.
Production : main. Publication : live-data.
Principe : localiser la cause, isoler la dépendance, corriger au minimum, tester, vérifier le fonctionnement réel.

## 1. Objectif général
Donner à ALIGN une infrastructure, des données, des secrets, des automatisations et une chaîne IA clairement séparés des autres projets et dépôts du compte. Réduire les dépendances croisées et rendre chaque composant identifiable, observable, restaurable et testable.
Aucun autre projet, notamment inside-dombe, ne doit être modifié dans le cadre de ce chantier.

## 2. Architecture cible dédiée
- Serveur ALIGN dédié : API, bridge TradingView ROBOT V12, endpoints de santé, journaux, redémarrage contrôlé et supervision.
- Données séparées : live.json, state.json, snapshots de marché, historique d'observations et statistiques dans des emplacements propres à ALIGN.
- Accès et secrets : secrets et variables propres au dépôt et à l'environnement ALIGN; aucun secret copié depuis un autre projet; rotation et stockage sécurisé si une exposition est suspectée.
- Automatisations dédiées : workflows GitHub Actions et tâches planifiées nommés ALIGN, permissions minimales, concurrence maîtrisée, alertes et journaux.
- Intelligence artificielle : Groq comme fournisseur principal gratuit, puis fournisseurs gratuits de secours explicitement vérifiés. Gemini désactivé dans la chaîne active selon la consigne de l'équipe. Ne jamais afficher ni journaliser les clés.
- Interfaces : TradingView, bridge, bot Telegram @align_mtf_adel_bot et site de publication restent reliés par des contrats d'API documentés et contrôlés.

## 3. Migration sans interruption
1. Inventorier l'état réel : dépôts, branches, SHA, PR, workflows, secrets présents (présence uniquement), services, processus, ports, DNS/tunnels, fichiers de données et dépendances.
2. Cartographier les flux ALIGN et les dépendances externes. Identifier les ressources partagées et les risques de collision.
3. Concevoir le serveur cible et ses frontières réseau; vérifier domaine, TLS, authentification, sauvegardes et procédure de retour arrière.
4. Déployer le serveur en parallèle, sans remplacer la production.
5. Tester health checks, authentification, bridge, données réelles, bot, IA et reprise après redémarrage.
6. Basculer une seule dépendance à la fois, avec comparaison avant/après et rollback prêt.
7. Vérifier le fonctionnement réel sur main et live-data; conserver l'ancien chemin jusqu'à validation complète.
8. Décommissionner uniquement les anciennes ressources identifiées comme ALIGN et devenues inutiles. Ne jamais toucher à une ressource d'un autre projet.

## 4. Programme d'observation des marchés — après stabilisation
Une fois l'infrastructure et les données live validées, mettre en place une à deux revues par jour pour BTC, GOLD et NASDAQ.
Chaque revue doit :
- vérifier l'heure, le symbole, la source et la fraîcheur des données;
- consulter les graphiques TradingView et les unités de temps pertinentes (M5, M15, H1, H4, D1, W1);
- comparer le prix observé aux snapshots réellement reçus par le bridge;
- relever tendance, structure, volatilité, momentum, niveaux de l'indicateur, zones de liquidité et changements de régime, uniquement lorsque les données le permettent;
- consigner les hypothèses de scénario haussier et baissier, les conditions de validation, d'invalidation et les événements à surveiller;
- mesurer ensuite ce qui s'est réellement produit, y compris les scénarios invalidés et les périodes sans signal.
La consultation visuelle de TradingView complète les données structurées; elle ne les remplace pas. Si l'accès écran ou la session TradingView est indisponible, la revue doit être marquée comme non effectuée, jamais simulée.

## 5. Statistiques et boucle d'amélioration IA / indicateur
Constituer un historique horodaté et versionné pour calculer notamment :
- fréquence et qualité des signaux par actif et unité de temps;
- taux de validation/invalidation des scénarios;
- excursions favorables et défavorables après signal (MFE/MAE);
- délai entre pré-signal, confirmation, entrée théorique et invalidation;
- comportement des niveaux Entry, SL, TP1 et TP2 calculés par ALIGN;
- performance par régime de marché, volatilité et session;
- écarts entre données TradingView, bridge et indicateur.
L'IA peut analyser ces statistiques, proposer des hypothèses et recommander des ajustements. Toute modification de Pine, du moteur de signaux ou des paramètres doit passer par une branche dédiée, un diff minimal, des tests de non-régression et une validation humaine avant fusion. Conserver une référence stable et comparer les résultats hors production avant toute activation.

## 6. Anticipation des entrées et sorties — limites de sécurité
Le système peut produire des pré-alertes conditionnelles et des scénarios probabilistes : « surveiller si… », « confirmation attendue si… », « scénario invalidé si… ». Il ne doit jamais présenter une anticipation comme une certitude ni inventer un prix ou un niveau.
Les niveaux Entry, SL, TP1 et TP2 restent calculés par l'indicateur/moteur de référence. L'IA les interprète et ne les remplace pas. Une pré-alerte n'est pas un ordre. Aucun ordre broker réel ni exécution automatique n'est autorisé dans ce programme.

## 7. Tableau de contrôle obligatoire
Avant de déclarer ALIGN opérationnel :
- dépôt, branche, PR et SHA identifiés;
- diff revu et tests verts;
- serveur et bridge authentifiés et joignables;
- snapshots BTC, GOLD et NASDAQ frais et cohérents sur les unités de temps requises;
- live.json horodaté et publié correctement;
- bot Telegram connecté et messages réellement délivrés lors d'un test autorisé;
- fournisseur IA gratuit réellement testé, nom du fournisseur et statut consignés sans secret;
- sauvegarde et rollback vérifiés;
- absence de dépendance involontaire à un autre projet confirmée.
Un workflow vert seul ne suffit pas à déclarer le live opérationnel.

## 8. Règle de conduite
Localiser le problème → isoler sa cause → corriger au minimum → tester → vérifier en conditions réelles → documenter.
Ne jamais confondre disponibilité d'un outil, résultat d'un test automatisé et fonctionnement live. Ne jamais déclarer une action réalisée sans preuve vérifiable.
