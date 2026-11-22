# ALIGN — Rapport d'audit ChatGPT

**Mode : TEST MODE RÉEL — audit lecture seule sur le code, aucune action production.**  
**Référence :** `main` = `fe9166d68eda44c10bbee1c9cdc4f6b0bc5d7ca4`  
**Périmètre :** dépôt `adelkhatra-bit/trading-align-`.

Aucun fichier applicatif, workflow, secret, indicateur TradingView ou branche `live-data` n'a été modifié. Aucun merge, déploiement, ordre ou message Telegram réel n'a été émis. Le seul changement autorisé est ce rapport sur la branche `audit/chatgpt-pilotage`.

## 1. Branches supprimées et preuve d'archive

- Recherche GitHub authentifiée : branches distantes visibles `main` et `live-data` seulement.
- Archive locale retrouvée : `ALIGN_BRANCH_ARCHIVE_20261123.bundle`, 11 141 097 octets.
- SHA-256 recalculé : `B766A6A4C4B18CBCD90C43354EF552D551FFCAF5EB682BD1199FD645C24C82AF`.
- `git bundle list-heads` : **258 références**, ce bundle inclut des références d'audit/sauvegarde et ne correspond donc pas à 253 branches supprimées.

**Verdict : PARTIEL / NON VÉRIFIÉ.** La présence et l'intégrité de l'archive sont prouvées. La liste exacte des 253 branches supprimées (nom + SHA) et le rapprochement 62 observées / 253 annoncées / références du bundle ne sont pas certifiés. Le clone local de contrôle contient des refs `origin/*` anciennes : elles sont un cache local et ne sont pas une preuve de branches distantes actuelles. Ne pas les restaurer.

## 2. Suite de tests sur le SHA demandé

Worktree indépendant, HEAD détaché, état Git propre, SHA contrôlé :

`fe9166d68eda44c10bbee1c9cdc4f6b0bc5d7ca4`

Commande lancée depuis la racine :

`python -m unittest discover -s align-bot -p "test_*.py"`

Sortie finale exacte du runner :

```text
Ran 1139 tests in 73.546s

OK (skipped=1)
EXIT_CODE=0
```

Le premier passage affichait `OK (skipped=1)` mais le wrapper PowerShell avait signalé exit 1. Le second passage a capturé stdout/stderr avec un wrapper Python et a confirmé le code de sortie **0**. Résultat : **1139 tests, OK, 1 skipped, exit 0** sur le SHA demandé.

## 3. PR fermées : état, SHA et recommandation

Les SHA ci-dessous sont les HEAD/base enregistrés dans les métadonnées PR. Les patches ont été récupérés directement. Pour les PR ayant pour base `live-data`, le compare à `main` traverse une forte divergence historique ; les nombres ahead/behind du compare API ne sont pas le diff de la PR. Les décisions sont basées sur le patch PR et la présence de la logique dans `main`, pas sur ces compteurs.

| PR | État / base | Head SHA | Diff observé | Recommandation |
|---|---|---|---|---|
| #749 | merged / main | `416c7cb45b68a0ee719fd2a9ec214d050c30b0e8` | `.github/workflows/align-bot.yml`, gate bridge 3+/3−; 2 tests, 3+/3− et 2+/2− | **Conserver** : fusionnée dans main (`8274968689ece0e8b03840e916737aaa981f86f4`). |
| #768 | fermé sans merge / live-data | `8213870569635efb2f387800a1743d38db30df58` | Pine v24 modifié vers v25, bridge, plan M15/UT confirmées, payload | **Abandonner** : PR ancienne sur le fichier v24, incompatibilité avec parité/immutabilité; main possède déjà le Pine v25 canonique. |
| #769 | fermé sans merge / live-data | `0febf2ee282dacceba71465c3984340104b22471` | `align_bot.py` parser v25 +74/−1; tests +65; `live.json` ajouté | **Abandonner** : parser structuré v25 déjà présent dans main; patch dupliqué. |
| #770 | merged / live-data | `f97cf4545268b58ca4f9433e0408edc11f93b962` | Parser v25 +85/−3; tests +92; `live.json` ajouté | **Ne pas cherry-pick** : fusionné dans live-data seulement; parser v25 déjà présent dans main. |
| #771 | fermé sans merge / main | `b752f6cbfcc1069308b492945ff3311085ebdcff` | Workflow M15 +2; bot +3; Pine +2/−1; tests contract +7 chacun; doc +4/−4 | **Réintégration ciblée à proposer** : main valide plan M15 dans le parser, mais le workflow ne force pas encore le timeframe actif à M15. Rebase sur main et test de ce gate dans une nouvelle PR, sans cherry-pick aveugle. |
| #576 | fermé sans merge / main | `2c42a3952fd1882cd2eeb3bef727d01c5465d185` | Workflow +7/−3; test sécurité +5/−3; fallback moteur Python lorsque bridge absent | **Abandonner** : le fallback contourne la règle production de bridge TradingView obligatoire / fail-closed. |
| #751 | fermé sans merge / main | `e37a1ec06c900352fb90c9400ed3729e57af3971` | Migration clavier version 5, marquage après confirmation Telegram, tests de retry et migration | **Abandonner** : logique de migration version 5 et validation d'envoi déjà présente dans main. |
| #754 | fermé sans merge / main | `1e284afad2d542d9934bcdd3d0d8cc4147d7aa0f` | Bouton « Ouvrir mon menu ALIGN » sous message canal, tests et migration clavier | **Abandonner** : main/tests refusent explicitement ce bouton de canal; réintroduirait un bouton retiré. |

