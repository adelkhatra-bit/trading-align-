# ALIGN TRADING — AGENT RULES

> Read `docs/ALIGN_SOURCE_DE_VERITE.md` first: canonical repository, branches, indicator, data chain and secret status.

## Scope and identity
- This repository is the canonical project: `adelkhatra-bit/trading-align-`.
- Production code branch: `main`. Public live-data publication branch: `live-data`.
- Markets: BTC and GOLD only. NASDAQ is fully removed from active analysis, new entries, monitoring and position follow-up. Legacy NASDAQ state is archived for audit only and must never be reactivated or replayed. Telegram bot: `@align_mtf_adel_bot`.
- Canonical indicator: `align-bot/pine/ALIGN_MTF_PRO_v25.pine` (TradingView title « ALIGN MTF PRO v25 (Inside) »). Other Pine files (v24*, *_PROPOSITION*) are history, never the active indicator. Before acting, every agent verifies repository, branch, PR, SHA, symbol and indicator version; if any is ambiguous or belongs to another project, it stops.
- Apply these rules only to work explicitly identified as ALIGN/TRADING. If the account user or project context is ambiguous, ask before acting.
- Never assume a branch name, SHA, PR state, deployment state, or runtime health. Read it from GitHub immediately before acting.

## Permanent project identity lock — Claude Chrome and ALIGN
- The authorized recovery source identified by the owner is **Claude Chrome**. Do not rename it or substitute Claude Code, VS Code, Cowork, or another tool; keep their sessions and provenance distinct.
- The only target repository is `adelkhatra-bit/trading-align-`. `main` is the production code branch and `live-data` is only the generated public-data branch.
- The former `trading-auto` environment, its pages, servers, workers, Puppeteer sessions, ports, and similarly named local folders are out of scope. Do not inspect their operational data, connect to their ports, reuse their files, change their processes, or delete them during ALIGN work.
- Prove project identity from the canonical GitHub repository, exact branch and SHA, and file provenance. An open port, process name, folder name, browser tab, or old branch label is not proof.
- Claude Chrome conversation history is a discovery index, not proof that a change reached GitHub. Verify source material and decisions in the actual source conversation, then independently confirm each claimed change in the canonical repository and commit history.
- Never assume a `claude/*` branch is current or authoritative because of its name. Verify ancestry, base, SHA, changed files, dependencies, and tests before considering any source.
- During recovery, do not delete old files, branches, projects, servers, or history. First create a provenance inventory (source conversation, repository, branch, SHA, paths, dependencies, tests), propose minimal extraction, and preserve a rollback point.
- No mass merge, mass copy, broad cleanup, or replacement of the Telegram/ALIGN foundation. Preserve verified Telegram, Pine, MTF, bridge, AI, server, state, and live-overlay behavior unless a narrowly scoped change is proven necessary and explicitly approved.
- If the Claude Chrome source conversation or exact project/branch cannot be accessed, report the missing evidence. Never fill gaps by guessing or substituting another agent's history.

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
6. **Canonical TradingView indicator.** The only active indicator is align-bot/pine/ALIGN_MTF_PRO_v25.pine, titled ALIGN MTF PRO v25 (Inside). Never substitute older v24 files or proposal files. Verify the source from current main before work.
7. **Zero regression.** Preserve Pine calculations, signal logic, Entry/SL/TP, MTF behavior, design, Claude-era v12.2 animations, AI commentary, Telegram, bridge, server, memory, and separation of main and live-data.
8. **Stop on uncertainty or failure.** If source, branch ownership, permissions, a live dependency, or expected behavior cannot be verified, report the blocker. Never weaken or delete a failing test to get a green result.
9. **Evidence-based handoff.** Report exact branch and SHA, files, diff, tests and workflow URLs, runtime checks not performed, residual risks, and rollback path. Never claim a change or external process ran without evidence.
10. No human or automated process may place a real broker order through this maintenance workflow. Production trading remains subject to the separate explicit trading safety constraints above.

## External code-agent access is disabled

- ALIGN does not use GitHub Copilot CLI relays, Copilot cloud-agent assignment, repository custom-agent profiles, or automated code-agent handoffs.
- The workflow watchdog and auto-repair coordinator may create or update deduplicated diagnostic issues for human maintainers only. They must never read a Copilot token, query assignable code agents, or assign an agent.
- Runtime AI providers used by the Telegram BOT for market commentary remain a separate production feature. Keep their existing quotas, fallback, consent, market isolation, and safety controls.
- A public repository remains readable by external services, including AI services. Repository instructions cannot prevent external reading; private visibility and GitHub permission changes must be enforced in repository settings by an authorized owner.
- No automated coding agent may write, commit, push, merge, deploy, change secrets, or place broker orders in ALIGN. All changes continue through a focused branch, reviewed diff, green required checks, and explicit human authorization.
- Every contributor must obtain explicit user approval before any merge.
- All merges require explicit owner approval after diff review, required checks, and applicable runtime validation.
