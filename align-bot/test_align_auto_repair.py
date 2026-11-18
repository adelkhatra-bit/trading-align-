import unittest
from unittest.mock import patch
from scripts import align_auto_repair as repair
from scripts.align_auto_repair import (
    event_target, find_issue_for_sha, next_attempt, repair_issue_body,
    summarize_failed_jobs,
)

SHA = "1" * 40


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
        issue = {"number": 9, "body": f"report <!-- ALIGN_REPAIR_SHA={SHA} -->"}
        self.assertEqual(find_issue_for_sha([issue], SHA), issue)
        self.assertIsNone(find_issue_for_sha([issue], "2" * 40))

    def test_attempt_counter_starts_at_one_and_increments(self):
        issue = {"body": "<!-- ALIGN_REPAIR_ATTEMPT=1 -->"}
        comments = [{"body": "<!-- ALIGN_REPAIR_ATTEMPT=2 -->"}]
        self.assertEqual(next_attempt(issue, comments), 3)

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

    def test_failed_job_summary_lists_failed_steps_only(self):
        summary = summarize_failed_jobs({"jobs": [
            {"name": "test", "conclusion": "failure", "steps": [
                {"name": "setup", "conclusion": "success"},
                {"name": "MTF regression", "conclusion": "failure"},
            ]},
            {"name": "lint", "conclusion": "success", "steps": []},
        ]})
        self.assertIn("MTF regression", summary)
        self.assertNotIn("setup", summary)
        self.assertNotIn("lint", summary)


class CopilotAssignmentGateTests(unittest.TestCase):
    def test_no_user_token_keeps_assignment_manual(self):
        with patch.object(repair, "COPILOT_TOKEN", ""), patch.object(repair, "request_graphql") as query:
            self.assertFalse(repair.assign_copilot_if_available(77, []))
            query.assert_not_called()

    def test_active_copilot_issue_blocks_parallel_assignment(self):
        active = [{"state": "open", "assignees": [{"login": "copilot-swe-agent[bot]"}]}]
        with patch.object(repair, "COPILOT_TOKEN", "user-token"), patch.object(repair, "request_graphql") as query:
            self.assertFalse(repair.assign_copilot_if_available(77, active))
            query.assert_not_called()

    def test_cloud_agent_assignment_uses_user_token_only_after_actor_check(self):
        actors = {"data": {"repository": {"suggestedActors": {"nodes": [{"login": "copilot-swe-agent"}]}}}}
        with patch.object(repair, "COPILOT_TOKEN", "user-token"), \\
             patch.object(repair, "request_graphql", return_value=actors), \\
             patch.object(repair, "request_json", return_value={}) as request:
            self.assertTrue(repair.assign_copilot_if_available(77, []))
        args = request.call_args
        self.assertEqual(args.args[0], "/repos/adelkhatra-bit/trading-align-/issues/77/assignees")
        self.assertEqual(args.kwargs["token"], "user-token")
        self.assertEqual(args.kwargs["payload"]["assignees"], ["copilot-swe-agent[bot]"])
        self.assertEqual(args.kwargs["payload"]["agent_assignment"]["base_branch"], "main")


if __name__ == "__main__":
    unittest.main()