Bases SHA à l'ouverture : #749 `f2db94395b614424232f5902e5e4bb8dfdc1e3cb`; #768 `e396de02fd1e769dc862e1cfb4b7fc4b722b0a81`; #769/#770 `26321ea07261e78deb3fef60be8d7316c55909ec`; #771 `c71bc1c672a67b9f5707867be044eb1d4dad551d`; #576 `de25a93a26fd20bc8231b4460ab605556622348c`; #751/#754 `814f19841038f344bfb3b13566322b0cf7ae6d22`.

## 4. mt5_bridge.py — deux copies, importeurs non identifiés

| Fichier | Blob SHA | Taille |
|---|---|---:|
| `mt5_bridge.py` (racine) | `b55b298f82f68780d3ae231a966736afa3404acf` | 12 850 octets |
| `bridge/mt5_bridge.py` | `f65277f9bb290cbb2e641ae87105b4b9c02beb1e` | 11 815 octets |

Les deux fichiers sont différents. Scan des imports Python : **aucun `import mt5_bridge` / `from bridge.mt5_bridge` trouvé**.

- Racine : `public/dev-helper.js` référence le nom et le chemin du script. `server.js` a des références au bridge configuré via `MT5_BRIDGE`, à un message d'état et à l'arrêt de processus; le chemin de lancement par défaut est toutefois `mt5_bridge_simple.py`. Aucun import direct du fichier racine n'a été prouvé.
- `bridge/mt5_bridge.py` : auto-documentation/lancement manuel; aucun importeur ou lanceur externe direct trouvé par le scan.

**Verdict : NON VÉRIFIÉ pour l'appel effectif de chaque copie.** Garder les deux. Prochaine vérification : routes, scripts de démarrage, appels subprocess et configuration locale.

## 5. Retrait NASDAQ — plan ordonné, non exécuté

La migration de state et les garde-fous existent déjà dans main, mais des références explicites au marché retiré restent (migration/log, refus des anciennes demandes). La règle d'audit fournie par Claude est de **conserver les garde-fous**.

| Ordre | Bloc / PR distincte | Risque | Tests avant/après |
|---|---|---|---|
| a | Migration générique idempotente de `state.json`, BTC/GOLD uniquement, sans nom de marché retiré | perte de préférences/archives, état invalide | fixtures state v1–v4, conservation des clés non marché, migration répétée, sauvegarde/restore |
| b | Gestionnaire générique d'anciens boutons/callbacks inconnus; menu BTC/GOLD, aucun texte de marché retiré | callback inactif, clavier stale, spam ou double réponse | anciens callbacks, callbacks inconnus, retry, ack, zéro double envoi |
| c | Retrait ciblé des mentions opérationnelles dans `align_bot.py`, `align-bot.yml`, `scripts/align_workflow_watchdog.py`; conserver les garde-fous explicitement approuvés | marché réactivé via worker/workflow, surveillance cassée | grep ciblé, workflow lint, watchdog fixtures, tests marché et bot |
| d | Remplacer les tests nommés par des tests génériques « marché inconnu refusé » sans perte de couverture | protection insuffisante des callbacks/entrées inconnues | mêmes cas refus, tests de migration et callbacks anciens |
| e | Documentation et archives : déplacement seulement vers `archive/2026-11-23/`, aucune suppression | liens, scripts manuels ou documentation historique cassés | grep liens/imports, index d'archives, diff et tests CI |

