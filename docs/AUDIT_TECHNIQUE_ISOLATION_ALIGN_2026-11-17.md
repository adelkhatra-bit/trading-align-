# Audit technique approfondi — ALIGN et isolation locale
Date de contrôle : 2026-11-17
Dépôt : adelkhatra-bit/trading-align-
Branche de production examinée : main
SHA main examiné : ba8ba5031c5725b8e07079e44599195aa3a6725a
Branche de publication : live-data
SHA live-data observé : 4bebb37dfe7fc77af0bd0345755a5a9cbf24308e

## Résumé exécutif

Le problème immédiat de production ALIGN est identifié : le workflow « ALIGN MTF BOT » s'arrête au préflight du bridge, car les secrets ALIGN_TV_API_URL et ALIGN_TV_READ_TOKEN sont absents dans le runner GitHub. Le run 44162309509 (#896), job « signaux » ID 134319090137, le confirme. Telegram répond et le bot reconnu est @align_mtf_adel_bot; le mode de réception observé est polling, webhook absent. Le contrôle IA montre Groq connecté (openai/gpt-oss-120b), tandis que Gemini retourne HTTP 503 et le second modèle Gemini expire en timeout. La chaîne active essaie cependant Gemini avant Groq.

Un second problème d'isolation est prouvé sur le poste Windows : les ports 3000 et 4000 sont occupés par des processus Node rattachés à l'ancien chemin OneDrive/Desktop/trading-auto, pas au clone canonique ALIGN. Le processus Node du port 4000 exécute explicitement C:\Users\97156\OneDrive\Desktop\trading-auto\server.js. Le processus parent du serveur PM2 associé au port 3000 est C:\Users\97156\OneDrive\Desktop\trading-auto\server-manager.js restart. Aucun processus cloudflared/ngrok n'a été observé pendant ce contrôle.

Le dossier .cloudflared local contient un tunnel Cloudflare préexistant configuré pour dossierfacilefrance.com et www.dossierfacilefrance.com vers localhost:3000; ce tunnel n'est pas une preuve de bridge ALIGN et ne doit pas être réutilisé. Le fichier scripts/cloudflare-oneclick.ps1 décrit un tunnel nommé trading-bridge et exige CF_TUNNEL_HOSTNAME pour une URL publique stable, mais cette variable n'est pas présente dans les environnements Windows User/Machine contrôlés.

Le dépôt canonique ALIGN contient encore de nombreux résidus de l'ancien projet trading-auto : scripts de démarrage, documentation, chemins absolus, stockage local et fichiers serveur. Ces éléments créent un risque réel de mauvais démarrage et de confusion. Leur présence dans Git ne prouve pas qu'ils sont tous utilisés par ALIGN; les supprimer sans graphe de dépendances serait dangereux.

## 1. Références et preuves

### GitHub Actions
- Run ALIGN MTF BOT #896 : 44162309509, SHA main ba8ba5031c5725b8e07079e44599195aa3a6725a, échec.
- Job signaux : 134319090137, échec au contrôle bridge.
- Le log indique les deux variables ALIGN_TV_API_URL et ALIGN_TV_READ_TOKEN vides.
- Le job de validation du même workflow est « skipped » après l'échec du job signaux.
- Run ALIGN MTF validation sur main : 44162097864, succès.
- Pages build/deployment : 44162096219, succès.
- Un workflow vert ne valide donc pas à lui seul le fonctionnement du worker live.

### Telegram
- TELEGRAM_API_OK bot=@align_mtf_adel_bot.
- TELEGRAM_RECEIVE_MODE=polling webhook=none.
- Le préflight ne démontre pas qu'un signal de trading a effectivement été envoyé; le worker est arrêté avant l'analyse des marchés.
- align_bot.py contient une file telegram_outbox, un cooldown 429 et des fonctions de retry; ces mécanismes nécessitent des tests de livraison réelle et de reprise d'état.
- L'état Telegram contient un offset persisté selon l'audit du worker. Il faut vérifier la cohérence entre offset, polling et état restauré.

