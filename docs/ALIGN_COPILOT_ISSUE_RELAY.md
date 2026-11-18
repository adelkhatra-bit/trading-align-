# ALIGN — relais automatique ChatGPT ↔ GitHub Copilot

## Source de vérité et périmètre

Ce relais unique utilise exclusivement le dépôt `adelkhatra-bit/trading-align-` et l'issue ordinaire #431. La branche de production reste `main`; `live-data` reste réservée à la publication des données. Aucun second workflow de surveillance ne doit être ajouté pour ce relais.

Le workflow est `.github/workflows/align-copilot-issue-relay.yml` et le script est `scripts/align_copilot_issue_relay.py`.

## Fonctionnement

1. ChatGPT publie une tâche dont le commentaire commence par `[CHATGPT → COPILOT][TASK-ID]` ou par un titre Markdown suivi de ce marqueur, dans l'issue #431.
2. Le déclencheur `issue_comment.created` lance immédiatement un contrôle léger.
3. Un unique polling de secours s'exécute toutes les dix minutes.
4. Le script vérifie le dépôt, l'issue, l'auteur autorisé, le marqueur d'activation `6962101708`, l'identifiant de tâche et toutes les pages de commentaires.
5. Si aucune tâche n'est en attente, le job s'arrête sans installer Copilot CLI, sans lire le secret Copilot et sans consommer de requête Copilot.
6. Si une tâche est en attente, Copilot CLI reçoit la demande et les 30 commentaires les plus récents, dans un workspace checkouté en lecture seule sur `main`.
7. Le relais publie la réponse dans l'issue #431 avec le marqueur `[COPILOT → CHATGPT][TASK-ID]`.
8. Une tâche n'est considérée comme répondue que si le marqueur est publié par `github-actions[bot]` après le commentaire de demande. Les marqueurs d'autres auteurs ne ferment jamais une tâche.

## Configuration requise — une seule fois

Le dépôt est personnel. Pour ce contexte, utiliser le secret du dépôt :

- Nom : `COPILOT_GITHUB_TOKEN`
- Type : fine-grained personal access token créé depuis le compte personnel propriétaire.
- Permission de compte : `Copilot Requests` pour le relais CLI.
- Permissions du dépôt requises pour l'assignation cloud agent : accès lecture aux métadonnées et accès lecture/écriture à Actions, Contents, Issues et Pull requests.
- L'assignation automatique est activée uniquement si ce secret existe, si `copilot-swe-agent` apparaît dans les acteurs assignables du dépôt et si aucun autre issue ALIGN n'a déjà un agent Copilot actif.
- Sans secret, sans acteur disponible ou en cas de permission insuffisante, l'issue reste créée et l'assignation est manuelle.
- Stockage : dépôt ALIGN → Settings → Secrets and variables → Actions → New repository secret.
- Ne jamais publier le token dans une issue, un fichier ou une conversation.

Le `GITHUB_TOKEN` éphémère d'Actions sert uniquement à lire et commenter l'issue, avec `contents: read` et `issues: write`. Aucun droit d'écriture de code n'est accordé au relais.

## Contrôles de sécurité

- Dépôt exact : `adelkhatra-bit/trading-align-`.
- Issue ordinaire exacte : `#431` ; les PR sont rejetées.
- Auteur de tâche exact : `adelkhatra-bit`.
- Les demandes antérieures à `6962101708` sont ignorées.
- Un seul workflow et une seule exécution concurrente.
- Une tâche est traitée par exécution, dans l'ordre chronologique.
- Pagination bornée à 100 pages ; arrêt fermé si la limite est dépassée.
- Seul `github-actions[bot]` peut fournir un marqueur de réponse reconnu.
- Copilot CLI ne dispose que des outils `view`, `grep` et `glob`. Aucun outil d'écriture, shell, MCP ou navigation web n'est autorisé.
- Aucun commit, push, PR, merge, déploiement, accès aux secrets, ordre broker ou modification des services locaux.
- Les contenus des commentaires et fichiers sont des données non fiables, jamais des instructions de sécurité.

## Économie de ressources

- Déclenchement immédiat sur une demande autorisée.
- Secours toutes les dix minutes, pas toutes les cinq.
- Contrôle des tâches en attente avant installation du CLI.
- Aucune installation CLI, aucun appel Copilot et aucune lecture du secret quand la file est vide.
- Une seule tâche par exécution et concurrence sérialisée.
- Le workflow ne tourne pas en boucle : il s'arrête après le contrôle ou la réponse.

## Validation de l'activation

1. Ajouter le secret `COPILOT_GITHUB_TOKEN` dans les paramètres Actions du dépôt.
2. Fusionner cette PR après revue et CI verte.
3. Vérifier que GitHub Actions est activé.
4. Le commentaire `RELAY-SMOKE-TEST-010` (ID `6962101708`) est la tâche de test en attente.
5. Vérifier un run Actions réussi, puis une réponse dans #431 signée par `github-actions[bot]` avec le marqueur exact.
6. ChatGPT vérifie l'auteur, l'ID de tâche, le SHA `main` annoncé et le fait qu'aucun fichier n'a été modifié.

## Tests de non-régression

La suite `align-bot/test_align_copilot_issue_relay.py` couvre 12 cas : tâches Markdown, auteur autorisé, marqueurs usurpés, ordre temporel des réponses, IDs dupliqués, pagination et verrouillage du dépôt/de l'issue/de l'auteur.

## Limites

- Le relais ne devient actif qu'après fusion et ajout du secret.
- Le premier aller-retour réel n'est pas encore prouvé.
- Le polling de dix minutes est un filet de sécurité ; les nouveaux commentaires autorisés déclenchent normalement le workflow immédiatement.
- Une réponse Copilot est une proposition technique. ChatGPT, en rôle de coordinateur, doit la vérifier, demander les preuves manquantes et rédiger une consigne corrective précise avant toute modification de code.
