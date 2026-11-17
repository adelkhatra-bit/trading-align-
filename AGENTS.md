# ALIGN TRADING — AGENT RULES

## Scope and identity
- This repository is the canonical project: `adelkhatra-bit/trading-align-`.
- Production code branch: `main`. Public live-data publication branch: `live-data`.
- Markets: BTC, GOLD, NASDAQ. Telegram bot: `@align_mtf_adel_bot`.
- Apply these rules only to work explicitly identified as ALIGN/TRADING. If the account user or project context is ambiguous, ask before acting.
- Never assume a branch name, SHA, PR state, deployment state, or runtime health. Read it from GitHub immediately before acting.

## Permanent project identity lock — Claude Chrome and ALIGN
- The user explicitly identifies the current recovery source as **Claude Chrome**. Do not rename this source to Claude Code, VS Code, Cowork, or another agent/tool. Keep those products and sessions distinct.
- The only target project for this work is the ALIGN repository `adelkhatra-bit/trading-align-`. The target production code branch is `main`; `live-data` is only the public generated-data branch.
- The old project/environment named `trading-auto`, its old web page, old servers, old workers, old Puppeteer sessions, and any similarly named local folders are **out of scope**. Never inspect operational data there, connect to its ports, reuse its files, change its processes, or delete it as part of ALIGN work.
- Never infer project identity from an open port, process name, folder name, browser tab, old branch name, or a shared machine. Prove identity using the GitHub repository URL, exact branch and SHA, and file provenance.
- Claude Chrome conversation history is a discovery index, not proof that a GitHub change was applied. Recover source material and decisions from the actual Claude Chrome conversation(s), then independently verify each claimed change against the canonical ALIGN repository and commit history.
- Do not treat any `claude/*` branch as current or authoritative solely because it contains “claude”. In particular, `claude/live-sans-telegram` is an old v4.6 branch and is 407 commits behind current `main` (verified 2026-11-17); do not merge, reset to, or use it as a base.
- Do not delete old files, branches, projects, servers, or history during recovery. First produce a provenance inventory (source conversation, repo, branch, SHA, paths, dependencies, tests); propose minimal extraction into a new focused branch; preserve an untouched rollback point.
- No mass merge, mass copy, broad cleanup, or replacement of the Telegram/ALIGN foundation. Preserve all verified Telegram, Pine, MTF, bridge, AI, server, state, and live overlay behavior unless a narrowly scoped change is proven necessary and explicitly approved.
- If Claude Chrome's source conversation or its exact project/branch cannot be accessed, report the exact missing access/evidence. Never fill gaps by guessing or substituting Claude Code history.

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
