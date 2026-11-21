import unittest
from unittest.mock import patch
from scripts import align_auto_repair as repair
from scripts.align_auto_repair import (
    event_target, find_issue_for_sha, has_run_marker, next_attempt, repair_issue_body,
    summarize_failed_jobs,
)

import importlib
import os

with patch.dict(os.environ, {
    "GITHUB_REPOSITORY": "adelkhatra-bit/trading-align-",
    "GITHUB_TOKEN": "test-token",
}):
    watchdog = importlib.import_module("scripts.align_workflow_watchdog")

SHA = "1" * 40
BOT = {"login": "github-actions[bot]"}
USER = {"login": "adelkhatra-bit"}


class RepairEventTests(unittest.TestCase):
    def run_event(self, *, conclusion="failure", branch="feature/test", prs=None):
        return {"workflow_run": {
            "conclusion": conclusion, "head_sha": SHA, "head_branch": branch,
            "pull_requests": prs or [], "id": 123, "name": "ALIGN MTF validation",
            "html_url": "https://github.com/adelkhatra-bit/trading-align-/actions/runs/123",
        }}

    def test_failed_main_run_is_eligible(self):
        self.assertEqual(event_target(self.run_event(branch="main"))["sha"], SHA)

    def test_failed_pull_request_run_is_eligible(self):
        self.assertEqual(event_target(self.run_event(prs=[{"number": 500}]))["pr_numbers"], [500])

    def test_timed_out_main_run_is_eligible(self):
        self.assertEqual(event_target(self.run_event(conclusion="timed_out", branch="main"))["sha"], SHA)

    def test_non_failure_is_ignored(self):
        self.assertIsNone(event_target(self.run_event(conclusion="success", branch="main")))

    def test_non_main_unlinked_run_is_ignored(self):
        self.assertIsNone(event_target(self.run_event(branch="feature/unlinked")))

    def test_protected_prs_are_ignored(self):
        for number in (401, 448, 451):
            self.assertIsNone(event_target(self.run_event(prs=[{"number": number}])))

    def test_invalid_sha_is_ignored(self):
        event = self.run_event(branch="main")
        event["workflow_run"]["head_sha"] = "bad"
        self.assertIsNone(event_target(event))


class RepairIssueTests(unittest.TestCase):
    def test_deduplicates_by_exact_sha_marker(self):
        issue = {"number": 9, "user": BOT, "body": f"report <!-- ALIGN_REPAIR_SHA={SHA} -->"}
        self.assertEqual(find_issue_for_sha([issue], SHA), issue)
        self.assertIsNone(find_issue_for_sha([issue], "2" * 40))

    def test_user_authored_sha_marker_cannot_suppress_repair(self):
        issue = {"number": 10, "user": USER, "body": f"<!-- ALIGN_REPAIR_SHA={SHA} -->"}
        self.assertIsNone(find_issue_for_sha([issue], SHA))

    def test_attempt_counter_starts_at_one_and_increments(self):
        issue = {"user": BOT, "body": "<!-- ALIGN_REPAIR_ATTEMPT=1 -->"}
        comments = [{"user": BOT, "body": "<!-- ALIGN_REPAIR_ATTEMPT=2 -->"}]
        self.assertEqual(next_attempt(issue, comments), 3)

    def test_user_comment_cannot_inflate_attempt_counter(self):
        issue = {"user": BOT, "body": "<!-- ALIGN_REPAIR_ATTEMPT=1 -->"}
        comments = [
            {"user": USER, "body": "<!-- ALIGN_REPAIR_ATTEMPT=99 -->"},
            {"user": BOT, "body": "<!-- ALIGN_REPAIR_ATTEMPT=2 -->"},
        ]
        self.assertEqual(next_attempt(issue, comments), 3)

    def test_only_bot_run_marker_deduplicates(self):
        marker = "<!-- ALIGN_REPAIR_RUN=123 -->"
        issue = {"user": BOT, "body": ""}
        self.assertFalse(has_run_marker(issue, [{"user": USER, "body": marker}], marker))
        self.assertTrue(has_run_marker(issue, [{"user": BOT, "body": marker}], marker))


    def test_finds_open_watchdog_issue_for_same_sha(self):
        target = {"sha": SHA, "run_id": 123}
        issue = {
            "number": 8, "state": "open", "user": BOT,
            "body": f"<!-- [align-watchdog:run-123] -->\n**Commit:** {SHA}",
        }
        self.assertEqual(repair.find_watchdog_issue_for_target([issue], target), issue)

    def test_does_not_reuse_user_authored_closed_or_wrong_sha_watchdog_issue(self):
        target = {"sha": SHA, "run_id": 123}
        body = f"<!-- [align-watchdog:run-123] -->\n**Commit:** {SHA}"
        candidates = [
            {"number": 1, "state": "open", "user": USER, "body": body},
            {"number": 2, "state": "closed", "user": BOT, "body": body},
            {"number": 3, "state": "open", "user": BOT, "body": body.replace(SHA, "2" * 40)},
        ]
        self.assertIsNone(repair.find_watchdog_issue_for_target(candidates, target))

    def test_annotating_watchdog_issue_is_preserving_and_idempotent(self):
        target = {"sha": SHA, "run_id": 123}
        original = "## Watchdog report\nExisting evidence."
        tagged = repair.annotate_watchdog_issue_body(original, target, 1)
        self.assertTrue(tagged.startswith(original))
        self.assertIn(f"<!-- ALIGN_REPAIR_SHA={SHA} -->", tagged)
        self.assertIn("<!-- ALIGN_REPAIR_ATTEMPT=1 -->", tagged)
        self.assertIn("<!-- ALIGN_REPAIR_RUN=123 -->", tagged)
        self.assertEqual(repair.annotate_watchdog_issue_body(tagged, target, 1), tagged)


    def test_issue_body_contains_evidence_and_guardrails(self):
        target = {
            "sha": SHA, "head_branch": "main", "pr_numbers": [],
            "run_id": 123, "run_name": "ALIGN MTF validation",
            "run_url": "https://github.com/run/123",
        }
        body = repair_issue_body(target, "- pytest failed", 1)
        self.assertIn(SHA, body)
        self.assertIn("123", body)
        self.assertIn("pytest failed", body)
        self.assertIn("live-data/live.json", body)
        self.assertIn("1/2", body)

    def test_timed_out_job_and_step_are_included(self):
        summary = summarize_failed_jobs({"jobs": [{"name": "timed", "conclusion": "timed_out", "steps": [
            {"name": "stalled", "conclusion": "timed_out"},
        ]}]})
        self.assertIn("timed", summary)
        self.assertIn("stalled", summary)

    def test_failed_job_summary_lists_failed_steps_only_and_links_job_logs(self):
        summary = summarize_failed_jobs({"jobs": [
            {"name": "test", "conclusion": "failure", "html_url": "https://github.com/adelkhatra-bit/trading-align-/actions/runs/1/job/2", "steps": [
                {"name": "setup", "conclusion": "success"},
                {"name": "MTF regression", "conclusion": "failure"},
            ]},
            {"name": "lint", "conclusion": "success", "steps": []},
        ]})
        self.assertIn("MTF regression", summary)
        self.assertIn("https://github.com/adelkhatra-bit/trading-align-/actions/runs/1/job/2", summary)
        self.assertNotIn("setup", summary)
        self.assertNotIn("lint", summary)

    def test_untrusted_non_github_job_url_is_not_linked(self):
        summary = summarize_failed_jobs({"jobs": [
            {"name": "test", "conclusion": "failure", "html_url": "https://evil.invalid/logs", "steps": []},
        ]})
        self.assertNotIn("evil.invalid", summary)