### IA
- Le worker a essayé Gemini gemini-3.6-flash (HTTP 503), Gemini gemini-3.8-flash (timeout), puis Groq openai/gpt-oss-120b (connecté).
- Le code main place Gemini avant Groq dans IA_FOURNISSEURS.
- Les secrets Gemini et Groq sont injectés par le workflow actuel. La demande de l'équipe est de désactiver Gemini dans la chaîne active et de donner la priorité à Groq gratuit, avec secours gratuits testés.
- PR #423 traite la réutilisation du fournisseur confirmé par le préflight, mais ne règle pas à elle seule l'ordre des fournisseurs ni le choix explicite Groq-first. Elle est ouverte et doit être rebasée/revérifiée contre le main courant.

### Poste Windows autorisé — lecture seule
- Clone canonique : C:\Users\97156\ALIGN_CANONICAL\trading-align-.
- Remote Git : origin vers adelkhatra-bit/trading-align-.
- HEAD local : ba8ba5031c5725b8e07079e44599195aa3a6725a; branche locale observée : fix/align-groq-primary-disable-gemini-20261117; aucun changement local non commité dans le contrôle.
- Port 4000 : PID 63664, node.exe, commande exécutée depuis C:\Users\97156\OneDrive\Desktop\trading-auto\server.js.
- Parent du processus port 4000 : PID 64016, node.exe, C:\Users\97156\OneDrive\Desktop\trading-auto\server-manager.js restart.
- Port 3000 : PID 22656 node.exe, processus enfant géré par le daemon PM2 PID 15296. Son contexte parent remonte également au serveur manager de trading-auto.
- Aucun processus cloudflared/ngrok observé au moment du contrôle.
- Aucun service Windows portant un nom ALIGN, trading ou cloudflared n'a été listé.
- Variables ALIGN_TV_API_URL, ALIGN_TV_READ_TOKEN et CF_TUNNEL_HOSTNAME absentes des environnements User/Machine contrôlés. Les clés ne sont jamais affichées.
- Le répertoire .cloudflared contient un tunnel existant configuré pour dossierfacilefrance.com et www.dossierfacilefrance.com vers localhost:3000. Ressource étrangère au périmètre ALIGN : ne pas modifier ni réutiliser.
- Les variables de secrets et l'état d'un processus ne sont pas entièrement déductibles d'un simple inventaire environnemental; les contrôles présents ne prouvent pas l'absence de toute autre configuration externe.

## 2. Résidus de l'ancien projet dans le dépôt ALIGN

Les recherches Git sur main ont trouvé notamment :
- START.bat : lance node server.js sur port 4000 avec BROKER_MODE=live et SAFE_MODE=0.
- START_COMPLETE.bat : lance également node server.js avec BROKER_MODE=live et SAFE_MODE=0.
- QUICK_START.bat : même lancement live sur port 4000.
- START_CLEAN.bat : ancien démarrage « Trading Auto » sur port 4000.
- .env.example : SAFE_MODE=0 et BROKER_MODE=live par défaut.
- public/dev-helper.js : chemin absolu OneDrive/Desktop/trading-auto et localhost:4000.
- tradingview-analyzer/PRE_LAUNCH_CHECKLIST.md : chemin absolu vers trading-auto.
- src/agents/stateManager.js : clés localStorage trading-auto-state et trading-auto-history.
- src/services/fileService.js : répertoire temporaire trading-auto-files.
- ARCHITECTURE.md, README.md, AUDIT_GUIDE.md, AUDIT_SYNC.md, EXECUTION_PLAN_COMPLETE.md, FILES_ORGANIZATION.md, INTEGRATION_LINE_NUMBERS.md, PROJECT_ANALYSIS_REPORT.json et plusieurs autres documents décrivent encore trading-auto.
- server-manager.js référence server.js à la racine du dépôt.

