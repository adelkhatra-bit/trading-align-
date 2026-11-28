ALIGN TRADING — AGENT OPERATING RULES
Policy version: 2.1
Repository: adelkhatra-bit/trading-align-
Production code branch: main
Publication-only branch: live-data
Telegram bot: @align_mtf_adel_bot
Before every task, read docs/ALIGN_SOURCE_DE_VERITE.md and the relevant system map/documentation. This file defines agent permissions and safety gates; the source-of-truth documentation defines the current technical architecture. Verify all repository facts from GitHub at task time.

1. Purpose and operating principles
ALIGN TRADING is a single, maintained trading-software project. AI assistants and human maintainers may investigate, diagnose, test, fix bugs, and make narrowly scoped improvements. The goal is reliable incremental maintenance—not a rewrite, redesign, migration, or replacement of the existing system.

All contributors must follow these principles:
1. Evidence before action: inspect the live repository, exact branch, commit SHA, changed files, relevant workflows, and current source before making claims or changes.
2. Smallest safe change: fix the demonstrated defect with the smallest practical diff. Do not refactor unrelated modules or bundle unrelated work.
3. Preserve working behavior: keep all validated functionality, user experience, integrations, data contracts, and historical compatibility unless the owner explicitly requests a specific change.
4. Test the actual risk: add or update regression tests for the defect and run the complete relevant validation set.
5. Fail closed: missing, stale, contradictory, invalid, or unverified trading data must result in a safe waiting state—not a guessed signal or fabricated levels.
6. Human-controlled release: agents may prepare branches and pull requests under the authorization rules below, but may never merge or deploy without separate explicit owner approval.
7. Honest reporting: never claim a test, integration, deployment, or live check succeeded unless its result was actually observed and tied to the exact commit or runtime tested.
No process can mathematically guarantee that regressions will never occur. These rules are designed to prevent avoidable regressions, detect them before release, and make every change traceable and reversible.
2. Project identity and scope
- Canonical product name: ALIGN TRADING.
- Canonical repository: adelkhatra-bit/trading-align-.
- Trading Auto / trading-auto is a historical/internal alias for this same project only. Do not create a second product, repository, runtime, or branch family.
- Production source branch: main.
- Public generated-data branch: live-data.
- Active markets: BTC and GOLD only (BTCUSD and XAUUSD, subject to the exact symbol mapping in the current source-of-truth documentation).
- NASDAQ is excluded from active analysis, new entries, monitoring, and position follow-up. Legacy NASDAQ state is archival/audit material only and must never be reactivated or replayed.
- Telegram bot: @align_mtf_adel_bot.
- If the repository, product, symbol, indicator, branch, or requested scope is ambiguous, stop and ask the owner. Do not infer identity from a local folder, open port, process name, browser tab, or historical branch label.
3. Canonical architecture and sources
Read docs/ALIGN_SOURCE_DE_VERITE.md first and follow its current architecture map. The known canonical components are:
- Pine data/bridge indicator: align-bot/pine/ALIGN_MTF_PRO_v25.pine, TradingView title ALIGN MTF PRO v25 (Inside). It is the only indicator authorized to publish snapshots consumed by ROBOT V12.
- Visual companion: align-bot/pine/ALIGN_MTF_PRO_v24.pine. It is candle-close visuals only: no alert(), no alertcondition(), no webhook/bridge output, and no ROBOT V12 consumption. Other v24 variants, proposals, and proposition files are historical unless the current source-of-truth document explicitly changes this.
- TradingView bridge chain, as currently documented: TradingView Pine v25 → Cloudflare Worker align-tv-mailbox → Durable Object mailbox → align_tv_mailbox_feeder.py → align-bot/align_tv_bridge.py in the GitHub runner → ROBOT V12 MTF endpoint → align-bot/align_bot.py → Telegram and generated live data.
- Telegram bot: @align_mtf_adel_bot.
- Public generated data: live-data/live.json and, when produced by the bot, live-data/fermes.json.
- Main live TradingView visual overlay: Tampermonkey userscript docs/live/align-bande-live.user.js, running on TradingView chart pages.
- Auxiliary broadcast scene: docs/live/index.html, intended for TikTok LIVE Studio. It is not the TradingView overlay or its control panel.
- Cloudflare Worker and Durable Object LIVE_SHOW are synchronization dependencies for the auxiliary scene/overlay where documented. Do not remove or bypass them without tracing and testing every producer and consumer.
- The bot also depends on its AI-provider routing/fallback, news and risk filters, persistence/state handling, GitHub Actions, and publication path. Verify actual consumers before changing any shared interface.
If this file and the current source-of-truth documentation or implementation disagree, do not guess. Record the conflict, inspect the latest relevant commits and tests, and ask the owner when the intended behavior cannot be proven.
4. Indicator, market-data, and signal authority
1. Pine v25 is the canonical source for TradingView bridge snapshots and the trade plan. Never substitute a local estimate, an old Pine variant, or an unverified external source for a canonical Pine plan.
2. Keep these concepts distinct in code and user-facing messages:
   - TradingView/Pine price and snapshot provenance;
   - local bot price/calculations;
   - Pine/ROBOT V12 timeframe readings;
   - local ALIGN timeframe readings;
   - MTF plan confirmation;
   - closed-candle entry-trigger confirmation;
   - actual price-in-entry-zone validation.
