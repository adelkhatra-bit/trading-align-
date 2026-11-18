import datetime as dt
import os
import unittest
from unittest.mock import call, patch

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


def iso(value):
    return value.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class RecentFailurePaginationTests(unittest.TestCase):
    def test_failure_on_second_page_is_not_hidden_by_coordinator_noise(self):
        now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)

        def stamp(seconds_ago):
            return iso(now - dt.timedelta(seconds=seconds_ago))

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

        with patch.object(
            watchdog,
            "api",
            side_effect=[
                {"total_count": 101, "workflow_runs": page_one},
                {"total_count": 101, "workflow_runs": [missed_bot_failure]},
                {"total_count": 0, "workflow_runs": []},
            ],
        ) as api_mock, patch.object(watchdog, "handle_completed") as handle:
            watchdog.inspect_recent_failures()

        handle.assert_called_once_with(missed_bot_failure)
        requested = [item.args[0] for item in api_mock.call_args_list]
        self.assertTrue(any("branch=main" in url and "page=2" in url and "created=" in url for url in requested))
        self.assertTrue(any("branch=live-data" in url and "page=1" in url and "created=" in url for url in requested))
        self.assertEqual(len(requested), 3)

    def test_splits_saturated_time_window_and_deduplicates_boundary_run(self):
        now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        start = now - dt.timedelta(hours=24)
        midpoint = start + dt.timedelta(hours=12)

        left_failure = workflow_run(
            101,
            watchdog.BOT_WORKFLOW,
            "failure",
            iso(midpoint - dt.timedelta(seconds=1)),
        )
        boundary_failure = workflow_run(
            102,
            watchdog.BOT_WORKFLOW,
            "failure",
            iso(midpoint),
        )
        right_failure = workflow_run(
            103,
            watchdog.BOT_WORKFLOW,
            "timed_out",
            iso(midpoint + dt.timedelta(seconds=1)),
        )

        with patch.object(watchdog, "MAX_RUNS_PER_QUERY", 2), patch.object(
            watchdog,
            "api",
            side_effect=[
                {"total_count": 3, "workflow_runs": []},
                {"total_count": 2, "workflow_runs": [left_failure, boundary_failure]},
                {"total_count": 2, "workflow_runs": [boundary_failure, right_failure]},
                {"total_count": 0, "workflow_runs": []},
            ],
        ) as api_mock, patch.object(watchdog, "handle_completed") as handle:
            watchdog.inspect_recent_failures()

        handle.assert_has_calls(
            [call(left_failure), call(boundary_failure), call(right_failure)],
            any_order=False,
        )
        self.assertEqual(handle.call_count, 3)
        requested = [item.args[0] for item in api_mock.call_args_list]
        self.assertEqual(len(requested), 4)
        self.assertTrue(all("created=" in url for url in requested))
        self.assertTrue(any("branch=live-data" in url for url in requested))

    def test_ignores_a_run_outside_the_24_hour_window(self):
        now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
        old = workflow_run(
            200,
            watchdog.BOT_WORKFLOW,
            "failure",
            iso(now - dt.timedelta(hours=25)),
        )

        with patch.object(
            watchdog,
            "api",
            side_effect=[
                {"total_count": 1, "workflow_runs": [old]},
                {"total_count": 0, "workflow_runs": []},
            ],
        ) as api_mock, patch.object(watchdog, "handle_completed") as handle:
            watchdog.inspect_recent_failures()

        handle.assert_not_called()
        self.assertEqual(api_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
