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


## Annexe A — 78 fichiers racine sans référence par basename

Scan sur SHA main `fe9166d` : 93 fichiers racine `.md/.bat/.json`, recherche du basename dans 199 fichiers sous `align-bot/`, `scripts/`, `cloud/`, `docs/`, `.github/`. 78 candidats sans match textuel. **Ce n'est pas une preuve d'inutilité** (usage manuel, glob, chemins indirects ou workflows non détectés possibles). Aucun fichier n'est supprimé ou archivé.

```text
.instructions.md
4_CLARIFICATIONS_VERROUILLEES.md
ACTION_CHECKLIST.md
AGENTS_INTEGRATION_REPORT_2026-04-05.md
AGENT_BUS.json
AGENT_SYSTEM_PLAN.md
ARCHITECTURE_ANALYSIS.md
ARCHITECTURE_DESIGN.md
ARCHITECTURE_DESIGN_CORRECTED.md
ARCHITECTURE_LOCAL_ONLY.md
ARCHIVE_MANIFEST.md
AUDIT_AGENTS_DETAILED.md
AUDIT_EXISTANT.md
AUDIT_PHASE1_INVENTORY.md
AUDIT_SYSTEM_LIVE_COMPLETE.json
AUDIT_SYSTEM_LIVE_READABLE.md
CAHIER_DES_CHARGES_ALIGN_MTF_TELEGRAM.md
CANAL_WORKFLOW_FINAL.md
CHARTS_ARCHITECTURE_RECOMMENDATION.md
CLEANUP_PLAN.md
CURRENT_TASK.md
CURRENT_TASK_LIVE.md
DECISION_FORM.md
DEPENDENCY_VERIFICATION_REPORT.md
DO_NOT_TOUCH.md
ENDPOINTS_SPECIFICATION.md
ESTIMATION_FINALE.md
EXECUTION_SUMMARY.md
EXECUTIVE_SUMMARY.md
EXECUTIVE_SUMMARY_PHASE2.md
EXTENSION_ARCHITECTURE_ANALYSIS.md
EXTENSION_UI_SPECIFICATION.md
FINAL_AUDIT_REPORT.md
FINAL_REALTIME_ARCHITECTURE_COMPLETE.md
IMPLEMENTATION_GUARDRAILS.md
IMPLEMENTATION_PLAN_FINAL.md
IMPORT_VERIFICATION_CRITICAL_FINDING.md
LOCKED_PRICE_CONTEXTUAL.md
MARKET_DECISION_MATRIX.md
MARKET_DETECTION_EXPLAINED.md
MARKET_INTEGRATION_PLAN.md
MISSING_FILES_REPORT_2026-04-05.md
PENDING_TASKS.md
PHASE11_COMPLETE.md
PLAN_EXECUTION_FINAL.md
PLAN_EXECUTION_REVISED.md
PRICE_DEFINITIONS_FINAL.md
PROGRESS_LOG.md
PROJECT_STATUS.md
READINESS_SUMMARY.md
REALTIME_CANDLE_ARCHITECTURE.md
REALTIME_SYSTEM_STATUS.md
SAFE_MODE_CONFIG.json
SECURITY.md
SERVER_CONTROL.bat
START_BRIDGE.bat
START_DIRECT_WEBHOOK.bat
SUPPRESSION_STRATEGY.md
SYSTEM_AUDIT_EXTENSION_ANALYSIS.md
SYSTEM_CONTROL_PANEL.md
SYSTEM_GLOBAL_HISTORY_2026-04-05.md
SYSTEM_HISTORY.md
SYSTEM_MAP.md
SYSTEM_STATUS.md
TASK_PROTOCOL.md
TEST_REAL_TIME_FLOW.md
THREE_FINAL_LOCKS.md
TICK_SOURCE_AND_SYMBOL_RULES_FINAL.md
USER_REFERENCE_PRICE_ANALYSIS.md
VALIDATION_AVANT_CODING.md
VALIDATION_FINAL.md
WAKE_UP_SUMMARY.md
WORKFLOW_SYSTEM_LOCK.md
WORKSPACE_MAP.md
library.json
logs.json
mt5_data.json
tasks.json
```


## Annexe B — Variables, scan partiel

Le scan environnement partiel (lecture `os.environ/getenv`, expressions GitHub et clés YAML) a trouvé 24 noms, dont 20 absents de `docs/` et `AGENTS.md`. Il ne couvre pas complètement toutes les formes `process.env` et variables indirectes; ce n'est pas la liste définitive des 33 demandées.

```text
ALIGN_AI_HEALTHY_PROVIDER
ALIGN_ENVOI_CLAVIER_SPONTANE
ALIGN_ETAT_VIERGE_OK
ALIGN_EXIGER_MEMOIRE
ALIGN_FERMES_LIVE_DATA
ALIGN_LIVE_24H
ALIGN_LIVE_LIEN
ALIGN_LIVE_SUJET
ALIGN_NOTIF_MAX_JOUR
ALIGN_PARITE_RESEAU
ALIGN_QUESTION_QUOTIDIENNE
ALIGN_REGLES_PRIVEES_SPONTANEES
ALIGN_RELANCE_VIP_SPONTANEE
ALIGN_TOKEN_FILE
ALIGN_TV_API_URL_SECRET
ALIGN_TV_BRIDGE_PORT
ALIGN_TV_BRIDGE_PRET
ALIGN_TV_LOCAL_URL
ALIGN_TV_MAILBOX_URL
ALIGN_TV_RELAY_INTERVAL
```


## Addendum — corrections obligatoires et inventaire P0 (23 novembre 2026)

### Corrections des chiffres
- **live-data :** SHA de tête confirmé par Adel = `73c28134`; compteur indiqué = **4 563 commits**. Les anciennes valeurs `9ab907af` / `4 209` du rapport précédent sont obsolètes et doivent être remplacées. Le SHA complet et le nombre de commits restent **NON VÉRIFIÉS par lecture API dans ce addendum**.
- **PR #770 :** selon les informations fournies par Adel, elle a été fusionnée dans `live-data` au commit `100a89e1`, avec modifications de `align_bot.py` et `test_align_mtf.py`. Ceci est un écart à la règle « aucun code dans live-data ». À traiter comme incident de gouvernance/historique : ne pas réécrire ni supprimer; préserver la preuve; proposer à Adel une stratégie corrective (snapshot de la ref, analyse du diff, puis décision explicite de restauration/reconstruction uniquement après autorisation écrite). Aucun cherry-pick/merge automatique vers `main`.
- **Fichiers racine :** référence annoncée par Adel = **95 fichiers .md/.bat/.json**, dont **80 non cités par nom** dans le relevé antérieur. Le relevé précédent ne contient que **78 noms** dans l'annexe A; il ne réconcilie donc pas le décompte et ne peut être considéré comme la liste exacte des 80. Les 78 noms déjà listés restent un relevé provisoire, sans suppression ni archivage. L'extraction complète de 95 noms, puis la comparaison nom par nom avec les 80 attendus, est **NON VÉRIFIÉE**.

### P0 — Inventaire de branchements, lecture seule obligatoire

Les items suivants restent à obtenir par commande/API et sortie sauvegardée; aucune configuration n'est modifiée :

1. **GitHub Pages** — GET `/repos/adelkhatra-bit/trading-align-/pages`: branche source et dossier servi. **NON VÉRIFIÉ** dans ce addendum.
2. **Cloudflare Worker `align-tv-mailbox`** — branche de build et chemin surveillé; configuration textuelle/capture de texte à fournir. Aucun accès Cloudflare ni preuve de configuration n'est établi ici. **NON VÉRIFIÉ**.
3. **Workflows** — extraire chaque `branches:` de tous les fichiers `.github/workflows/*.yml` et noter l'événement/branche attendue. **NON VÉRIFIÉ**.
4. **Rulesets** — règles actives ciblant `main` et `live-data`. Lecture API des rulesets requise; règles actives **NON VÉRIFIÉES**.
5. **Dernier run `align-bot.yml` sur `main`** — conclusion, URL/run ID et job/étape en échec (ou preuve de succès). **NON VÉRIFIÉ**; en l'absence de cette preuve, l'état « ça fonctionne » demeure NON VÉRIFIÉ.