3. The local price may be displayed as secondary context, but must not be presented as the TradingView reference price. Label the source clearly.
4. Entry, SL, TP1, TP2, and entry zone must come from the valid canonical Pine v25 plan. Do not manufacture or silently replace those values with local estimates.
5. Distinguish a valid MTF-confirmed plan from an entry trigger that has actually closed and confirmed. A prepared plan is not an executable entry signal.
6. If the required TradingView snapshot is missing, stale, malformed, symbol-mismatched, timeframe-mismatched, internally contradictory, or outside its validity window, do not present its levels as a live confirmed plan. Use the project's safe waiting state, including DIVERGENCE DES SOURCES — ATTENTE where appropriate.
7. Never convert a local bias, forecast, proxy candle, or AI opinion into a confirmed trade entry. AI commentary may explain verified data but may not override signal authority or invent prices/levels.
8. Preserve closed-candle rules, MTF confirmation, per-market logic, risk/reward gates, news/session filters, deduplication, and trade-state transitions. Do not weaken safety conditions to increase signal frequency.
9. Do not introduce NASDAQ back into active paths, replay legacy NASDAQ state, or allow one market's state/data to leak into another market.
5. Agent authorization and permissions
5.1 Read access
Any assistant or AI tool may perform read-only inspection when the user requests ALIGN work and the connected integration grants access. Read access does not imply write access.
5.2 Conditional write authorization
The repository owner may explicitly authorize an AI coding agent to perform a specific ALIGN maintenance task. Once the owner has approved the task in the current instruction/conversation, and the agent's connected GitHub integration has the necessary repository permissions, that agent is authorized to:
- create a new, focused branch from the latest verified main;
- modify the minimum necessary source and test files;
- add or update regression tests and narrowly scoped documentation;
- commit and push to its own task branch;
- create or update the corresponding pull request;
- inspect checks and update the branch/PR without overwriting another contributor's work.
This conditional authorization applies to ChatGPT and other AI coding tools only when the owner has explicitly assigned or approved the task. It does not grant an agent access to an account, credential, repository, or connector that the agent does not actually possess. Repository instructions do not bypass GitHub branch protection, review requirements, organization policy, or platform permissions.
5.3 Actions reserved to the owner or categorically forbidden
Task-level permission to edit code does not transfer production authority. The following boundaries are non-negotiable for coding agents:

