# ALIGN TRADING — AGENT RULES

> Read `docs/ALIGN_SOURCE_DE_VERITE.md` first: canonical repository, branches, indicator, data chain and secret status.

## Scope and identity
- **Single project identity:** ALIGN TRADING is the canonical product name. `Trading Auto` / `trading-auto` is a historical/internal alias for the same project, not another project or code version. All maintenance, updates, issues and PRs must resolve to this single repository and its canonical branches. Do not create a parallel Trading Auto repository or branch family.
- This repository is the canonical project: `adelkhatra-bit/trading-align-`.
- Production code branch: `main`. Public live-data publication branch: `live-data`.
- Markets: BTC and GOLD only. NASDAQ is fully removed from active analysis, new entries, monitoring and position follow-up. Legacy NASDAQ state is archived for audit only and must never be reactivated or replayed. Telegram bot: `@align_mtf_adel_bot`.
- Canonical data/bridge indicator: `align-bot/pine/ALIGN_MTF_PRO_v25.pine` (TradingView title « ALIGN MTF PRO v25 (Inside) »); it is the only source allowed to publish snapshots to ROBOT V12. The exact companion `align-bot/pine/ALIGN_MTF_PRO_v24.pine` may remain on TradingView for candle-close visuals only: no `alert()`/`alertcondition()`, no webhook/bridge, and no BOT consumption. Other v24*, *_PROPOSITION* and proposal files remain historical. Before acting, every agent verifies repository, branch, PR, SHA, symbol and indicator version; if any is ambiguous or belongs to another project, it stops.
- Apply these rules only to work explicitly identified as ALIGN/TRADING. If the account user or project context is ambiguous, ask before acting.
- Never assume a branch name, SHA, PR state, deployment state, or runtime health. Read it from GitHub immediately before acting.

## Historical provenance reference - Claude Chrome and ALIGN
- Claude Chrome is preserved as a historical provenance/source-history reference only. It is not a repository-managed agent and grants no coding agent access or write authorization. Keep historical session provenance distinct; do not substitute another source or infer unverified history.
- The only target repository is `adelkhatra-bit/trading-align-`. `main` is the production code branch and `live-data` is only the generated public-data branch.
- `Trading Auto` is a historical/internal alias for this exact same ALIGN TRADING project, not a separate repository, product, runtime, server, or codebase. Treat mentions of `Trading Auto`, `trading-auto`, `ALIGN`, and `ALIGN TRADING` as references to this one project when provenance points to this canonical repository. Never split work by these names or create a second source of truth. The canonical product name is `ALIGN TRADING`; the canonical repository is `adelkhatra-bit/trading-align-`; the canonical code branch is `main`.
- Prove project identity from the canonical GitHub repository, exact branch and SHA, and file provenance. An open port, process name, folder name, browser tab, or old branch label is not proof.
- Claude Chrome conversation history is a discovery index, not proof that a change reached GitHub. Verify source material and decisions in the actual source conversation, then independently confirm each claimed change in the canonical repository and commit history.
- Never assume a `claude/*` branch is current or authoritative because of its name. Verify ancestry, base, SHA, changed files, dependencies, and tests before considering any source.
- During recovery, do not delete old files, branches, projects, servers, or history without provenance. For an owner-authorized scope cleanup, preserve a complete pre-cleanup branch snapshot, prove candidate files have no production consumer, and remove only the unrelated active-tree copy through a reviewed PR. Never delete the archive snapshot.
- No mass merge, mass copy, or replacement of the Telegram/ALIGN foundation. When the owner explicitly requests scope isolation, inventory every candidate, verify imports/workflows/runtime consumers, create an exact pre-cleanup archive, remove only proven unrelated legacy components on a dedicated PR, and run the complete ALIGN validation suite. Preserve verified Telegram, Pine, MTF, Cloudflare mailbox, ROBOT V12 bridge, AI, state, and live-overlay behavior.
- If the Claude Chrome source conversation or exact project/branch cannot be accessed, report the missing evidence. Never fill gaps by guessing or substituting another agent's history.

## Branch and change discipline
1. Start every task by recording repository, current default branch, source branch, target branch, PR number, exact head/base SHAs, latest relevant workflow runs, and working-tree state when available.
2. `main` is the production code branch. Never commit directly to it. Make code changes on the existing PR branch for the same issue when its head/base and purpose are verified; otherwise create one focused branch from the latest verified `main`.
3. `live-data` is a publication-only branch. Its root may contain only `live.json` and, when created by the bot, `fermes.json`. No source code, workflow, HTML, documentation, Pine, JavaScript, or other application files may exist there. Never develop on or merge this branch into `main`. CI verifies its remote tree on every validation run.
4. A fix branch must target the intended base explicitly. Never infer a branch from its name. Verify the PR head, base, SHA, changed files, and workflow results.
5. One issue, one focused branch, one minimal change. Do not bundle unrelated fixes, mass-merge PRs, or transplant modules without checking dependencies and provenance.
6. Preserve unrelated commits and user work. No force-push, hard reset, destructive cleanup, or broad revert on code branches. The one-time `live-data` cleanup was performed only after archiving its exact old head; any future rewrite of that publication branch requires explicit owner authorization, a fresh archive, preservation of generated data, and the CI tree guard. For code rollback, use a reviewed, narrowly scoped revert on a separate branch.
7. Before writing, inspect the exact current file and blob SHA. After writing, inspect the resulting diff and commit. Never claim a change succeeded without read-back proof.