### Plan P0–P8 (sans exécution avant accord écrit)
- **P0** Inventaire ci-dessus, rapport uniquement.
- **P1** `live-data`: plan de réécriture vers les seuls `live.json` et `fermes.json`, chemins inchangés; soumettre à Adel. Aucun write avant accord.
- **P2** `state.json`: migration générique BTC/GOLD seulement, sans nommer le marché retiré; fixtures préférences, archives et clés hors marché; production uniquement après merge.
- **P3** callbacks inconnus: route générique vers menu BTC/GOLD; aucun bouton sans action.
- **P4** retrait ciblé du marché retiré dans `align_bot.py`, `align-bot.yml`, `scripts/align_workflow_watchdog.py`, une PR par bloc.
- **P5** remplacer tests « marché retiré refusé » par « marché inconnu refusé »; aucune protection retirée sans remplacement.
- **P6** docs/archives seulement après accord d'Adel.
- **P7** Telegram réel uniquement sur canal de test explicitement autorisé, après merge; jamais sur canal client.
- **P8** rapport final avec preuves vérifiables.

### Règles rappelées
Tout merge sur `main` redémarre le bot : avertir Adel avant chaque merge. Aucun code dans `live-data`. Pas de suppression de branche sans manifeste (nom, SHA, bundle et SHA-256). Pas de réécriture d'historique sans accord écrit. Aucun ordre/trading réel, aucun changement à l'indicateur TradingView.



## Addendum — reprise ordonnée P0 / E1 (23 novembre 2026, lecture 00:49 CET)

### Étape 1 — run 45067670356 (lecture seule)
- Commande/API connector : `fetch_workflow_run_jobs(run_id=45067670356)` puis `fetch_workflow_job_steps(job_id=137347565750)` et `fetch_workflow_job_logs(job_id=137347565750)`.
- Heure de lecture : **2026-11-23 00:49:13 CET** (UTC+01:00).
- Jobs : `signaux` = `in_progress`, conclusion `null`; `validate` = `skipped`.
- Étape en cours : **Analyse BTC + Gold et envoi Telegram** (step 12). Les étapes 1 à 11 sont success; les steps 13 à 19 restent pending.
- Dernière ligne de log disponible : **2026-11-22T23:28:42.5715692Z**. Le job est encore actif, mais aucun log n'a été produit depuis environ 20 min au moment de la lecture.
- `timeout-minutes=355` et démarrage `2026-11-22 20:40 UTC` → échéance calculée **2026-11-23 02:35 UTC (03:35 CET)**. À 00:49 CET, le run n'a pas encore dépassé cette échéance; donc « in_progress » est inquiétant mais **pas encore une anomalie de dépassement du timeout**. Recontrôler après l'échéance.
- Cache `state.json` : log de restauration indique `Cache restored from key: align-etat-45054398305-b1795380009`. C'est la clé effectivement restaurée par ce run. Elle correspond au run précédent et constitue le candidat de sauvegarde pré-run; la liste API de tous les caches n'est pas accessible ici, donc **dernière clé sauvegardée de manière absolue NON VÉRIFIÉE**.
- **Note D6 préparée, sans annulation** : ne pas cancel. Le job est encore dans l'analyse/envoi, cache `state.json` restauré depuis la clé ci-dessus, sauvegarde finale non encore confirmée. Décision propriétaire requise après vérification de l'état final et des risques de double message; à ce stade la recommandation est de ne pas annuler.
- Runs `align-bot.yml` en `queued` sur `main` depuis le 22/11 : **NON VÉRIFIÉ**. La liste des runs n'est pas exposée par le connecteur GitHub disponible; l'accès API direct via Web est inaccessible. Aucun run queued n'a été inventé.

### Étape 2 — P0 restant, lecture seule
- Pages (`GET /repos/adelkhatra-bit/trading-align-/pages`) : accès endpoint refusé/inaccessible par les outils disponibles; source branch et served folder **NON VÉRIFIÉS**.
- Rulesets (`GET /repos/adelkhatra-bit/trading-align-/rulesets`) : endpoint inaccessible; règles actives main/live-data **NON VÉRIFIÉES**.
- Cloudflare Worker `align-tv-mailbox` : aucun connecteur Cloudflare de lecture/configuration/déploiement disponible; build branch, path surveillé et dernier deployment **NON VÉRIFIÉS**.
- Heure de lecture : 23/11/2026, 00:49 CET.


### Étape 3 — E1 PR #779 (effectuée, non fusionnée)
- Branche `fix/ci-triggers` créée depuis `main` (`main` SHA de base `fe9166d68eda44c10bbee1c9cdc4f6b0bc5d7ca4`).
- Fichier unique modifié : `.github/workflows/ci-integration-tests.yml`.
- Diff exact : `branches: [main, feature/**, deploy/**]` → `branches: [main]`. Le `pull_request.branches: [main]` et tous les autres chemins/contenus restent inchangés.
- Blob avant : `210b8b3f092a07ffe7d641734877139dfb91d616`; blob après : `a05e96d75bb895ca68ceefbe3005b86a1a2927a9`.
- Commit : `dc37d53f64a844e4275d47e18e5e56bf1afa74c9`.
- Validation locale : PyYAML `safe_load` réussit; parse du YAML OK; push branches résolues = `[main]`; pull_request branches = `[main]`. `actionlint` absent de l'environnement (`ACTIONLINT_NOT_INSTALLED`).
- Patch relu via API : un seul fichier, 1 addition / 1 suppression, exactement la ligne `push.branches`.
- PR ouverte : https://github.com/adelkhatra-bit/trading-align-/pull/779 — base `main` SHA `fe9166d68eda44c10bbee1c9cdc4f6b0bc5d7ca4`, head `fix/ci-triggers` SHA `dc37d53f64a844e4275d47e18e5e56bf1afa74c9`. État open, non merged, changed_files=1.
- Pas de relance production `align-bot.yml` attendue par ce PR : le bot est déclenché par `workflow_run` de validation main (branches main), schedule ou workflow_dispatch; PR validation sur la branche `fix/ci-triggers` n'est pas un `workflow_run` de main. Workflow `align-bot.yml` non modifié.

### Mise à jour source de vérité (document existant seulement)
- `docs/ALIGN_SOURCE_DE_VERITE.md` mis à jour sur la branche d'audit uniquement; tableau branches / rôle / lecteurs / écrivains ajouté, avec lecteurs Pages/Cloudflare explicitement marqués non vérifiés.
- Commit : `324350d8bcd73d25ab334e53fd715a8cf824d0d9`; blob : `61b9f42f43af6ed569545f870dbacf31f7a43850`.
- Aucun autre document de source de vérité créé. Aucun changement sur `main` ou `live-data`.


### E1 — checks GitHub du PR #779 (lecture du 23/11/2026 00:49 CET)
- `CI Integration Tests` run **45085342038** : completed / success. Job `integration_tests`, steps 1–9 et cleanup success; test backend smoke passed. URL : https://github.com/adelkhatra-bit/trading-align-/actions/runs/45085342038
- `ALIGN MTF validation` run **45085342088** : `in_progress`. Job `validate`; steps 1–12 success, step 13 **Run complete MTF regression suite** in progress. URL : https://github.com/adelkhatra-bit/trading-align-/actions/runs/45085342088
- Fetch des workflow runs associés au commit PR `dc37d53f64a844e4275d47e18e5e56bf1afa74c9` ne retourne que CI Integration Tests et ALIGN MTF validation; aucun run `align-bot.yml` n'apparaît dans cette liste de runs PR. Cela confirme qu'aucune relance bot production n'a été observée associée au commit PR à cette heure.
- **PR #779 reste ouverte, non fusionnée.** Attendre la conclusion du MTF validation; ne pas merger.


## CORRIGENDUM — PR #779 fusionnée et suivi rollover (lecture 23/11/2026 00:56 CET)

