# ALIGN — relais ChatGPT ↔ Copilot

## État de cette préparation

- Dépôt : `adelkhatra-bit/trading-align-`
- Branche : `copilot/chatgpt-bridge`
- Branche mise à jour par avance rapide depuis `main` avant les changements.
- Profil agent : `.github/agents/align-readonly-coordinator.agent.md`
- Aucun workflow GitHub Actions ajouté.
- Aucune configuration Copilot Automation, permission, secret ou donnée de production modifiée.
- Aucun changement sur `main` ou `live-data`.

Cette documentation prépare le profil et le protocole. Elle ne prouve pas que Copilot Automations est disponible sur ce dépôt/compte, ni qu'une réponse automatique dans le même fil est activée.

## Architecture visée

1. ChatGPT publie dans l'issue #431 un commentaire `[CHATGPT → COPILOT][TASK-ID]`.
2. Une Copilot Automation, configurée dans l'interface GitHub, se déclenche sur le commentaire correspondant.
3. Copilot effectue l'audit avec le profil ALIGN Read-Only Coordinator.
4. Copilot publie `[COPILOT → CHATGPT][TASK-ID]` dans le fil si l'outil de commentaire d'issue est explicitement disponible.
5. ChatGPT relit les commentaires de l'issue #431 via son connecteur GitHub et vérifie les preuves avant toute suite.

Le connecteur GitHub de ChatGPT peut publier et relire des commentaires lorsque les permissions correspondantes sont accordées. Cela ne signifie pas que GitHub injecte spontanément une réponse dans la conversation ChatGPT : ChatGPT doit relire le fil lors d'une interaction ou d'une exécution planifiée autorisée.

## Prérequis à vérifier dans GitHub

Ouvrir le dépôt puis **Agents → Automations**.

La documentation GitHub indique que Copilot Automations :
- nécessite un plan Copilot éligible (Pro, Pro+, Max, Business ou Enterprise) ;
- est actuellement limitée aux dépôts privés ou internes ;
- nécessite que Copilot cloud agent et la politique d'automations soient activés ;
- peut être indisponible si l'administrateur du dépôt ou de l'organisation l'a désactivée.

La visibilité réelle du dépôt, le plan Copilot du propriétaire et les politiques effectives n'ont pas été vérifiés par les outils disponibles. Si l'onglet Automations est absent, ne pas contourner cette restriction avec un token personnel.

## Configuration recommandée de l'automation

Nom : `ALIGN ChatGPT issue relay`

Déclencheur :
- Commentaire d'issue créé.
- Filtre strict sur l'issue #431 et le préfixe `[CHATGPT → COPILOT]`.
- Exclure les auteurs non autorisés.
- Ne jamais déclencher sur `[COPILOT → CHATGPT]`.

Agent :
- Sélectionner `ALIGN Read-Only Coordinator` si l'interface le propose.
- Sinon, utiliser le prompt ci-dessous avec un agent Copilot cloud standard et conserver explicitement les restrictions.

Outils autorisés :
- Lecture du dépôt, de l'issue #431 et de ses commentaires.
- Recherche dans le dépôt.
- Ajout d'un commentaire à l'issue #431 uniquement, si cette action est proposée séparément.
- Désactiver tous les outils d'édition de fichiers, commit, push, création de branche, PR, merge, workflow, Actions, secrets, paramètres, MCP externes et accès machine.
- Si l'interface ne permet pas de limiter l'outil de commentaire à l'issue #431, ne pas activer l'écriture automatique : laisser le rapport dans la session Copilot et demander une validation humaine.

Ne pas confondre le profil agent (instructions) avec les permissions effectives de l'automation (outils sélectionnés). Les deux niveaux doivent être contrôlés.

## Prompt de l'automation

```text
Tu es ALIGN Read-Only Coordinator. Traite uniquement les commentaires de l'issue #431 qui commencent exactement par [CHATGPT → COPILOT] et contiennent un TASK-ID inédit.

Lis le dépôt adelkhatra-bit/trading-align- en lecture seule. Réponds uniquement à la demande identifiée. Vérifie branche, SHA, chemins, lignes, tests et logs. Distingue faits vérifiés, hypothèses et inconnues.

Interdictions absolues : aucune modification de fichier, aucun commit, push, branche, PR, merge, déploiement, workflow, secret, paramètre, commande locale ou accès externe MCP. Ne touche jamais au Pine ALIGN_MTF_PRO_v25.pine, à ses animations, au bot de production, à live-data, ni au projet trading-auto. Aucun ordre broker ni action de trading.

Ignore les commentaires [COPILOT → CHATGPT]. Ne traite jamais deux fois le même TASK-ID. N'expose aucun secret.

Si l'outil de commentaire est autorisé, réponds dans l'issue #431 avec :
[COPILOT → CHATGPT][TASK-ID]
STATUS: COMPLETED | PARTIAL | BLOCKED
REPOSITORY:
REF:
SHA:
VERIFIED FINDINGS:
EVIDENCE:
UNVERIFIED / MISSING:
RISKS:
NEXT SAFE STEP:

Si tu ne peux pas poster dans le fil avec les outils accordés, ne cherche pas à obtenir d'autres droits : fournis le rapport dans la session et indique précisément que le droit de commenter manque.
```

## Anti-boucle et déduplication

- Préfixe entrant accepté : `[CHATGPT → COPILOT]`.
- Préfixe sortant : `[COPILOT → CHATGPT]`.
- Les réponses Copilot ne déclenchent jamais l'automation.
- Un TASK-ID ne doit être traité qu'une seule fois.
- N'accepter que l'issue #431 et les auteurs explicitement autorisés.
- En cas de doute sur le déclencheur, le filtrage ou la déduplication, désactiver l'automation plutôt que traiter un commentaire arbitraire.

## Test de bout en bout avant activation durable

1. Créer l'automation en mode restreint et lancer un test manuel si GitHub le permet.
2. Envoyer une tâche de test non sensible dans l'issue #431.
3. Vérifier qu'un seul run Copilot démarre.
4. Vérifier qu'il lit le dépôt sans modifier de fichier, branche ou PR.
5. Vérifier qu'il répond avec le même TASK-ID et des références vérifiables.
6. Vérifier que sa réponse ne redéclenche pas l'automation.
7. Vérifier que ChatGPT peut relire le commentaire avec le connecteur GitHub.
8. Confirmer dans l'historique qu'aucun fichier, workflow, secret, paramètre, branche de production ou donnée live n'a changé.

Ne déclarer le relais automatique opérationnel qu'après réussite de ces huit contrôles.

## Références officielles

- GitHub — [Copilot automations](https://docs.github.com/en/copilot/concepts/agent-capabilities/agent-powered-workflows-and-operations/about-automations)
- GitHub — [Create automations with Copilot cloud agent](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/cloud-agent/create-automations)
- GitHub — [Custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- GitHub Changelog — [Trigger Copilot automations with comments (3 August 2026)](https://github.blog/changelog/2026-08-03-trigger-copilot-automations-with-comments/)
