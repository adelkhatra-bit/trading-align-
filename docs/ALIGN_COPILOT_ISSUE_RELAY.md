# ALIGN — relais automatique ChatGPT ↔ GitHub Copilot

## Objectif

Permettre à ChatGPT et à GitHub Copilot CLI de s'échanger des tâches et rapports dans l'issue GitHub #431, sans copier-coller manuel après la configuration initiale.

Le relais utilise le workflow `.github/workflows/align-copilot-issue-relay.yml` et le script `scripts/align_copilot_issue_relay.py`.

## Fonctionnement

1. ChatGPT publie un commentaire qui commence par `[CHATGPT → COPILOT][TASK-ID]` dans l'issue #431.
2. Le workflow tente un déclenchement immédiat sur `issue_comment.created`.
3. Un contrôle périodique toutes les cinq minutes sert de secours si le commentaire est publié par une intégration qui ne déclenche pas les workflows.
4. Le script sélectionne une tâche non répondue de l'auteur autorisé `adelkhatra-bit`.
5. Copilot CLI reçoit le contexte récent de l'issue et le dépôt ALIGN checkouté sur `main`.
6. Copilot répond dans le même fil avec `[COPILOT → CHATGPT][TASK-ID]`.
7. Le script déduplique les tâches déjà répondues et traite une seule tâche par exécution.

## Configuration requise — une seule fois

Le dépôt est personnel et non organisationnel. La méthode de facturation Copilot par `GITHUB_TOKEN` documentée par GitHub est destinée aux dépôts appartenant à une organisation avec Copilot. Pour ce dépôt personnel, le relais utilise le secret de dépôt :

- Nom exact : `COPILOT_GITHUB_TOKEN`
- Valeur : fine-grained personal access token disposant de l'autorisation **Copilot Requests**.
- Portée : limiter le jeton au strict nécessaire ; ne pas lui donner de permissions de code en écriture.
- Stockage : dépôt ALIGN → Settings → Secrets and variables → Actions → New repository secret.
- Ne jamais coller la valeur du jeton dans une issue, un commentaire, un fichier ou une conversation ChatGPT.

Le workflow utilise le `GITHUB_TOKEN` éphémère fourni par Actions uniquement avec `contents: read` et `issues: write`, pour lire et commenter l'issue #431.

## Permissions Copilot

Copilot CLI est limité aux outils de lecture `view`, `grep`, `glob` et au droit `read`. Les catégories `write`, `shell`, `url` et `memory` sont explicitement refusées. Aucun accès de modification, commit, push, PR, merge, déploiement, réglage, secret ou ordre broker n'est accordé.

## Déclencheurs et protections

- Issue #431 uniquement ; pas les PR.
- Auteur de demande autorisé : `adelkhatra-bit`.
- Préfixe obligatoire : `[CHATGPT → COPILOT]`.
- Identifiant de tâche obligatoire et unique.
- Réponse marquée : `[COPILOT → CHATGPT][TASK-ID]`.
- Une seule exécution à la fois ; une tâche traitée par exécution.
- Déclencheur planifié toutes les cinq minutes comme filet de sécurité.
- Le workflow ne traite pas les commentaires de réponse Copilot comme de nouvelles demandes.

## Activation et validation

1. Ajouter le secret `COPILOT_GITHUB_TOKEN` dans les paramètres Actions du dépôt.
2. Fusionner la PR après revue et tests.
3. Vérifier que GitHub Actions est activé pour le dépôt.
4. Publier une demande de test non sensible dans l'issue #431, avec un TASK-ID neuf.
5. Vérifier le run Actions et la réponse de Copilot dans le même fil.
6. ChatGPT relit ensuite cette réponse avec son connecteur GitHub.

## Limites connues

- Le premier déploiement n'est pas opérationnel tant que le secret Copilot n'est pas configuré et que la PR n'est pas fusionnée.
- Le polling de secours peut ajouter jusqu'à cinq minutes de délai.
- Le relais fait intervenir Copilot CLI dans GitHub Actions ; il ne connecte pas directement l'interface locale « Guide Hub » à ChatGPT. Il crée un agent Copilot automatisé qui communique avec ChatGPT par l'issue GitHub.
- Si Copilot Requests n'est pas inclus dans le jeton ou le plan, le workflow échouera à l'authentification ; aucun contournement ne sera tenté.
