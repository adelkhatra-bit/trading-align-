import os
import unittest
from unittest.mock import patch

os.environ.setdefault("GITHUB_REPOSITORY", "adelkhatra-bit/trading-align-")
os.environ.setdefault("GITHUB_TOKEN", "test-token")

from scripts import align_workflow_watchdog as watchdog


def run(run_id, workflow="ALIGN Copilot Issue Relay", branch="main"):
    return {
        "id": run_id,
        "name": workflow,
        "head_branch": branch,
        "head_sha": "a" * 40,
        "html_url": f"https://github.com/adelkhatra-bit/trading-align-/actions/runs/{run_id}",
        "run_attempt": 1,
    }


def failed_job(name="relay", step="Verify Copilot credentials only when work is pending"):
    return {
        "name": name,
        "conclusion": "failure",
        "steps": [{"name": step, "conclusion": "failure"}],
    }


def issue(number, body, state="open"):
    return {"number": number, "state": state, "body": body}


class WatchdogBlockerDedupTests(unittest.TestCase):
    def test_same_open_legacy_blocker_suppresses_a_new_run(self):
        legacy = issue(
            498,
            "\n".join([
                "<!-- [align-watchdog:run-44261555540] -->",
                "## ALIGN workflow watchdog report",
                "**Workflow:** ALIGN Copilot Issue Relay",
                "**Branch:** main",
                "### Jobs",
                "- **relay** — failure",
            ]),
        )
        with patch.object(watchdog, "api", side_effect=[[], [legacy]]) as api_mock:
            watchdog.report(
                run(44270000001),
                "Workflow failed or timed out.",
                [failed_job()],
            )

        self.assertEqual(api_mock.call_count, 2)
        self.assertNotEqual(api_mock.call_args_list[-1].kwargs.get("method"), "POST")

    def test_same_blocker_fingerprint_is_stable_across_run_ids(self):
        jobs = [failed_job()]
        first = watchdog.blocker_fingerprint(run(1), jobs)
        second = watchdog.blocker_fingerprint(run(2), jobs)
        self.assertEqual(first, second)

    def test_different_failed_step_has_a_distinct_fingerprint(self):
        first = watchdog.blocker_fingerprint(run(1), [failed_job(step="Verify Copilot credentials")])
        second = watchdog.blocker_fingerprint(run(2), [failed_job(step="Install Copilot CLI")])
        self.assertNotEqual(first, second)

    def test_different_failed_job_creates_a_separate_issue(self):
        existing = issue(
            492,
            "\n".join([
                "<!-- [align-watchdog:run-44249111410] -->",
                "**Workflow:** ALIGN Copilot Issue Relay",
                "**Branch:** main",
                "### Jobs",
                "- **validate** — failure",
            ]),
        )
        with patch.object(watchdog, "api", side_effect=[[], [existing], {"number": 501}]) as api_mock:
            watchdog.report(
                run(44270000002),
                "Workflow failed or timed out.",
                [failed_job()],
            )

        self.assertEqual(api_mock.call_count, 3)
        post = api_mock.call_args_list[-1]
        self.assertEqual(post.kwargs.get("method"), "POST")
        body = post.kwargs["payload"]["body"]
        self.assertIn("<!-- [align-watchdog:blocker-", body)
        self.assertIn("### Failed steps", body)

    def test_closed_legacy_issue_does_not_suppress_a_new_failure(self):
        closed = issue(
            498,
            "\n".join([
                "**Workflow:** ALIGN Copilot Issue Relay",
                "**Branch:** main",
                "### Jobs",
                "- **relay** — failure",
            ]),
            state="closed",
        )
        with patch.object(watchdog, "api", side_effect=[[], [closed], {"number": 502}]) as api_mock:
            watchdog.report(
                run(44270000003),
                "Workflow failed or timed out.",
                [failed_job()],
            )

        self.assertEqual(api_mock.call_args_list[-1].kwargs.get("method"), "POST")


if __name__ == "__main__":
    unittest.main()