Décisions en attente d'Adel : **MNQ dans TopStep, archivage du legacy, fichiers racine**. Aucun de ces choix n'est exécuté.

## 6. live-data — audit du contenu et plan, aucune réécriture

Audit local après fetch de la branche (lecture seule) :

- SHA live-data : `9ab907afede4d86d4cce3b78339ab887e7ea1328`
- Fichiers : **239** (confirmé)
- Diff de l'arbre à deux points `main` vs `live-data` : **129 fichiers** (confirmé)
- Commits accessibles depuis live-data : **4 209** (le nombre annoncé 4 559 n'est pas confirmé)
- Ahead/behind du compare : **3 696 ahead / 1 215 behind**
- Diff à trois points : **5 fichiers**; ceci reflète la base commune divergente, pas l'écart direct de contenu.

Plan (à soumettre à Adel, non exécuté) :
1. Inventaire des lecteurs Pages/workflows qui consomment `live-data`.
2. Snapshot de secours vérifié et sauvegarde SHA de la ref.
3. Construire un arbre de staging depuis le contenu actuel, avec seulement `live.json` et `fermes.json` (si ce sont bien les deux données contractuelles).
4. Valider les consommateurs, formats JSON, publication Pages et rollback.
5. Prévisualiser le diff complet et la ref cible.
6. **Réécriture d'historique/force-update uniquement après accord écrit d'Adel.** Ne jamais toucher à live-data avant cet accord.

## 7. Interdictions et écarts

- Aucun delete/archivage de branches, fichiers ou ref, aucune réécriture sans accord écrit d'Adel.
- Ne pas toucher `live-data`, ne pas merge dans `main`.
- Aucun ordre/trading réel, message Telegram réel ou modification TradingView.
- Aucun secret affiché.

**GEMINI_API_KEY reste référencé dans les workflows :**
- `.github/workflows/ai-check.yml:31`
- `.github/workflows/align-bot.yml:237`
- `.github/workflows/align-bot.yml:386`

C'est un écart par rapport à la décision de retirer cette variable. Signaler seulement; aucun changement.

Inventaire variables : un scan lexical brut trouve 51 tokens `ALIGN_*`, dont 45 absents des docs/AGENTS; il inclut des identifiants de logs/constants, donc ce n'est pas la liste d'environnement attendue. Un scan environnement partiel trouve 24 noms, 20 non documentés. **La liste exacte des 33 variables annoncées est NON VÉRIFIÉE**; il faut une extraction AST/usage complète, en incluant `process.env`, `os.environ`, secrets/vars YAML et les noms de variables d'étapes.

## 8. Plan d'action — une PR par problème, archivage uniquement

1. Reconstituer la liste exacte des branches supprimées depuis un manifeste pré-suppression fiable; ne pas inventer à partir du bundle de 258 refs.
2. Conserver le test vert sur SHA `fe9166d` comme baseline (1139 OK, 1 skipped, exit 0).
3. Préparer uniquement la PR ciblée de gate M15 (#771) si Adel l'autorise; rebase depuis main actuel, tests spécifiques + suite complète.
4. PR a (migration state générique) → validation production de migration avant retrait code.
5. PR b (callbacks/boutons inconnus) → tests de migration et non-régression Telegram mock.
6. PR c (code/workflow/watchdog) → grep et CI; garder les gardes.
7. PR d (tests génériques marché inconnu) → mêmes refus couverts.
8. PR e (documentation/archives) → déplacer dans `archive/2026-11-23/`, indexer, aucun delete.
9. Auditer l'import MT5 et le legacy; ne pas archiver avant preuve et accord.
10. Réécriture live-data, MNQ TopStep et fichiers racine : attente explicite d'Adel.

**Statut global :** tests main vérifiés verts sur SHA demandé. Branches supprimées (liste exacte) non certifiées. Importeurs MT5 non certifiés. Les PR sont classées selon leur patch et état API; aucun merge proposé automatiquement. Le nettoyage NASDAQ et live-data reste un plan, pas une action.

---
Rapport généré par ChatGPT; les éléments factuels sont datés du 23 novembre 2026 et attachés au SHA main indiqué.
