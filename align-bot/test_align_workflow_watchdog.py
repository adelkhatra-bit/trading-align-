import datetime as dt
import os
import unittest
from unittest.mock import patch

# The watchdog reads these at import time; the test replaces all network calls.
os.environ.setdefault("GITHUB_REPOSITORY", "adelkhatra-bit/trading-align-")
os.environ.setdefault("GITHUB_TOKEN", "test-token")

from scripts import align_workflow_watchdog as watchdog


def workflow_run(run_id, name, conclusion, created_at):
    return {
        "id": run_id,
        "name": name,
        "conclusion": conclusion,
        "created_at": created_at,
        "head_branch": "main",
        "head_sha": "a" * 40,
        "html_url": f"https://github.com/adelkhatra-bit/trading-align-/actions/runs/{run_id}",
        "run_attempt": 1,
    }


class RecentFailurePaginationTests(unittest.TestCase):
    def test_failure_on_second_page_is_not_hidden_by_coordinator_noise(self):
        now = dt.datetime.now(dt.timezone.utc)

        def stamp(seconds_ago):
            return (now - dt.timedelta(seconds=seconds_ago)).isoformat().replace("+00:00", "Z")

        # The first page is full of recent coordinator events. The production BOT
        # failure is on page 2, as happened for run 44222373864 on 2026-11-18.
        page_one = [
            workflow_run(5000 - i, "ALIGN Auto Repair Coordinator", "skipped", stamp(i * 10))
            for i in range(100)
        ]
        missed_bot_failure = workflow_run(
            44222373864,
            watchdog.BOT_WORKFLOW,
            "failure",
            stamp(6000),
        )
        older_failure = workflow_run(100, watchdog.BOT_WORKFLOW, "failure", stamp(25 * 3600))

        with patch.object(
            watchdog,
            "api",
            side_effect=[
                {"workflow_runs": page_one},
                {"workflow_runs": [missed_bot_failure, older_failure]},
                {"workflow_runs": []},
            ],
        ) as api_mock, patch.object(watchdog, "handle_completed") as handle:
            watchdog.inspect_recent_failures()

        handle.assert_called_once_with(missed_bot_failure)
        requested = [call.args[0] for call in api_mock.call_args_list]
        self.assertTrue(any("branch=main" in url and "page=2" in url for url in requested))
        self.assertTrue(any("branch=live-data" in url and "page=1" in url for url in requested))
        self.assertEqual(len(requested), 3)

    def test_stops_paging_after_crossing_the_24_hour_cutoff(self):
        now = dt.datetime.now(dt.timezone.utc)
        recent = (now - dt.timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
        old = (now - dt.timedelta(hours=25)).isoformat().replace("+00:00", "Z")

        page = [
            workflow_run(1, "ALIGN Workflow Watchdog", "success", recent),
            workflow_run(2, watchdog.BOT_WORKFLOW, "failure", old),
        ]
        with patch.object(
            watchdog,
            "api",
            side_effect=[{"workflow_runs": page}, {"workflow_runs": []}],
        ) as api_mock, patch.object(watchdog, "handle_completed") as handle:
            watchdog.inspect_recent_failures()

        handle.assert_not_called()
        self.assertEqual(api_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