## Stable baseline and zero regression
- The latest verified, working version is the baseline; identify its exact SHA and evidence for each task rather than hard-coding a possibly stale SHA.
- Active runtime boundary: `align-bot/`, `cloud/align-tv-mailbox/`, `docs/live/`, `scripts/align_*.py`, `scripts/validate_align_source_of_truth.py`, and the ALIGN GitHub workflows. Read-only Topstep/MetaAPI safety checks remain only where they are explicitly connected to ALIGN; no legacy local server, generic dashboard, MT5 bridge, or second TradingView extension may be treated as a production dependency.
- Preserve the TradingView indicator design and all validated Claude-era v12.2 behavior: live band, animations, AI commentary/bubbles, controls, time display, and MTF dashboard. Do not simplify, remove, rename, or reposition these without explicit approval.
- Preserve Pine v24 / ROBOT V12 behavior and all established integrations. Recover only modules whose source, version, dependencies, and compatibility are verified.
- If a change fails any required test, do not merge or deploy it. Isolate the failure, fix and retest, or revert only that change to the last verified stable state without overwriting other work.

## Architecture and runtime
Understand dependencies among Pine v24, TradingView ROBOT V12, bridge, live overlay/userscript, public `live-data/live.json`, Telegram bot, AI providers, server, `state.json` persistence, GitHub Actions, and GitHub Pages. Change only the affected component and proven dependencies.
For relevant changes, verify:
- Python compilation and targeted Python tests.
- Pine/TradingView source checks and JavaScript syntax/tests.
- Full MTF regression suite when signal, indicator, or shared logic changes.
- Signal direction, confirmation/closed-candle rules, Entry, SL, TP1/TP2, and market-specific behavior.
- Telegram connectivity and delivery behavior without sending unsolicited messages; opt-in preferences, deduplication, and retry handling.
- Real AI-provider connectivity and graceful fallback.
- TradingView bridge connectivity, data freshness, schema, and live JSON producer/consumer URL agreement.
- Server/worker health, state restore/save integrity, GitHub Pages deployment, and actual live display where accessible.
A green workflow is not proof that the live system works. Clearly distinguish automated tests, connectivity checks, and real end-to-end verification.

## Trading and safety constraints
- Markets: BTC and GOLD only. NASDAQ is fully excluded from analysis, entry, monitoring and position follow-up; legacy state is audit archive only and must never be replayed. Respect the documented multi-timeframe strategy and do not invent a signal when confirmation is absent. Avoid entries in the middle of a range.
- Never place real broker orders or enable auto-trading.
- TopStep constraint: maximum one open position and exactly one micro-contract.
- Keep credentials in GitHub Secrets or the approved secret manager. Never print, copy into files, commit, or expose secret values. Report only whether required secrets are present/usable, never their values.

## Review and release gate
Before a PR is approved or merged:
1. Read the complete diff and inspect affected callers, tests, and dependent modules.
2. Confirm the PR targets the intended base and contains only the scoped fix.
3. Run targeted tests and all relevant regression checks.
4. Confirm all required checks pass on the exact PR head SHA.
5. Verify no stable feature, animation, comment, user setting, memory, or unrelated change was lost.
6. Confirm deployment and runtime behavior after merge when access permits.
Never merge or deploy on a failed, missing, stale, or mismatched required check. Do not merge automatically; obtain explicit user approval for the merge.

## Required work report
For each task report, concisely: issue and proven root cause; repository/branch/PR/base SHA/head SHA; files changed; minimal fix; tests and exact results; runtime checks; residual risks; and rollback plan. State explicitly what was not verified. Never claim continuous background monitoring or completed work without evidence.

## Human maintainer protocol

This procedure applies to the repository owner and explicitly authorized human maintainers. It does not authorize a repository-managed coding agent.