The owner performs these actions personally; agents do not perform them, even after a general task authorization:
- merge a pull request or enable auto-merge;
- deploy, publish, promote, or change production runtime configuration;
- commit directly to main;
- change repository rules, branch protections, repository visibility, or access permissions;
- modify, rotate, delete, reveal, copy, log, or otherwise handle secret values, tokens, credentials, or private keys;
- rewrite shared history, force-push, hard-reset, delete branches, or take over another agent's branch;
- make broad refactors, mass merges, mass copies, or destructive cleanups.
Categorically forbidden for every agent and every maintenance workflow:
- place real broker orders, enable live auto-trading, or alter broker account permissions;
- bypass risk limits, market isolation, MTF confirmation, closed-candle rules, or fail-closed behavior;
- modify this policy to expand the modifying agent's own permissions.
The owner retains the right to change repository policy personally. Any change to this policy must be reviewed and published by the owner; an agent must never grant itself additional authority. The owner manually reviews, merges, and deploys only after the applicable checks and runtime evidence are satisfactory.
5.4 Multiple-agent coordination
Multiple AI agents may work on ALIGN, but they must not compete on the same branch or silently overwrite one another.
- One issue/defect = one owner-designated task, one focused branch, one PR.
- Each agent records its identity/tool, task, base SHA, branch, and PR in its handoff.
- Use a unique branch per task/agent. Never assume an existing branch is available; inspect its PR, commits, owner, and purpose first.
- Do not edit another agent's branch unless the owner explicitly assigns that handoff and the current branch owner/work is verified.
- Before every push, fetch/check the remote branch and verify that its current head is still the commit the agent expects. If it changed unexpectedly, stop and reconcile; never force-push.
- If two tasks touch the same shared contract or file, coordinate through the issue/PR and sequence the changes. Do not create competing implementations.
- Each PR must state the files changed, tests run, known limitations, and any dependency on another PR.
6. Branch and Git workflow
1. At task start, record:
   - repository and default branch;
   - current main SHA;
   - source branch and target branch;
   - relevant PR number, base SHA, and head SHA, if any;
   - latest relevant workflow runs and their commit SHAs;
   - exact files/blobs to be changed;
   - current status of any existing task branch.