La présence de ces fichiers n'autorise pas leur suppression automatique. Chaque fichier doit être classé : utilisé par ALIGN, historique non référencé, outil de développement isolé, ou résidu dangereux. Les points d'entrée de démarrage doivent être corrigés avant toute purge.

## 3. Sécurité d'exécution broker

Le dépôt conserve des scripts qui démarrent le serveur racine avec BROKER_MODE=live et SAFE_MODE=0. L'exemple .env est lui aussi configuré en mode live et sécurité désactivée. Le workflow du bot définit actuellement AUTO_TRADE=0 et TOPSTEP_REEL=0, ce qui est une protection du worker GitHub, mais ne neutralise pas automatiquement le serveur Node local ou tous les autres chemins de lancement.

Aucun ordre broker n'a été envoyé pendant cet audit. Avant de relancer ou migrer les serveurs, imposer un défaut fail-closed : SAFE_MODE=1, BROKER_MODE=paper, AUTO_TRADE=0, TOPSTEP_REEL=0. Les chemins live doivent être supprimés du démarrage standard et ne jamais être activés par défaut. Ajouter des tests qui prouvent que toute tentative d'ordre est refusée en mode sûr.

## 4. Causes racines et niveau de confiance

1. Bridge absent dans le worker GitHub — confirmé, bloquant.
2. Aucun tunnel ALIGN actif observé sur le poste et hostname Cloudflare manquant — confirmé localement; cause plausible de l'absence de bridge public, à vérifier contre l'ancien déploiement.
3. Serveurs locaux 3000/4000 exécutent l'ancien chemin trading-auto — confirmé.
4. Scripts de démarrage ALIGN hérités qui activent explicitement le mode broker live — confirmé dans les fichiers; l'état effectif de toutes les sessions ne peut être déduit sans lecture des environnements propres à chaque processus.
5. Chaîne IA tente Gemini avant Groq malgré l'échec Gemini et le succès Groq — confirmé.
6. Les captures TradingView montrent des niveaux qui semblent dépassés par le prix — indice visuel seulement; il faut rejouer les snapshots historiques et inspecter les transitions d'état avant d'affirmer un défaut de calcul.
7. Les échecs keep-alive #7590/#7591 montrés sur les captures appartiennent au dépôt inside-dombe et à son workflow ping. Aucun lien technique vers le dépôt ALIGN n'est établi par les captures. Ne pas corriger ce workflow dans le cadre du chantier ALIGN.

## 5. Plan précis de réparation — ordre obligatoire

### Phase A — sécurisation et inventaire final
- Sauvegarder les configurations et fichiers ALIGN utiles, sans copier les secrets en clair.
- Faire l'inventaire des processus, ports, tâches planifiées, PM2, DNS, tunnels et comptes de service.
- Identifier chaque processus par chemin d'exécutable, répertoire de travail, PID parent et fichier de configuration.
- Ne pas arrêter/supprimer les processus trading-auto avant d'avoir prouvé qu'ils ne servent pas à une autre application et obtenu une fenêtre de bascule contrôlée.
- Mettre les points d'entrée ALIGN en mode sûr par défaut et ajouter des tests de non-exécution broker.

### Phase B — serveur et bridge ALIGN indépendants
- Définir un répertoire de déploiement dédié ALIGN, un service identifié ALIGN, un port dédié non partagé, un compte de service et un répertoire de logs/données propres.
- Créer ou retrouver le tunnel Cloudflare dédié ALIGN avec hostname stable appartenant à l'équipe; ne pas réutiliser le tunnel dossierfacilefrance.com.
- Configurer l'endpoint /bridge/robot-v12/mtf, TLS, token Bearer, rotation et health check.
- Alimenter ALIGN_TV_API_URL et ALIGN_TV_READ_TOKEN dans les secrets GitHub du seul dépôt ALIGN, sans jamais les afficher dans les logs.
- Vérifier la fraîcheur, l'horodatage, le symbole et la cohérence des snapshots BTCUSD, XAUUSD, NAS100 et des unités de temps M5/M15/H1/H4/D1/W1.
- Comparer la réponse du bridge au graphique TradingView et au flux de l'indicateur.