1. **Read-only first.** Verify the canonical repository, issue, branch, PR, base/head SHAs, changed-file list, latest checks, canonical Pine source, and working-tree state before modifying anything.
2. **Localize the defect.** Identify the exact file, function or block, line range, root cause, reproduction scenario, and affected behavior. Do not infer a cause from a failing workflow name alone.
3. **Minimal plan before changes.** Record the exact files and behavior to change, focused regression tests, side effects, and rollback path. Obtain owner authorization before changing shared production code.
4. **No branch takeover.** Never replace, rewrite, rebase, reset, force-push, or bulk-synchronize an existing branch. Preserve every existing commit and unrelated change. Use an isolated branch from the current verified main when the existing work is not demonstrably the same task.
5. **One defect, one focused change.** Do not bundle unrelated findings or opportunistic refactors. Touch only the smallest set of files required by the proven dependency chain.
6. **Canonical TradingView indicators.** The only data/bridge indicator is align-bot/pine/ALIGN_MTF_PRO_v25.pine, titled ALIGN MTF PRO v25 (Inside). The exact align-bot/pine/ALIGN_MTF_PRO_v24.pine companion is permitted for candle-close visuals only and must never emit alerts or feed ROBOT V12. Never substitute other v24 files or proposal files. Verify both sources from current main before work.
7. **Zero regression.** Preserve Pine calculations, signal logic, Entry/SL/TP, MTF behavior, design, Claude-era v12.2 animations, AI commentary, Telegram, bridge, server, memory, and separation of main and live-data.
8. **Stop on uncertainty or failure.** If source, branch ownership, permissions, a live dependency, or expected behavior cannot be verified, report the blocker. Never weaken or delete a failing test to get a green result.
9. **Evidence-based handoff.** Report exact branch and SHA, files, diff, tests and workflow URLs, runtime checks not performed, residual risks, and rollback path. Never claim a change or external process ran without evidence.
10. No human or automated process may place a real broker order through this maintenance workflow. Production trading remains subject to the separate explicit trading safety constraints above.


## Terminologie obligatoire — animations sur TradingView

- Quand le propriétaire dit « animations », « animations ALIGN », « bulles », « bande live » ou « coach vocal sur TradingView », la cible par défaut est **l'overlay Tampermonkey `docs/live/align-bande-live.user.js` exécuté directement sur les graphiques `https://*.tradingview.com/chart/*`**. C'est la surface visuelle principale : bande animée, bulles, effets, commandes, commentaires IA et lecture vocale navigateur.
- Ne jamais interpréter une demande d'« animations sur TradingView » comme une demande d'ouvrir, modifier ou rétablir l'interface de la page GitHub Pages `/live/`. Ne jamais présenter cette page comme l'interface quotidienne du propriétaire.
- `docs/live/index.html` est une **scène auxiliaire de diffusion**, transparente et conçue pour TikTok LIVE Studio. Elle lit le résumé public `live-data/live.json`, publie les dialogues du duo Thomas/Leïla dans le canal `LIVE_SHOW` et anime leurs avatars/bouches à partir des événements vocaux du userscript. Elle n'est ni l'overlay TradingView ni le panneau de commande Tampermonkey.
- Le Worker Cloudflare `align-tv-mailbox` et son Durable Object `LIVE_SHOW` sont des dépendances de synchronisation entre la scène et l'overlay. Ne pas les débrancher au motif que le propriétaire n'utilise pas la page `/live/`. Toute suppression ou migration doit d'abord prouver que le producteur de dialogues est repris ailleurs et que le coach vocal sur TradingView reste autonome et testé.
- La voix entendue sur TradingView est prononcée par `window.speechSynthesis` dans le navigateur, uniquement après activation explicite de « COACH VOCAL ON ». Les événements START/STOP synchronisent seulement l'animation des avatars de la scène ; ils ne transportent pas l'audio vers TradingView. Distinguer impérativement « état vocal activé », « voix système compatible trouvée », « synthèse démarrée » et « son réellement entendu ».
- À chaque tâche liée aux animations, vérifier séparément : script Tampermonkey réellement installé et version, exécution sur un graphique TradingView, contrôles visibles, animations activées, commentaires IA reçus, voix navigateur disponibles par langue/locuteur, état `LIVE_SHOW`, et synchronisation START/STOP. Une page `/live/` HTTP 200 ou un Worker sain ne prouve pas que l'overlay ni l'audio fonctionnent.
- Ne jamais remplacer les animations TradingView par la scène `/live/`, ni modifier leur design, leur placement, leurs effets ou leur comportement sans demande explicite. Préserver toutes les fonctions Claude-era v12.2.

## External code-agent access is disabled

- ALIGN does not use GitHub Copilot CLI relays, Copilot cloud-agent assignment, repository custom-agent profiles, or automated code-agent handoffs.
- The workflow watchdog and auto-repair coordinator may create or update deduplicated diagnostic issues for human maintainers only. They must never read a Copilot token, query assignable code agents, or assign an agent.
- Runtime AI providers used by the Telegram BOT for market commentary remain a separate production feature. Keep their existing quotas, fallback, consent, market isolation, and safety controls.
- A public repository remains readable by external services, including AI services. Repository instructions cannot prevent external reading; private visibility and GitHub permission changes must be enforced in repository settings by an authorized owner.
- No automated coding agent may write, commit, push, merge, deploy, change secrets, or place broker orders in ALIGN. All changes continue through a focused branch, reviewed diff, green required checks, and explicit human authorization.
- Every contributor must obtain explicit user approval before any merge.
- All merges require explicit owner approval after diff review, required checks, and applicable runtime validation.