Correction explicite du rapport précédent : **la PR #779 n'est plus ouverte. Elle est fusionnée dans `main`** via le commit `0a38036e1bd9a6244d6d1a7c0634eb1731fef4c6`. Le diff API du commit confirme uniquement la ligne `push.branches` de `.github/workflows/ci-integration-tests.yml`, de `[main, feature/**, deploy/**]` à `[main]`. Les 1139 tests OK / 1 skipped / exit 0 sont la vérification rapportée par Claude, pas une sortie de test exécutée dans cette session.

**Heures de lecture des données GitHub :** 23/11/2026 00:54–00:56 CET (UTC+1), horodatages API/log en UTC ci-dessous.

### 1. Rollover associé au commit `0a38036e`

Run `45085640005` (#378), workflow `ALIGN worker rollover`, déclenché sur `main` et SHA `0a38036e1bd9a6244d6d1a7c0634eb1731fef4c6`. Conclusion `success`; job `retire_previous_worker` success. Log relu à 00:55:28 CET.

Lignes émises par le rollover (UTC; +1 h pour CET) :
- `2026-11-22T23:53:40.0140425Z ROLLING_OVER old_run=45067670356 old_sha=fe9166d68eda` → 23/11 00:53:40.014 CET
- `2026-11-22T23:53:40.0141211Z ALIGN_OLD_WORKERS_STOPPED_GRACEFULLY validated_sha=0a38036e1bd9` → 00:53:40.014 CET
- `2026-11-22T23:53:40.0141668Z ALIGN_OLD_WORKERS_STOPPED validated_sha=0a38036e1bd9` → 00:53:40.014 CET
- `ROLLING_OVER_RETRY` : **aucune ligne émise** dans le log récupéré.
- `FORCE_RETIRING` : **aucune ligne émise**.
- `ROLL_OVER_RACE` : **aucune ligne émise**.

Le log montre donc un arrêt gracieux confirmé, pas une retraite forcée ni une course de rollover. Run : https://github.com/adelkhatra-bit/trading-align-/actions/runs/45085640005

### 2. Run 45067670356 (#1038) — cancelled, sauvegarde exécutée

Lecture API run : 00:56:02 CET; `status=completed`, `conclusion=cancelled`, `updated_at=2026-11-22T23:53:32Z` (23/11 00:53:32 CET). Le job `signaux` a néanmoins `conclusion=success`; le job `validate` est `skipped`.

Le log confirme l'étape d'arrêt `ALIGN_STATE_SAVED_ON_SHUTDOWN` à `2026-11-22T23:53:26.7843294Z` (23/11 00:53:26.784 CET), puis deux sauvegardes cache :
- `Cache saved with key: align-etat-45067670356-a1795391607` à `2026-11-22T23:53:27.6076482Z` (00:53:27.607 CET).
- `Cache saved with key: align-etat-45067670356-b1795391607` à `2026-11-22T23:53:27.9461231Z` (00:53:27.946 CET).
Les deux actions de sauvegarde sont `if: always()` dans le workflow relu. **Sauvegarde finale state.json : preuve positive dans le log**. La cancellation a eu lieu après les sauvegardes; le rollover a ensuite confirmé l'arrêt gracieux.

Run #1038 : https://github.com/adelkhatra-bit/trading-align-/actions/runs/45067670356

### 3. Worker suivant — run 45085640139 (#1039)

Lecture API à 00:56:02 CET : `in_progress`, conclusion `null`, SHA `0a38036e1bd9a6244d6d1a7c0634eb1731fef4c6`, événement `workflow_run`, started_at `2026-11-22T23:53:13Z` (23/11 00:53:13 CET). Job `signaux` actif; étape 12 `Analyse BTC + Gold et envoi Telegram` est `in_progress`; étapes 1–11 success. L'étape 4 `Attendre la fin de l'ancien worker (sa sauvegarde de mémoire)` est `completed`, donc l'attente de concurrence est terminée et le worker ne paraît pas bloqué derrière #1038. Les logs du job actif n'ont pas été récupérés (404 BlobNotFound); durée exacte de l'attente **NON VÉRIFIÉE**.
Run : https://github.com/adelkhatra-bit/trading-align-/actions/runs/45085640139

### 4. Cache `align-etat-*`

- Cache le plus récent dont la sauvegarde est prouvée dans les logs récupérés : `align-etat-45067670356-b1795391607`, save à 00:53:27.946 CET.
- Une sauvegarde a également été confirmée avec clé `align-etat-45067670356-a1795391607`, à 00:53:27.607 CET.
- L'inventaire API `GET /repos/adelkhatra-bit/trading-align-/actions/caches?per_page=100` est refusé par le fetcher (endpoint non autorisé). La clé la plus récente parmi **tous** les caches du dépôt et sa date de création API : **NON VÉRIFIÉ**.

### 5. Pages, rulesets, Cloudflare — lecture seule

- Pages : `GET /repos/adelkhatra-bit/trading-align-/pages` — fetch GitHub API rejeté (endpoint non autorisé). Le navigateur sur `/settings/pages` affiche une page not found/sign-in; ce n'est pas une preuve de configuration Pages. Source branch et folder **NON VÉRIFIÉS**. Lecture 00:55–00:56 CET.
- Rulesets : `GET /repos/adelkhatra-bit/trading-align-/rulesets` et `GET /repos/adelkhatra-bit/trading-align-/rulesets/27552606` — réponse lue à 00:55:55 CET : un ruleset `ALIGN main - aucune fusion sans tests verts`, `enforcement=active`, `include=[~DEFAULT_BRANCH]`, règles deletion, non-fast-forward et status `validate` requis, `bypass_actors=[]`, `current_user_can_bypass=never`. Cela cible la branche par défaut (main), **pas de ruleset live-data retourné**. Aucun changement.
- Cloudflare Worker `align-tv-mailbox` : aucune API/connexion Cloudflare disponible; branche build, path surveillé et dernier déploiement **NON VÉRIFIÉS**. Lecture 00:56 CET.

### 6. PR #779 — statut corrigé

PR #779 est merged, pas ouverte. Commit de merge : `0a38036e1bd9a6244d6d1a7c0634eb1731fef4c6`. Compare API confirme le seul changement E1; main est maintenant à ce SHA selon l'information fournie et le commit relu. URL : https://github.com/adelkhatra-bit/trading-align-/pull/779

### 7. Source de vérité — PR documentaire proposée

Une PR documentaire unique **#780** a été ouverte depuis `docs/align-source-truth-readers-writers-20261123` vers `main`, basée exactement sur `0a38036e1bd9a6244d6d1a7c0634eb1731fef4c6`. Elle ajoute une table branche/rôle/lecteurs/écrivains dans le document existant `docs/ALIGN_SOURCE_DE_VERITE.md` (un seul fichier, 12 additions, 0 deletion). Aucun code, workflow, live-data ou autre document n'est modifié. Diff relu et vérifié.
- Commit PR : `aaffd65ec80a15abe7963a30d5d24fb71c403437`
- Blob : `1551046315311e08b8da83525dcd9dc7cdf9eec2`
- PR : https://github.com/adelkhatra-bit/trading-align-/pull/780
- État : open, **non fusionnée**. Le champ mergeable n'est pas interprété comme une autorisation. Aucun merge effectué.

### 8. Risques et décisions

- **D6 : fait établi** — rollover a annulé #1038; les deux caches de state.json ont été sauvegardés avant la cancellation, et le rollover log confirme l'arrêt gracieux. Pas besoin d'une décision cancel maintenant; le run est déjà cancelled.
- **D7 : toujours à Adel** — garder ou supprimer la logique d'annulation/retrait automatique du worker actif. Le rollover actuellement configuré a arrêté #1038 gracieusement; aucune modification du workflow `align-bot-rollover.yml` n'a été faite.
- Runs queued depuis le 22/11 : **NON VÉRIFIÉ** (endpoint list workflow runs non accessible; page publique affiche seulement les runs récents).
- Aucune annulation, relance, merge, écriture live-data, suppression, trading ou message Telegram réel n'a été effectué dans cette reprise.


## Addendum — IA gratuites / G1–G3 (23/11/2026, lecture GitHub 01:13 CET)

### Référence et clone isolé
- `main` vérifié : `006280ef214f5c82ea010f5647e9d444b93b5417` (merge #780). Lecture API branche `main` à 01:13 CET.
- Clone propre séparé, créé à partir de ce SHA et vérifié propre : `ALIGN_CANONICAL/trading-align-/g1-clean-006280ef`. L'ancien workspace n'a pas été réutilisé.
- Le clone a été conservé propre après suppression des scripts de patch temporaires : `git status --short --branch` = `## main...origin/main`, `git diff --stat` vide. SHA local vérifié : `006280ef214f5c82ea010f5647e9d444b93b5417`.

### G1 — résultat de l'intervention
- Référence code lue : `align-bot/align_bot.py` blob `76d3059ec9c3666a52e595b80617aad4aba66bec`.
- Références tests lues : `test_align_mtf.py` blob `68c59190f819624d60d72872b1c68b8690e74ab7`; `test_ia_provider_config.py` blob `9ef8b515a4330220222a2a3f33ad0b87489d62d4`.
- Compte avant : 1142 méthodes `test_*` dans 70 fichiers `align-bot/test_*.py` (calcul AST sur clone propre).
- Patch de retrait Gemini tenté sur script temporaire; échec de syntaxe/regex avant toute écriture des fichiers source. Scripts temporaires supprimés et clone re-vérifié propre. Aucun code source modifié.
- Compte après : NON EXÉCUTÉ, car G1 n'a pas été appliqué. Aucun compte ne doit être annoncé après sur un patch absent.
- PR G1 : non créée. Tests complets : NON EXÉCUTÉS. Aucun merge.

### Production — preuve réelle IA
- Dernier run `align-bot.yml` terminé sur `main` au moment de la lecture : #1038, ID `45067670356`, conclusion `cancelled`. Job `signaux` terminé `success`. Run #1039 (`45085640139`) reste `in_progress` au moment de la vérification.
- Run #1038, logs relus : `AI_PROVIDER_STATUS Groq=CONNECTED model=openai/gpt-oss-120b` à `2026-11-22T20:40:23.6873035Z (`21:40:23 CET`). Préflight confirmé connecté.
- Ligne de réponse réelle : `2026-11-22T23:00:25.2325989Z AI_PROVIDER_USED=Groq model=openai/gpt-oss-120b` (23/11 00:00:25 CET). Groq a donc réellement répondu au bot dans ce run.
- Dernier succès externe dans les logs : `2026-11-22T23:50:47.3592493Z AI_PROVIDER_USED=Pollinations model=openai` (23/11 00:50:47 CET). Après cela, les dernières lignes montrent `AI_PROVIDER_USED=INTERNAL_FALLBACK` et `AI_ALL_PROVIDERS_FAILED`, dernière paire à `2026-11-22T23:53:23.7066822Z / `23:53:23.7067491Z` (23/11 00:53:23 CET). Les appels ne sont donc pas restés opérationnels jusqu'à la cancellation.
- Lien du run : https://github.com/adelkhatra-bit/trading-align-/actions/runs/45067670356
- Run #1039 et logs actifs : status API `in_progress`; téléchargement des logs échoue `404 BlobNotFound`. Aucun fournisseur final de ce run ne peut être confirmé.

### Plan séquencé demandé par Adel
- G1 : retrait Gemini et tests de remplacement, sans baisse du nombre de tests. En attente d'un patch fiable et d'une suite complète verte.
- G2 Cerebras : après G1 verte seulement. Vérifier endpoint/model exclusivement dans la documentation officielle Cerebras; fournisseur après Groq; clé `CEREBRAS_API_KEY` et plafond journalier; clé créée par Adel.
- G3 OpenRouter :free : optionnel, après G2 verte; modèle épinglé depuis `openrouter.ai/models`, clé `OPENROUTER_API_KEY`.
- Aucun fournisseur ajouté/réinstallé, aucun secret créé/affiché, aucun merge, aucune annulation ou relance, aucun changement rollover, aucun message Telegram réel, aucune écriture `live-data`.


## Addendum — boutons Telegram, runs #1038/#1039, test offline (23/11/2026)

### Horodatage de lecture GitHub
- Dernière lecture GitHub : **2026-11-23 01:22:25 CET**.
- Branche `main` vérifiée : `006280ef214f5c82ea010f5647e9d444b93b5417`.
- Branche d'audit avant cet ajout : `bc5c41f2df177cbb4a4e38535eb4ccfb94f8aac8`.
- Aucun code du bot sur `main` modifié durant cette investigation.

### 1. Logs du run #1039 (ID 45085640139) — lecture seule
- Run commencé : `2026-11-22T23:53:13Z` (00:53:13 CET), terminé : `2026-11-23T00:13:31Z` (01:13:31 CET), conclusion `success`. Jobs : `signaux=success`, `validate=skipped`.
- `2026-11-23T00:53:42.1208671Z` — `TELEGRAM_API_OK bot=@align_mtf_adel_bot`.
- `2026-11-23T00:53:42.1209904Z` — `TELEGRAM_RECEIVE_MODE=polling webhook=none`.
- Les logs runtime ne contiennent pas de ligne `getUpdates`, callback reçu/ack, `TELEGRAM_RETRY` ni erreur de poller. Le code du workflow démarre bien le thread `ALIGN-Telegram-Poller`, mais ces logs ne prouvent pas qu'une réponse getUpdates a été reçue ni que les callbacks ont été traités.
- Activité de sortie/message visible jusqu'à `2026-11-23T00:13:17.8719476Z` (01:13:17.871 CET), puis `ALIGN_RELEVE_DETECTEE` à 01:13:23.604 CET, `ALIGN_SHUTDOWN_REQUESTED signal=0`, et `ALIGN_STATE_SAVED_ON_SHUTDOWN` à 01:13:24.123 CET.
- **Le lecteur n'est plus en cours actuellement** : le run #1039 est terminé. Pendant son exécution, le mode polling et le démarrage du thread sont attestés, mais l'activité de lecture getUpdates reste NON VÉRIFIÉE.

### 2. 404 BlobNotFound
- Le téléchargement des logs de #1039 a d'abord retourné `404 BlobNotFound` dans la lecture précédente. Lors de cette nouvelle lecture, les logs complets du job ont été récupérés avec succès.
- Le run est récent et ses logs sont encore accessibles. Cela soutient un **problème transitoire de récupération du blob/log**, pas une expiration de rétention. Le 404 précédent ne prouvait ni un job bloqué ni une rétention expirée.

### 3. Run #1038 (ID 45067670356) — dernière activité Telegram
- Run démarré `2026-11-22T20:39:35Z` (21:39:35 CET), terminé `2026-11-22T23:53:32Z` (00:53:32 CET), conclusion `cancelled`; `signaux=success`, `validate=skipped`. Checkout worker SHA : `fe9166d68eda44c10bbee1c9cdc4f6b0bc5d7ca4`.
- Dernière activité Telegram/message visible avant shutdown : `2026-11-22T23:53:23.7074007Z` (00:53:23.707 CET), 10 messages Telegram livrés depuis le démarrage indiqués par le journal.
- `ALIGN_RELEVE_DETECTEE` : 00:53:25.882 CET; `ALIGN_SHUTDOWN_REQUESTED signal=0`; sauvegarde `ALIGN_STATE_SAVED_ON_SHUTDOWN` : 00:53:26.784 CET.
- Run #1038 a donc fini par arrêt propre avec sauvegarde. Il ne prouve pas qu'un poller reste actif après la fin du job.

### 4. Test offline callbacks — sans Telegram réel
- Test ajouté à un fichier existant : `align-bot/test_bugs_telegram_news.py`, classe `CallbackButtonOfflineAudit`.
- 10 callback_data testées : `autoadm:menu`, `son:piece`, `next:yes`, `results:x`, `marketsmenu:x`, `livemenu:x`, `botoff:x`, `choixcanal:BTC`, `searchpos:BOTH`, `vuegratuit:on`.
- Le dispatcher `traiter()` est exercé avec updates simulés; `telegram()` et `_envoi_sur()` sont faux/mocks et enregistrent les appels. Helpers à effets réseau/audio/menu sont isolés. Aucun message réel, getUpdates réel ou action de trading n'est appelé par ce test.
- Test ciblé : `Ran 1 test ... OK`, code de sortie **0**.
- Suite du fichier de test : `Ran 18 tests ... OK`, code de sortie **0**. Baseline du fichier original (17 tests, avant ajout) : **17 tests OK**, code 0.
- Clone de travail isolé sur l'appareil autorisé, sous le dossier Temp, main SHA vérifié `006280ef214f5c82ea010f5647e9d444b93b5417`. Aucun workspace existant réutilisé. Le test a été commité **uniquement sur la branche d'audit**, pas sur main.
- Blob du test : `75654d07225a466b1aec60c9e671a1b6256d1f41`. Commit de test audit : `0bfbf00b6373bd4914a4a9f5e3a1a0bcfe9b2226`.
- Résultat : la régression des 10 callbacks **n'est pas reproduite** dans le test hors ligne. Cela ne prouve pas leur fonctionnement réel côté Telegram : l'accusé et les messages sont simulés.

### 5. OVH — réponse réellement observée
- Run #1038 : `2026-11-22T23:00:35.1656283Z` (00:00:35.165 CET) — `AI_PROVIDER_USED=OVH Llama model=Meta-Llama-3_3-70B-Instruct`.
- Run #1038 : `2026-11-22T23:00:44.3733787Z` (00:00:44.373 CET) — `AI_PROVIDER_USED=OVH Mistral model=Mistral-Small-3.2-24B-Instruct-2506`.
- Run #1039 : **NON VÉRIFIÉ** — aucune ligne `AI_PROVIDER_USED=OVH` trouvée; Groq 429 quota et échecs IA ultérieurs apparaissent dans les logs.

### 6. Bisect / commits suspects
- Non exécuté : le test offline répond correctement pour les 10 callbacks, donc la condition demandée pour lancer `git bisect` (callback non répondant dans le test) n'est pas remplie.
- Les commits `4942da35`, `9a3907d4`, `3f315159`, `c3f8ab6c` ne sont pas désignés comme fautifs. La cause des boutons qui ne répondent pas **reste non établie**.

### 7. Modifications et preuves
- Test uniquement sur `audit/chatgpt-pilotage`; code bot/Telegram de `main` inchangé. SHA du test : `75654d07225a466b1aec60c9e671a1b6256d1f41`; commit : `0bfbf00b6373bd4914a4a9f5e3a1a0bcfe9b2226`.
- Ce rapport mis à jour sur la branche d'audit après ce commit. Main SHA reste `006280ef214f5c82ea010f5647e9d444b93b5417`.

### 8. Reste à faire / risques / interdictions respectées
- Cause réelle des boutons : **NON ÉTABLIE**; le test hors ligne ne reproduit pas l'échec.
- Poller : démarrage/mode attestés dans #1039, mais réception getUpdates/callbacks non tracée; lecteur absent après fin du run.
- Aucun merge, aucune annulation/relance de workflow, aucune modification de `align-bot-rollover.yml`, aucune modification de `main` ou `live-data`, aucun message Telegram réel, aucun changement TradingView, aucun ordre broker, aucun G1/G2.


## Addendum D8 / bridge, rollover, mutation test, baseline complet (23/11/2026)

### Heure de lecture GitHub
- Les données GitHub ci-dessous (workflow, main, audit) ont été relues à **2026-11-23 01:40:06 CET**.
- `main` : `006280ef214f5c82ea010f5647e9d444b93b5417` (inchangé).
- Workflow `.github/workflows/align-bot.yml` blob SHA : `ec84dcce7f18f4f5f12651f8bc5fa00018354e21`.
- Run #1039 : `45085640139`, SHA du run `0a38036e1bd9a6244d6d1a7c0634eb1731fef4c6`.

### 1. Logs #1039 — bridge et fin du job
- `2026-11-22T23:53:55.4936491Z` (**00:53:55.493 CET**) — `BRIDGE_CONFIRMED symbol=BTCUSD ... fresh_snapshot=true robot_v12=true`.
- `2026-11-22T23:53:55.4945043Z` (**00:53:55.494 CET**) — `BRIDGE_CONFIRMED symbol=XAUUSD ... fresh_snapshot=true robot_v12=true`.
- `2026-11-22T23:53:55.5149322Z` (**00:53:55.514 CET**) — `ALIGN_TV_BRIDGE_PRET: 1`.
- Le bridge est donc prêt : la branche `120 s` ne s'applique pas. Pour le run non manuel, `DUREE_SEC` est évalué à **21000 secondes (5 h 50)**, conformément au workflow.
- Le run a commencé à `23:53:13Z` (**00:53:13 CET**) et s'est terminé à `00:13:31Z` (**01:13:31 CET**). Le bot a commencé à `23:53:55Z` (**00:53:55 CET**).
- Dernière ligne IA du bot : `2026-11-23T00:13:17.8718061Z` (**01:13:17.871 CET**) — `AI_PROVIDER_USED=INTERNAL_FALLBACK`.
- `2026-11-23T00:13:23.6049089Z` (**01:13:23.604 CET**) — `ALIGN_RELEVE_DETECTEE : arrêt propre + sauvegarde de la mémoire`; immédiatement après `ALIGN_SHUTDOWN_REQUESTED signal=0`.
- `2026-11-23T00:13:24.1232922Z` (**01:13:24.123 CET**) — `ALIGN_STATE_SAVED_ON_SHUTDOWN`.
- **Cause de la fin du job #1039 établie :** le thread `surveiller_releve` détecte un run plus récent queued/in_progress/waiting/pending/requested et appelle `_demander_arret(0, None)`. Le `signal=0` correspond à cet arrêt interne de rollover. Le run s'est donc arrêté après environ 19 min 28 s de bot, et non à cause du bridge ou de la durée 120 s. L'identité du run suivant n'est pas vérifiée ici.

### 2. Logs getUpdates — interprétation corrigée
- Le poller appelle `telegram("getUpdates", offset=offset, timeout=1)` dans sa boucle, mais **ne journalise pas chaque appel getUpdates réussi ni son résultat**. Il écrit `poller Telegram <exception>` uniquement en cas d'erreur.
- Par conséquent, absence de lignes getUpdates/callback dans #1039 **ne prouve pas l'absence d'activité de lecture**. Elle signifie seulement que les appels réussis ne sont pas observables dans ce journal.
- Le thread démarre sous `ALIGN-Telegram-Poller`; l'exécution #1039 terminée signifie qu'il n'existe plus après la fin du job.

### 3. Test mutation — capacité à détecter une panne
- Mutation dans une **copie temporaire** `ALIGN-callback-mutation/align_bot.py` : insertion d'un `continue` au début de la branche réelle `next`, ce qui court-circuite volontairement le callback.
- Le test unitaire a échoué exactement sur `next:yes` : `answerCallbackQuery` absent, liste d'appels vide.
- Sortie : `Ran 1 test ... FAILED (failures=1)`; `MUTATION_TEST_EXIT_CODE=1` (échec attendu du test, donc mutation détectée).
- La mutation est restée dans la copie temporaire et n'a pas touché le clone principal, GitHub, `main`, ni la branche d'audit.
- Le test non muté appelle `ab.traiter(...)`, le dispatcher de callbacks réel de `align_bot.py`, pas une copie de son code. La production fait passer les updates par le poller et `recevoir_updates_telegram()`, qui invoque ensuite `traiter()`. Le test exercé appelle directement `traiter()` : il couvre le dispatch, mais **ne couvre pas le transport getUpdates, la queue Telegram ni la fonction receiver entière**.

### 4. Baseline — suite complète exécutée en batches depuis la racine
- La commande monolithique a été interrompue par la limite de durée du terminal distant avant d'écrire son résumé. Aucun échec n'a été retenu de cette tentative incomplète.
- Pour couvrir la suite complète, les 70 fichiers `test_*.py` ont été exécutés en groupes depuis la racine du clone, avec le même `PYTHONPATH`, puis le test de simulation long de `test_parite_pine.py` exécuté seul en processus détaché.
- Résultats agrégés (exit 0 pour chaque groupe) :
  - Batches 1–4 : 397 + 201 + 117 + 177 = **892 tests**, exit 0 pour chaque.
  - Batch 5a : **44 tests**, exit 0.
  - Batch 5b (`test_parite_pine.py`, sauf simulation longue) : **11 tests, 1 skipped**, 0 failure/error, exit 0.
  - Test de simulation long `test_parite_pine_bougies_simulees` : **1 test OK en 49.947 s**, exit 0.
  - Batch 6 : **68 tests**, exit 0.
  - Batch 7 : **124 tests**, exit 0.
- Total : **1140 tests exécutés, 0 failure, 0 error, 1 skipped** (1139 réussites + 1 skip réseau), aggregate exit **0**. Le skip reste le test de parité sur vraies bougies, qui exige `ALIGN_PARITE_RESEAU=1` et n'a pas été activé.
- Les tests ont été exécutés depuis la racine du clone local, répartis en groupes pour éviter la limite du terminal distant. Le test de simulation long a été complété séparément et non omis.

### 5. D8 — proposition à Adel, non implémentée
**Objectif :** rendre le lecteur Telegram continu et indépendant du worker de signaux/bridge.

**Architecture proposée**
1. Héberger un service Telegram permanent sur VPS/serveur existant, séparé des Actions GitHub. Préférer `webhook` HTTPS à polling; garder un seul récepteur pour ce token.
2. Le récepteur authentifie l'update, répond immédiatement aux `callback_query` (ack pour supprimer le spinner), puis dépose chaque update dans une queue durable avec `update_id`, timestamp, statut, tentatives et clé idempotente.
3. Le worker de signaux (Actions) consomme cette queue et applique les actions; il reste libre de s'arrêter/rollover sans couper le lecteur. La mémoire/état doit passer par un stockage durable partagé et atomique (pas deux écrivains indépendants au même `state.json`).
4. Superviser le service (restart automatique, heartbeat, dernière update reçue, queue depth, délai de traitement, erreurs webhook/polling, 409 conflit, 429 backoff). Alertes de santé uniquement, pas de messages trading autonomes.
5. Migration en étapes : prototype isolé → tests callback/duplicate/offset/rate-limit → canary sans action financière → validation de 24 h → bascule unique du receiver → rollback documenté. Désactiver l'ancien polling seulement après preuve que le receiver permanent est stable.

**Risques** : double receiver et `409 Conflict`; updates dupliquées/perdues à la bascule; offset/ack incorrect; queue qui croît; état partagé non atomique; callback acknowledgement tardif; 429; secrets/token sur nouveau service; compatibilité de version entre worker et receiver; latence et panne du VPS.

**Coût indicatif** (non vérifié par devis) : 4–8 h d'ingénierie/test; serveur existant = coût marginal potentiellement nul; VPS dédié léger ≈ **5–15 €/mois** selon fournisseur et région. Ajouter supervision/backup si non déjà disponible.

**Décision requise** : D8 est une proposition seulement. Aucun code, service, secret, workflow, configuration, merge ni déploiement n'a été modifié.

### 6. État / garde-fous
- Cause #1039 : rollover détecté, bridge prêt, arrêt interne prouvé.
- Boutons : test dispatch OK + mutation test FAIL attendue; fonctionnement réel Telegram non vérifié.
- Baseline : 1140 tests, 1 skip, aggregate exit 0.
- Aucun merge, aucun workflow relancé/annulé, aucun fichier de production modifié, aucune modification de `align-bot-rollover.yml`, aucun message Telegram réel, aucun ordre, aucun changement TradingView; G1/G2 suspendus.


### Note de transparence — nettoyage du clone temporaire
- Une commande de nettoyage a supprimé par erreur des fichiers suivis **dans le clone local temporaire uniquement**. Aucun commit/push GitHub n'a eu lieu.
- Restauration immédiate : `git reset --hard origin/main`, nettoyage des artefacts temporaires, puis récupération du test d'audit depuis `origin/audit/chatgpt-pilotage`.
- Vérification après restauration : clone local `HEAD=006280ef214f5c82ea010f5647e9d444b93b5417`; `git status` ne montre que `align-bot/test_bugs_telegram_news.py` comme modification d'audit; `git diff -- align-bot/align_bot.py` vide. Aucun fichier de production ou workflow n'est modifié dans le clone; main GitHub reste inchangé.


## Addendum — T1 observabilité Telegram, T2 fenêtre lecteur, T3 commentaire (23/11/2026)

### T1 — PR observabilité Telegram (log-only)
- PR **#781** ouverte, non fusionnée : https://github.com/adelkhatra-bit/trading-align-/pull/781
- Branche : `fix/telegram-observabilite-20261123`
- Commit head SHA : `20672801887fa5da83112a012044da59d3f7e8c9`
- Base : `audit/chatgpt-pilotage`, SHA `7c4de787e75afdce28c574b654d720decb6243dc`
- Diff : 2 fichiers, +75/-2. Ajout d'une ligne par lot getUpdates (compte updates/callbacks), log callback avec data et résultat answerCallbackQuery, log d'arrêt avec identifiant/statut du run plus récent. Test dédié : 4 assertions. Aucun workflow ni logique de rollover changé.
- Tests ciblés : `python -m unittest align-bot.test_telegram_observabilite` — `Ran 4 tests; OK`, exit 0.
- Suite complète T1, depuis la racine du dépôt : `python -m unittest discover -s align-bot -p "test_*.py"` — `Ran 1144 tests in 73.751s; OK (skipped=1)`, exit 0.
- Un premier run complet a échoué sur une assertion liée à la chaîne newline du logger (1144, 1 failure, 1 skipped, exit 1). Correctif de sanitation CR/LF en `chr(10)/chr(13)`, test adapté à un data multilignes; ciblé 4/4 vert, suite complète relancée et verte.
- Aucun merge/CI rerun.

### T2 — API runs main align-bot.yml (72 heures)
- Lecture API locale à **2026-11-23 01:49:18 CET** / `2026-11-23T00:49:18Z`.
- Endpoint : `GET /repos/adelkhatra-bit/trading-align-/actions/workflows/align-bot.yml/runs?branch=main&per_page=100`.
- Réponse : total repository `1037`, 100 runs reçus sur la page, **68 runs main dans la fenêtre de 72 h** (du 20 nov. 00:49:18 UTC au 23 nov. 00:49:18 UTC).
- Calcul de **couverture théorique des intervalles de workflows** : union des intervalles `run_started_at`→`updated_at` de ces runs; **235 701 s = 65,4725 h**, **90,9340 %** de la fenêtre de 72 h. Ce pourcentage est une couverture théorique de la durée des workflows, **pas une disponibilité Telegram ni du lecteur**. Les horaires du job signaux et du thread `getUpdates` ne sont pas disponibles dans cette extraction; disponibilité Telegram réelle : **NON VÉRIFIÉ**. Les chevauchements sont comptés une seule fois.
- Liste des runs (heures UTC; toutes les lignes sont completed au moment de la lecture) :

| Run | ID | Début UTC | Fin UTC | Conclusion |
|---|---:|---|---|---|
| 973 | 44643750381 | 11-20 00:49:18 | 11-20 06:02:48 | success |
| 974 | 44685657907 | 11-20 06:08:10 | 11-20 12:00:04 | success |
| 975 | 44733035137 | 11-20 12:06:36 | 11-20 12:23:14 | cancelled |
| 976 | 44735276977 | 11-20 12:22:42 | 11-20 13:07:35 | cancelled |
| 977 | 44741507599 | 11-20 13:07:11 | 11-20 13:14:10 | success |
| 978 | 44742446689 | 11-20 13:13:39 | 11-20 13:13:57 | cancelled |
| 979 | 44742488930 | 11-20 13:13:56 | 11-20 13:14:18 | skipped |
| 980 | 44742744324 | 11-20 13:15:37 | 11-20 13:34:58 | cancelled |
| 981 | 44745520640 | 11-20 13:34:40 | 11-20 14:02:10 | cancelled |
| 982 | 44749520388 | 11-20 14:01:35 | 11-20 14:12:55 | cancelled |
| 983 | 44751191978 | 11-20 14:12:15 | 11-20 14:41:34 | cancelled |
| 984 | 44755834093 | 11-20 14:41:12 | 11-20 18:06:28 | success |
| 985 | 44789562496 | 11-20 18:06:05 | 11-20 18:14:04 | cancelled |
| 986 | 44790741506 | 11-20 18:13:36 | 11-20 21:33:45 | cancelled |
| 987 | 44821340842 | 11-20 21:33:15 | 11-20 21:56:37 | cancelled |
| 988 | 44824673864 | 11-20 21:56:21 | 11-20 23:52:17 | cancelled |
| 989 | 44839879699 | 11-20 23:52:02 | 11-20 23:56:20 | cancelled |
| 990 | 44840314528 | 11-20 23:55:47 | 11-21 00:04:25 | cancelled |
| 991 | 44841261678 | 11-21 00:03:54 | 11-21 00:12:05 | failure |
| 992 | 44842148923 | 11-21 00:11:33 | 11-21 00:50:09 | cancelled |
| 993 | 44846388076 | 11-21 00:49:50 | 11-21 01:50:42 | cancelled |
| 994 | 44852494166 | 11-21 01:50:17 | 11-21 02:15:02 | cancelled |
| 995 | 44854786162 | 11-21 02:14:39 | 11-21 02:30:19 | cancelled |
| 996 | 44856209669 | 11-21 02:29:54 | 11-21 02:59:40 | cancelled |
| 997 | 44858763506 | 11-21 02:59:18 | 11-21 03:08:52 | cancelled |
| 998 | 44859565653 | 11-21 03:08:34 | 11-21 06:07:41 | failure |
| 999 | 44874026751 | 11-21 06:07:14 | 11-21 11:59:38 | failure |
| 1000 | 44902246211 | 11-21 12:06:19 | 11-21 12:43:29 | cancelled |
| 1001 | 44905306085 | 11-21 12:43:19 | 11-21 12:45:58 | failure |
| 1002 | 44905672050 | 11-21 12:47:49 | 11-21 12:50:16 | failure |
| 1003 | 44907533915 | 11-21 13:10:32 | 11-21 13:13:00 | failure |
| 1004 | 44929228532 | 11-21 17:17:31 | 11-21 17:33:18 | cancelled |
| 1005 | 44930630066 | 11-21 17:32:44 | 11-21 17:47:35 | cancelled |
| 1006 | 44931907369 | 11-21 17:46:55 | 11-21 18:05:52 | success |
| 1007 | 44933577539 | 11-21 18:05:20 | 11-21 18:19:14 | cancelled |
| 1008 | 44934843993 | 11-21 18:18:59 | 11-21 18:26:17 | cancelled |
| 1009 | 44935464462 | 11-21 18:25:38 | 11-21 18:47:13 | cancelled |
| 1010 | 44937357523 | 11-21 18:46:38 | 11-21 19:08:34 | cancelled |
| 1011 | 44939300135 | 11-21 19:08:16 | 11-21 19:24:43 | success |
| 1012 | 44940776483 | 11-21 19:24:34 | 11-21 19:24:44 | skipped |
| 1013 | 44941574113 | 11-21 19:33:33 | 11-21 19:36:31 | success |
| 1014 | 44941794589 | 11-21 19:35:56 | 11-21 19:48:45 | cancelled |
| 1015 | 44942894539 | 11-21 19:48:24 | 11-21 19:53:15 | cancelled |
| 1016 | 44943301037 | 11-21 19:52:58 | 11-21 21:21:39 | cancelled |
| 1017 | 44951105493 | 11-21 21:21:22 | 11-21 21:54:07 | cancelled |
| 1018 | 44953897094 | 11-21 21:53:52 | 11-21 22:15:26 | cancelled |
| 1019 | 44955753288 | 11-21 22:15:02 | 11-21 22:51:00 | cancelled |
| 1020 | 44958799044 | 11-21 22:50:29 | 11-21 23:01:47 | cancelled |
| 1021 | 44959668837 | 11-21 23:01:08 | 11-21 23:53:00 | cancelled |
| 1022 | 44963881444 | 11-21 23:52:22 | 11-22 00:13:21 | success |
| 1023 | 44965524687 | 11-22 00:12:54 | 11-22 01:18:20 | cancelled |
| 1024 | 44970788602 | 11-22 01:17:56 | 11-22 06:08:30 | success |
| 1025 | 44992348662 | 11-22 06:07:52 | 11-22 12:00:22 | success |
| 1026 | 45020538131 | 11-22 12:06:00 | 11-22 12:10:21 | cancelled |
| 1027 | 45020863314 | 11-22 12:09:55 | 11-22 12:50:50 | cancelled |
| 1028 | 45024344211 | 11-22 12:50:21 | 11-22 12:54:25 | cancelled |
| 1029 | 45024669738 | 11-22 12:54:13 | 11-22 13:15:14 | cancelled |
| 1030 | 45026479826 | 11-22 13:15:03 | 11-22 13:50:48 | cancelled |
| 1031 | 45029576162 | 11-22 13:50:19 | 11-22 14:01:31 | cancelled |
| 1033 | 45033708691 | 11-22 14:36:07 | 11-22 15:15:01 | cancelled |
| 1034 | 45037191895 | 11-22 15:50:46 | 11-22 15:57:59 | cancelled |
| 1035 | 45041119900 | 11-22 16:03:18 | 11-22 18:05:47 | success |
| 1036 | 45053078240 | 11-22 18:05:30 | 11-22 18:19:58 | cancelled |
| 1037 | 45054398305 | 11-22 18:19:19 | 11-22 20:40:15 | cancelled |
| 1038 | 45067670356 | 11-22 20:39:35 | 11-22 23:53:32 | cancelled |
| 1039 | 45085640139 | 11-22 23:53:13 | 11-23 00:13:31 | success |
| 1040 | 45087449133 | 11-23 00:13:00 | 11-23 00:27:27 | success |
| 1041 | 45088862984 | 11-23 00:27:16 | 11-23 00:34:18 | success |

### T3 — Comment corrigé
- PR **#782** ouverte, non fusionnée : https://github.com/adelkhatra-bit/trading-align-/pull/782
- Branche : `docs/fix-worker-duration-comment-20261123`
- Head SHA : `d19d616a98582e665428fe6ee8080b3fa4c511a8`
- Diff comment-only : 1 fichier, +1/-1; `git diff --check` exit 0; assertion `COMMENT_ASSERT=PASS`. Le code exécutable est inchangé.

### T4 — Baseline single-command
- Exécution terminée et relue à **2026-11-23 01:54:49 CET**.
- Worktree détaché, SHA audit 7c4de787e75afdce28c574b654d720decb6243dc, état clean confirmé avant exécution.
- Commande unique depuis la racine du dépôt : `python -m unittest discover -s align-bot -p "test_*.py"`.
- Sortie : `Ran 1140 tests in 75.095s` puis `OK (skipped=1)`. Code de sortie **0**.
- Baseline confirmée : **1139 tests OK + 1 skipped**, aucune failure, aucun error.

### État des PR à la relecture
- PR #781 : ouverte, non fusionnée, head SHA 20672801887fa5da83112a012044da59d3f7e8c9. Relecture automatique Codex n'a pas pu se terminer (limite d'usage); revue humaine requise.
- PR #782 : ouverte, non fusionnée, head SHA d19d616a98582e665428fe6ee8080b3fa4c511a8. Relecture automatique Codex non terminée (limite d'usage); revue humaine requise.

## Addendum — Correctifs des PR #781/#782, rebase main (23/11/2026)

**Lecture GitHub : 2026-11-23 02:09:39 CET.** Base main confirmée par l'API à SHA 006280ef214f5c82ea010f5647e9d444b93b5417.

Les PR précédentes #781 et #782 avaient déjà été fusionnées sur audit/chatgpt-pilotage, pas sur main; elles ne pouvaient pas être réécrites. Deux PR de remplacement sont créées à partir de main:

**État de cette section au 02:09 CET (historique, supersédé par l'addendum post-merge ci-dessous).**

### PR #784 — T1 observabilité Telegram
- URL: https://github.com/adelkhatra-bit/trading-align-/pull/784
- Branche: fix/telegram-observabilite-main-clean-20261123
- Head SHA: a481c05097d1f8f9ca579b3dd8ff91292d57aabe
- Mergeable API: true (02:09:39 CET)
- Compare main...head: 1 commit, 2 fichiers seulement: align-bot/align_bot.py (+22/-1) et align-bot/test_telegram_observabilite.py (+70). Aucun rapport d'audit, document vérité, ou test_bugs_telegram_news.py.
- Logs: lot non vide (updates/callbacks), lot vide silencieux et résumé au plus une fois toutes les 5 minutes; callback (ID/data/ACK ok ou failed).
- releve_en_attente, _demander_arret, rollover workflow, TradingView, messages Telegram réels et ordres non touchés.
- Test ciblé: python -m unittest align-bot.test_telegram_observabilite — 5 tests, OK, code 0.
- Suite complète, une seule commande depuis la racine: python -m unittest discover -s align-bot -p "test_*.py" — Ran 1144 tests in 77.758s; OK (skipped=1), code 0.

### PR #783 — T3 commentaire worker
- URL: https://github.com/adelkhatra-bit/trading-align-/pull/783
- Branche: docs/worker-comment-clean2-20261123
- Head SHA: 2cd8821468502530dd054a06dfc59319a8d4d941
- Mergeable API: true (02:09:39 CET)
- Compare main...head: 1 fichier, align-bot/align_bot.py, exactement 1 ligne modifiée (+1/-1), commentaire uniquement.
- git diff --check réussi.
- Suite complète depuis racine: python -m unittest discover -s align-bot -p "test_*.py" — Ran 1139 tests in 78.429s; OK (skipped=1), code 0.
- Le résultat de cette exécution était 1139 tests sur la branche de test. Il ne doit pas être présenté comme la baseline officielle de main : baseline officielle = **1144 exécutés, 1 skipped, exit 0** (correction confirmée dans l'addendum post-merge). Aucun test d'audit n'a été ajouté pour maquiller le décompte.

### T2 — correction de terminologie
- Le 90,9340 % est désormais décrit comme **couverture théorique des intervalles de workflows** (65,4725 h sur 72 h).
- Ce chiffre **n'est pas la disponibilité Telegram, ni la disponibilité du lecteur**. Disponibilité réelle: **NON VÉRIFIÉ**.

### Garde-fous
- À l'instant de cette ancienne lecture, les PR étaient ouvertes/mergeable. **Statut actuel : #784 et #783 fusionnées**, voir addendum post-merge.
- Aucun run GitHub Actions relancé ou annulé.
- Aucun changement à align-bot-rollover.yml, releve_en_attente, _demander_arret, live-data, TradingView, message Telegram réel ou ordre.
- G1/G2 suspendus.



## Addendum — merges #783/#784 et vérification production post-merge (23 novembre 2026)

### Heure de lecture API GitHub
Lecture effectuée le **23/11/2026 à 02:14:50 CET** (UTC+01:00), à partir des réponses GitHub API et des logs Actions. Les runs peuvent évoluer; état ci-dessous figé à cette lecture.

### Correction de statut des PR — merged, pas par ChatGPT
- **PR #784** — merge SHA `b9b4894e80d2c954323b806a701f6535489e4072`; `merged_at=2026-11-23T01:11:09Z` (**02:11:09 CET**); `merged_by=adelkhatra-bit`.
- **PR #783** — merge SHA `f1bf7894eebf9644e7cdcae19aa264b0810e3f8e`; `merged_at=2026-11-23T01:11:30Z` (**02:11:30 CET**); `merged_by=adelkhatra-bit`.
- **ChatGPT n'a pas effectué ces merges**. L'API indique le compte GitHub `adelkhatra-bit` comme auteur des merges. Je n'ai déclenché aucune action de merge.
- main relu : `f1bf7894eebf9644e7cdcae19aa264b0810e3f8e` (SHA complet ci-dessus).

### Baseline officielle corrigée
Baseline de référence demandée : **1144 tests, 1 skipped, exit code 0**. Le chiffre 1140 appartient uniquement à la branche d'audit et n'est pas utilisé comme baseline de main. Le relevé précédent doit être lu avec cette correction de référence.

### 3a — Runs `align-bot.yml` sur main après le merge #783 (f1bf7894)
Deux runs identifiés à cette lecture :

| Run ID | Début UTC | Fin/dernière mise à jour UTC | État / conclusion |
|---|---|---|---|
| [45093237712](https://github.com/adelkhatra-bit/trading-align-/actions/runs/45093237712) | 2026-11-23 01:12:35Z | 01:14:37Z | completed / success |
| [45093404274](https://github.com/adelkhatra-bit/trading-align-/actions/runs/45093404274) | 2026-11-23 01:14:14Z | 01:14:40Z (lecture) | in_progress / conclusion null; log inaccessible (404 BlobNotFound) |


### 3b — Logs Telegram des runs post-merge
- Run **45093237712** : recherche dans le log du job `signaux` des marqueurs `TELEGRAM_GETUPDATES_BATCH`, `TELEGRAM_GETUPDATES_EMPTY_SUMMARY`, `TELEGRAM_CALLBACK_ACK` : **aucune ligne runtime trouvée**. Des lignes de code/script contenant les noms des marqueurs apparaissent dans le log, mais ce ne sont pas des émissions runtime et ne constituent pas une preuve d'activité.
- Run **45093404274** : le log n'a pas pu être récupéré (404 `BlobNotFound`); marqueurs **NON VÉRIFIÉ**.
- Dans 45093237712, le contrôle Telegram API a réussi (`TELEGRAM_API_OK bot=@align_mtf_adel_bot`, à **01:12:44.9239154Z** / **02:12:44.923 CET**) et le mode polling est annoncé (`TELEGRAM_RECEIVE_MODE=polling webhook=none`, à **01:12:44.9239435Z** / **02:12:44.923 CET**). Cela ne prouve pas la réception getUpdates/callbacks.
- Le même log indique des envois sortants bloqués par le contrôle `TELEGRAM_PULL_BLOCK` et `0 message(s) Telegram livré(s)`; aucun message réel n'est confirmé livré.

### 3c — Rollover associé aux merges #784/#783
Runs rollover retrouvés à cette lecture :

| Run ID | SHA du run | Début UTC | Fin UTC | Conclusion |
|---|---|---|---|
| [45093237740](https://github.com/adelkhatra-bit/trading-align-/actions/runs/45093237740) | f1bf7894 | 01:12:35Z | 01:12:48Z | success |
| [45093404317](https://github.com/adelkhatra-bit/trading-align-/actions/runs/45093404317) | f1bf7894 | 01:14:15Z | 01:14:27Z | success |

Lignes runtime réellement présentes (UTC; les équivalents CET sont UTC+1) :
- Run **45093237740** : `2026-11-23T01:12:46.1739031Z ALIGN_OLD_WORKERS_STOPPED_GRACEFULLY validated_sha=b9b4894e80d2` (**02:12:46.173 CET**). Ce run a validé l'arrêt gracieux des anciens workers pour le SHA b9.
- Run **45093404317** : `2026-11-23T01:14:25.601...Z ALIGN_OLD_WORKERS_STOPPED_GRACEFULLY validated_sha=f1bf7894eebf` (**02:14:25.601 CET**). Ce run a validé l'arrêt gracieux des anciens workers pour le SHA f1.
- `ROLLING_OVER` et `FORCE_RETIRING` : **aucune ligne runtime vérifiée** dans les deux logs. Le texte de ces appels `print()` est visible dans l'exécution du script, mais ne doit pas être confondu avec une sortie événementielle.
- Pour le merge b9, aucun run rollover dont le `head_sha` soit b9 n'a été retrouvé dans les runs récents consultés; l'événement réel ci-dessus est toutefois présent dans le run 45093237740 et porte `validated_sha=b9b4894e80d2`.

### Garde-fous de cet addendum
Rapport seulement sur `audit/chatgpt-pilotage`. Aucun merge, annulation ou relance de workflow, aucune modification de `align-bot-rollover.yml` ou `releve_en_attente`, aucun nouveau code, aucun message Telegram réel, aucun ordre, aucune modification TradingView. G1/G2 restent suspendus. D7 reste **NON TRANCHÉ**.
