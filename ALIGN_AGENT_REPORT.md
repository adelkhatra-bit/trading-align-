# ALIGN_AGENT_REPORT — AUTO-REPAIR-011

Date: 2026-11-18  
Repository: `adelkhatra-bit/trading-align-`  
Base branch: `main`  
Base SHA audited before changes: `1f9a7d0b6b73fb1384c547c811d97bc1511e1403`

## Mission scope

- Reuse the existing Copilot relay PR #436; do not add another watchdog.
- Keep repair coordination serialized and issue creation deduplicated by exact failing SHA.
- Cap repair attempts at two per SHA.
- Copilot cloud-agent assignment remains manual by default.
- No merge, deployment, Pine, indicator design, animations, signal logic, broker action, or `live-data/live.json` changes.

## Existing evidence

- Main SHA: `1f9a7d0b6b73fb1384c547c811d97bc1511e1403`.
- Existing relay PR #436 head: `cdefffa47f52fbe31af198d226efe2600e6bc1f1`; it already contains one relay with a ten-minute fallback schedule and a serialized concurrency group.
- Relay PR validation run: `44209552218` — success.
- Relay PR integration run: `44209552602` — success.
- The relay's prior regression evidence: 863 tests, zero failures.
- Production bot failure run: `44205828646` on main SHA above; the Telegram API and Groq checks passed, then the bridge preflight failed because the required bridge secrets were absent. This is recorded as evidence, not a reason to bypass the live-data guard.

## Proposed coordinator behavior in this PR

- A single `workflow_run` coordinator listens to the existing validation, integration, and production bot workflows.
- Failed PRs are filtered by their associated PR number; #401, #448 and #451 are excluded.
- Unlinked failures are processed only on `main`.
- One repair issue is created per exact 40-character SHA, with the workflow run, URL, and failed job/step summary.
- Repeated failures on the same SHA update the existing issue, with a maximum of two recorded attempts.
- GitHub Actions concurrency serializes the coordinator, preventing simultaneous agent handoffs.
- Agent assignment is deliberately not automated. A human reviews the report and assigns Copilot cloud agent manually.
- No Copilot token value is read, printed, or changed by this coordinator.

## Verification plan

1. Python syntax compile for the coordinator and tests.
2. Targeted unit tests for failure filtering, excluded PRs, SHA deduplication, attempt cap metadata, and failure-step summaries.
3. actionlint for the new workflow and the existing validation workflow.
4. Full ALIGN MTF regression suite through the existing CI.
5. Inspect the PR diff and GitHub run results before any merge decision.

## Current limitations

- The coordinator becomes active only after PR #436 is merged by a human.
- A real failure-to-issue round trip is not claimed until a GitHub Actions run proves it.
- Automatic Copilot assignment is not enabled; it remains a manual human action.
- This PR does not fix the currently missing TradingView bridge configuration and does not declare Telegram signals restored.
