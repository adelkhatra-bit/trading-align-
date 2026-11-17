# ALIGN TRADING — AGENT RULES

## Scope and identity
- This repository is the canonical project: `adelkhatra-bit/trading-align-`.
- Production code branch: `main`. Public live-data publication branch: `live-data`.
- Markets: BTC, GOLD, NASDAQ. Telegram bot: `@align_mtf_adel_bot`.
- Apply these rules only to work explicitly identified as ALIGN/TRADING. If the account user or project context is ambiguous, ask before acting.
- Never assume a branch name, SHA, PR state, deployment state, or runtime health. Read it from GitHub immediately before acting.

## Branch and change discipline
1. Start every task by recording repository, current default branch, source branch, target branch, PR number, exact head/base SHAs, latest relevant workflow runs, and working-tree state when available.
2. `main` is the production code branch. Never commit directly to it. Make code changes on the existing PR branch for the same issue when its head/base and purpose are verified; otherwise create one focused branch from the latest verified `main`.
3. `live-data` is a publication/data branch for generated public live state (including `live.json`). Do not treat it as a code-development branch, merge it into `main`, or overwrite its generated data with source code.
4. A fix branch must target the intended base explicitly. Never infer a branch from its name. Verify the PR head, base, SHA, changed files, and workflow results.
5. One issue, one focused branch, one minimal change. Do not bundle unrelated fixes, mass-merge PRs, or transplant modules without checking dependencies and provenance.
6. Preserve unrelated commits and user work. No force-push, hard reset, destructive cleanup, or broad revert. For rollback, use a reviewed, narrowly scoped revert on a separate branch.
7. Before writing, inspect the exact current file and blob SHA. After writing, inspect the resulting diff and commit. Never claim a change succeeded without read-back proof.

## Stable baseline and zero regression
- The latest verified, working version is the baseline; identify its exact SHA and evidence for each task rather than hard-coding a possibly stale SHA.
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
- Markets: BTC, GOLD, NASDAQ. Respect the documented multi-timeframe strategy and do not invent a signal when confirmation is absent. Avoid entries in the middle of a range.
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

## Naming clarity and ownership
- Use explicit component names in every report, issue, plan, log summary, and user-facing explanation. When referring to the ALIGN backend, call it **« mon serveur ALIGN »** or **« serveur ALIGN »**; never use the bare word « serveur » if another server, extension, local process, tunnel, or external service could be confused with it.
- For every non-ALIGN component name, state its role and owner at first mention (for example: extension Chrome, userscript Tampermonkey ALIGN Bande Live, tunnel Cloudflare ALIGN, bot Telegram, service Windows, or external application).
- Never present an unfamiliar process, hostname, executable, service, repository, or project name as belonging to ALIGN until its path, configuration, and dependency are verified. If ownership is unknown, label it **non identifié** and do not connect, stop, rename, or repurpose it.
- Before proposing or performing a rename, state the exact old name, new name, component type, owner, affected paths/configuration, and compatibility impact. Ask for explicit approval if the rename changes a visible product name or external integration.

## Visual lock and explicitly requested control placement
- The TradingView visual design is locked: do not change chart layout, colors, typography, band, animations/effects, candles, zones, support/resistance, Entry, SL, TP1, TP2, labels, calculations, signal logic, or Pine source as part of a control-positioning task.
- The user has explicitly requested that the **« ANIMATIONS ON/OFF »** control and the **commentator/voice activation** control be grouped on the **right side of the TradingView chart, beside the notification area**. Treat this as a pending implementation requirement until the exact target is verified in the live browser; a bottom-right dock alone does not satisfy the request if it is not beside the notification area.
- Preserve the existing button behavior, IDs, accessibility attributes, saved preferences, independent animation and voice toggles, and all Claude-era v12.2.3 behavior. Do not remove the commentator feature or the animation feature. Do not add a language selector or change existing language behavior.
- Before moving controls, inspect the actual TradingView notification element and responsive layout in the authorized browser. Anchor to a verified stable element when possible; avoid guessed fixed pixel offsets. Check desktop and narrow viewport behavior, overlap with chart controls, notifications, prices, and candles.
- Add/update regression tests proving both controls are visible and operable beside the notification area, that their settings persist, and that toggling animations does not stop timers, market data, commentary, voice, signal calculations, or Entry/SL/TP display.
- A visual-control change must include before/after evidence and a screenshot-based check. If the notification anchor cannot be identified reliably, do not ship a guessed placement; report the blocker.
- The user's placement approval applies only to these two controls. It is not permission to redesign any other part of the interface.