2. Never commit directly to main.
3. Create a new branch from the latest verified main unless a verified existing PR is explicitly the same task and the owner authorizes continuing it.
4. live-data is publication-only. Its root may contain only live.json and, when generated by the bot, fermes.json. Never put source code, Pine, JavaScript, HTML, workflows, documentation, or application files on that branch. Never develop on it or merge it into main.
5. One issue, one focused branch, one minimal PR. Set the PR base explicitly to main unless the owner has specified a different valid target.
6. Preserve all unrelated commits and work. No force-push, hard reset, destructive cleanup, broad revert, or unreviewed cherry-pick.
7. Before every write, inspect the exact current file and blob SHA. After every write, read the file and commit back from GitHub and inspect the full diff.
8. If main advances while the task is in progress, assess whether the PR branch is behind or conflicts. Update it only through a non-destructive, reviewed operation; rerun all affected tests after any rebase/merge/update. Never overwrite other work to make the branch appear current.
7. Change protocol: diagnose, fix, prove
For each defect or improvement:
1. Reconfirm identity: repository, branch, SHA, symbol, indicator, relevant PRs, and current code.
2. Reproduce/localize: identify the exact function/file/line range, inputs, failure mode, expected behavior, and affected callers. A failing workflow name alone is not a root cause.
3. Trace dependencies: inspect direct callers, producers/consumers, payload schemas, state transitions, related tests, and relevant workflows. Do not edit only one side of a data contract.
4. Define the minimum plan: list intended files, exact behavior, regression tests, side effects, risks, and rollback path before writing.
5. Add a regression test: reproduce the current defect and assert the corrected behavior. Do not weaken, delete, skip, or loosen an existing test merely to obtain a green result.
6. Implement the smallest fix: no opportunistic refactoring, renaming, redesign, or unrelated cleanup.
7. Validate locally/through CI: run targeted tests first, then every relevant regression suite and static check. Record exact commands, exit codes, test counts, and commit SHA.
8. Review the diff: inspect every changed line, check for accidental formatting/data changes, confirm no unrelated files were touched, and verify the branch/PR base.
9. Read back from GitHub: confirm the pushed commit SHA, file contents, PR diff, and checks match the work just tested.
10. Handoff: report evidence, unresolved checks, residual risks, and rollback. Do not describe the task as complete if any required gate is missing.
8. Zero-regression and preservation requirements
Preserve all verified and intended functionality, including:
- Pine v25 calculations, alerts, payload schema, signal logic, closed-candle/MTF rules, Entry/SL/TP, and market-specific behavior;
- ROBOT V12 strategy and risk controls;
- TradingView bridge, Cloudflare mailbox, feeder, runner endpoint, and data freshness/identity checks;
- Telegram bot commands, callbacks, buttons, user preferences, opt-in cadence, deduplication, retry behavior, and signal/message semantics;
- AI commentary, provider routing, quotas, consent, internal fallback, and separation between market decisions and explanatory commentary;
- state.json/memory persistence, restore/save integrity, trade lifecycle, and audit history;
- live-data/live.json producer/consumer contract and GitHub Pages publication;
- Tampermonkey TradingView overlay docs/live/align-bande-live.user.js and all validated Claude-era v12.2 behavior: live band, animations, bubbles/effects, controls, comments, time display, MTF dashboard, and voice behavior;
- the distinct auxiliary TikTok LIVE Studio scene docs/live/index.html and its documented synchronization dependencies.
Do not change the ALIGN name, established visual design, animation style, control placement, language separation, or user-facing text conventions without explicit owner approval. Keep French and English content correctly separated; do not accidentally mix translations or duplicate notifications.