### Phase C — IA
- Définir Groq comme fournisseur principal par défaut, Gemini désactivé dans le worker.
- Conserver uniquement des secours gratuits explicitement testés et documentés; aucun fallback silencieux vers une IA indisponible.
- Vérifier que le fournisseur validé au préflight est exactement celui utilisé dans l'analyse du même run.
- Mesurer latence, erreurs, quotas, cooldowns et résultat de commentaire; ne pas exposer de clés.

### Phase D — Telegram
- Garder un seul mode de réception par instance : polling ou webhook, jamais les deux simultanément.
- Vérifier offset, persistance state.json, anti-doublons, outbox, reprises après HTTP 429/5xx et redémarrage.
- Effectuer un test de livraison contrôlé dans un canal de test autorisé; ne pas envoyer de message promotionnel ou de signal réel sans validation.
- Vérifier que les commentaires IA ne contredisent jamais le sens du signal et qu'ils ne modifient pas Entry/SL/TP.

### Phase E — indicateur et cohérence marché
- Rejouer les captures et snapshots réels; comparer prix courant, prix d'entrée, SL, TP1 et TP2.
- Formaliser les états : préparation, confirmation, entrée théorique, actif, TP1 atteint, TP2 atteint, SL atteint, invalidé, expiré.
- Invalider ou clôturer explicitement un plan quand son prix/temps de validité est dépassé; éviter qu'un ancien plan reste affiché comme actif.
- Tester tous les symboles et timeframes, y compris bougies clôturées et données MTF manquantes.
- Préserver le design et les animations v12.2.3; ne pas modifier le Pine sans test de parité et compilation TradingView.

### Phase F — assainissement du dépôt
- Classer les fichiers hérités par dépendance et usage.
- Déplacer les documents obsolètes dans une archive explicite ou les supprimer seulement après preuve qu'ils ne sont plus référencés.
- Remplacer les chemins absolus trading-auto et les clés localStorage historiques par des identifiants ALIGN si ces composants sont réellement utilisés.
- Retirer les anciens scripts de démarrage du parcours principal; conserver une documentation de migration.
- Ajouter des tests de garde-fou interdisant les chemins OneDrive/Desktop/trading-auto dans les composants runtime ALIGN.

### Phase G — validation et bascule
- Tests Python complets, JavaScript/Node, MTF, Pine/parité, sécurité broker, Telegram, IA, bridge et publication.
- Tester sur environnement miroir, puis comparer avec production.
- Bascule progressive une seule dépendance à la fois avec rollback documenté.
- Contrôler main et live-data séparément.
- Déclarer ALIGN rétabli seulement après vérification des snapshots live, du bot, des commentaires IA, de live.json, des animations et du retour arrière.

## 6. Garde-fous permanents
- Dépôt unique : adelkhatra-bit/trading-align-.
- Production main; publication live-data.
- Aucune modification du dépôt inside-dombe dans ce chantier. Le keep-alive ping des captures est hors périmètre ALIGN tant qu'aucune dépendance n'est prouvée.
- Aucun ordre broker réel.
- Ne jamais afficher les secrets.
- Aucun merge/déploiement sans diff revu, tests verts et validation live.
- Préserver la référence stable et les animations/design.
- Règle de conduite : localiser → isoler → corriger au minimum → tester → vérifier en réel → documenter.

## 7. Modifications effectuées pendant cet audit
Aucune modification de code, aucune suppression, aucun arrêt de processus, aucun merge, aucun déploiement et aucun ordre broker. Audit effectué en lecture seule. Ce rapport est un document de diagnostic et de planification, pas une attestation de remise en état.