class WatchdogRepairCoordinationTests(unittest.TestCase):
    def make_run(self, *, name="ALIGN MTF validation", branch="main", prs=None, created_at="2026-11-20T10:00:00Z", conclusion="failure"):
        return {
            "name": name,
            "conclusion": conclusion,
            "head_sha": SHA,
            "head_branch": branch,
            "pull_requests": prs or [],
            "created_at": created_at,
        }

    def test_repair_coordinator_owns_main_and_linked_pr_failures(self):
        self.assertTrue(watchdog.repair_coordinator_owns_failure(self.make_run(branch="main")))
        self.assertTrue(watchdog.repair_coordinator_owns_failure(self.make_run(
            branch="fix/test", prs=[{"number": 627}],
        )))

    def test_repair_coordinator_does_not_own_ignored_or_unlinked_pr_failures(self):
        self.assertFalse(watchdog.repair_coordinator_owns_failure(self.make_run(
            branch="fix/test", prs=[{"number": 401}],
        )))
        self.assertFalse(watchdog.repair_coordinator_owns_failure(self.make_run(branch="fix/unlinked")))
        self.assertFalse(watchdog.repair_coordinator_owns_failure(self.make_run(
            branch="main", conclusion="success",
        )))
        self.assertFalse(watchdog.repair_coordinator_owns_failure(self.make_run(
            name="pages build and deployment",
        )))

    def test_watchdog_defers_event_failure_to_repair_coordinator(self):
        run = self.make_run(created_at="2026-11-20T13:59:00Z")
        self.assertTrue(watchdog.defer_to_repair_coordinator(
            run, repair_issue_found=False, event_name="workflow_run",
        ))

    def test_watchdog_defers_when_repair_issue_already_exists(self):
        run = self.make_run(created_at="2026-11-20T10:00:00Z")
        self.assertTrue(watchdog.defer_to_repair_coordinator(
            run, repair_issue_found=True, event_name="schedule",
        ))

    def test_safe_transient_validation_retry_runs_before_report_deferral(self):
        run = self.make_run(branch="main")
        run.update({"id": 123, "run_attempt": 1})
        with patch.object(watchdog, "EVENT_NAME", "workflow_run"):
            with patch.object(watchdog, "failed_jobs", return_value=[{"id": 1}]):
                with patch.object(watchdog, "transient_failure", return_value=True):
                    with patch.object(watchdog, "api") as api:
                        with patch.object(watchdog, "report") as report:
                            watchdog.handle_completed(run)
        api.assert_called_once_with(
            f"/repos/{watchdog.REPO}/actions/runs/123/rerun-failed-jobs",
            method="POST",
        )
        report.assert_not_called()

    def test_schedule_grace_period_backstops_missing_repair_issue(self):
        run = self.make_run(created_at="2026-11-20T13:55:00Z")
        before_grace = watchdog.dt.datetime.fromisoformat("2026-11-20T14:00:00+00:00")
        after_grace = watchdog.dt.datetime.fromisoformat("2026-11-20T14:11:00+00:00")
        self.assertTrue(watchdog.defer_to_repair_coordinator(
            run, event_name="schedule", now=before_grace,
        ))
        self.assertFalse(watchdog.defer_to_repair_coordinator(
            run, event_name="schedule", now=after_grace,
        ))


if __name__ == "__main__":
    unittest.main()