Do not treat an HTTP 200 response, a green workflow, an active process, a connected bridge, or an enabled voice toggle as proof that the full user-visible feature works. Verify the actual layer relevant to the task.
9. Validation matrix
Choose tests based on the changed dependency chain. Do not claim unrelated checks are required for every documentation-only change, but do not omit critical tests when shared logic or an integration is affected.
Python/BOT
- Python compilation and imports for changed modules.
- Targeted unit/regression tests for the defect.
- Relevant BOT/coach, Telegram rendering, memory/state, and MTF test suites.
- Verify BTC and GOLD paths separately where market-specific behavior is involved.
Pine/TradingView
- Run repository Pine/source validators and relevant static tests.
- Verify only canonical Pine v25 publishes bridge data.
- Verify symbol/timeframe identity, snapshot freshness, schema, closed-candle behavior, MTF direction, plan confirmation, trigger confirmation, Entry/SL/TP1/TP2, and zone validation.
- Do not claim TradingView compilation or chart execution unless actually tested in TradingView or through an authoritative available check.
JavaScript/overlay
- Run syntax and relevant userscript tests.
- Preserve the exact TradingView target and Tampermonkey behavior.
- When visuals/voice are touched, separately verify installed script version, execution on a TradingView chart, visible controls, animation state, AI comments, available browser voices, synthesis start, audible output where testable, and LIVE_SHOW START/STOP synchronization.
- Do not substitute the /live/ scene for the TradingView overlay.
Bridge/server/data
- Verify worker/feeder/bridge endpoint agreement, HTTP/auth behavior without exposing credentials, valid payload schema, symbol/timeframe mapping, timestamps, freshness, duplicate handling, and producer/consumer URLs.
- Verify generated live.json shape and publication path without writing application code to live-data.
- Verify server/worker health and state restore/save where accessible.
Telegram/AI
- Test message formatting and callback handling with controlled test data or a designated test destination.
- Do not send unsolicited test messages to real users or alter their opt-in preferences.
- Confirm deduplication, retries, rate limits, market isolation, and safe fallback.
- Do not treat an AI provider response as a trading signal or source of Entry/SL/TP.
End-to-end and release
- For signal/trade changes, verify the relevant chain from Pine snapshot through bridge/BOT message using safe test data and, where authorized and accessible, a real read-only runtime observation.
- Record what is automated, what is a connectivity check, what is a simulated test, and what was verified live.
- A green workflow on a different SHA is irrelevant. Required checks must pass on the exact PR head SHA.
- A green workflow alone never proves production health.
10. Trading, financial, and credential safety
- Never place real broker orders or enable live auto-trading through this maintenance workflow.
- Never use test procedures that can create an actual position or modify a live account.
- TopStep constraint: at most one open position and exactly one micro-contract, where applicable. Never bypass account/platform limits.
- Never expose, print, copy, log, commit, or place credentials in source files. Keep credentials in GitHub Secrets or the approved secret manager.
- Do not read or dump environment variables wholesale. When checking a secret, report only whether it is configured/usable, never its value.
- Do not change, rotate, delete, or add secrets without separate explicit owner authorization and the approved secret-management procedure.
- Keep public data free of private identifiers, account details, tokens, or other sensitive information.
11. Pull-request review and release gate
A pull request is ready for owner review only when:
1. It targets the intended base (main for source changes).
2. It contains one focused issue and a minimal, fully reviewed diff.
3. The root cause and reproduction are documented.
4. Regression tests cover the original defect and relevant edge cases.
5. All required checks pass on the exact PR head SHA; none are missing, stale, skipped unexpectedly, or tied to another commit.
6. The PR preserves the existing architecture, user experience, protections, and unrelated work.
7. Runtime checks are reported accurately, including those that could not be performed.
8. A rollback path is documented.
Agents may request review and provide a recommendation. Only the owner may authorize the merge. Only the owner may authorize deployment or publication changes outside the normal approved automation. Never enable auto-merge.

If a required test or check fails, do not merge. Diagnose, correct on the task branch, and rerun. If a safe correction cannot be proven, leave the PR unmerged and report the blocker.
12. Rollback and incident handling
- Every code change must be reversible through a focused revert or follow-up correction.
- Never reset or rewrite shared history to roll back a code change.
- Before any owner-authorized cleanup or migration, inventory consumers, preserve an exact archive/snapshot, and prove the target is unused before removal.
- Never delete archive branches or historical provenance without separate explicit owner authorization.
- If a regression is detected after merge/deployment, stop further rollout, notify the owner with exact SHA and evidence, and propose the smallest safe revert/mitigation. Do not independently deploy a rollback without owner approval unless a separately documented emergency procedure explicitly grants that action.
13. Claude Chrome and historical provenance
- Claude Chrome is a historical provenance/source-history reference, not proof that a change reached the canonical repository and not an authorization mechanism.
- Conversation history may help locate a past decision, but verify source files, branch ancestry, commit SHA, dependencies, and tests in GitHub before relying on it.
- Never assume a claude/* branch is current or authoritative from its name.
- If the original conversation/source cannot be accessed, state what evidence is missing. Do not invent history or substitute another tool's output.
- During recovery, do not delete old files, branches, projects, servers, or history without provenance and explicit owner approval.
14. Terminology and live visual components
- When the owner says “animations”, “ALIGN animations”, “bubbles”, “live band”, or “TradingView voice coach”, the default target is docs/live/align-bande-live.user.js running directly on https://*.tradingview.com/chart/*.
- docs/live/index.html is the auxiliary TikTok LIVE Studio broadcast scene. It is not the daily TradingView overlay or its control panel.
- The Cloudflare Worker align-tv-mailbox and Durable Object LIVE_SHOW are synchronization dependencies where specified by the current architecture. Do not disconnect them without proving that every producer/consumer is replaced and all affected behavior is tested.
- TradingView browser speech uses window.speechSynthesis only after the user explicitly enables the voice coach. START/STOP events may synchronize scene animations; they do not themselves transport audio to TradingView.
- Distinguish these separate states: voice toggle enabled, compatible system voice found, synthesis started, and sound actually heard.
- Do not change animation design, placement, effects, or behavior without explicit owner approval. Preserve all validated Claude-era v12.2 behavior.
15. External agents, automation, and AI services
- External coding agents (including GitHub Copilot agents or other connected AI tools) may be used only when the owner explicitly requests/approves their task and the platform/repository permissions allow it.
- Do not assume that a GitHub Actions workflow, watchdog, automation, or market-commentary AI has coding-agent permissions. Runtime AI providers are separate from repository coding agents.
- Diagnostic watchdogs may create/update deduplicated issues or reports only where their documented permissions allow; they must not fetch, print, or repurpose private coding tokens.
- Do not assign external coding agents, grant repository access, change repository visibility, or alter organization policy unless the owner explicitly requests that administrative action.
- A public repository may be readable by external services. Repository instructions do not provide confidentiality; repository visibility and access control must be configured in GitHub settings by the owner.
16. Required completion report
For every completed task, provide a concise, evidence-based report containing:
- defect/improvement and proven root cause;
- repository, base branch/SHA, task branch, PR number, and head SHA;
- exact files changed and summary of the diff;
- tests/commands run and exact results;
- workflow links tied to the exact PR head SHA;
- runtime/integration checks performed and their evidence;
- checks not performed and why;
- residual risks and rollback path;
- explicit status: ready for owner review, blocked, or not verified.
Never say “100% operational”, “fixed”, “deployed”, “live”, or “all tests pass” unless the available evidence supports that exact claim. Never claim background work or continuous monitoring unless an authorized automation actually exists and its state has been checked.
Owner approval rule
The owner retains final authority over production and may revoke an agent's task authorization at any time. Code-edit authorization is limited to the specifically assigned task and ends when that task is handed off or withdrawn; it is not a standing grant of production control. The owner personally reviews and performs any merge or deployment. Agents never handle secret values and never place real broker orders. A request to fix a bug authorizes only the scoped branch/PR workflow in section 5.2.


## Mandatory manual merge approval (legacy validation contract)
- Contributors must obtain explicit user approval before any merge.
- All merges require explicit owner approval after diff review, required checks, and applicable runtime validation.


## Mandatory PR conflict-prevention gate
- Before creating or updating any pull request targeting main, fetch the latest main and the exact task-branch head; record both SHAs and inspect the complete diff.
- Bring the task branch up to date with the latest main using a non-destructive merge/rebase workflow on that task branch only. Never force-push, reset, or overwrite another contributor's commits.
- Resolve every content conflict by preserving the current main behavior and the task's independently verified requirement. If intent is ambiguous, stop and ask the owner; never choose a side merely to make GitHub green.
- Do not create a PR, mark it ready, enable auto-merge, or tell the owner it is merge-ready unless GitHub reports mergeable=true and mergeable_state=clean against main, and required checks pass on the exact current head SHA.
- A green Actions/checks indicator does not override mergeable_state=dirty. Treat merge conflicts and CI checks as independent release gates.
- Before starting a task, inspect all open PRs for the same issue and overlapping files. Reuse the existing owner-designated PR when it is demonstrably the same task; otherwise keep separate PRs for distinct defects and sequence shared-file changes to avoid competing edits.
- After every branch update, re-read the branch SHA, PR base/head SHAs, mergeability state, changed-file diff, and check conclusions. If main advances and the PR becomes dirty, stop auto-merge and resolve/retest before requesting owner review.
- Never close or delete a distinct functional fix merely because it conflicts. Close only verified duplicates, superseded proposals, or expired changes, preserving their branches/history unless the owner separately authorizes deletion.
