import unittest
from unittest.mock import patch

from scripts import align_copilot_issue_relay as relay


def comment(comment_id, author, body):
    return {"id": comment_id, "user": {"login": author}, "body": body}


class RelayTaskSelectionTests(unittest.TestCase):
    def setUp(self):
        self.task = comment(
            relay.START_COMMENT_ID + 10,
            "adelkhatra-bit",
            "## [CHATGPT → COPILOT][RELAY-TEST-011]\nPlease inspect only.",
        )

    def test_markdown_heading_task_by_owner_is_pending(self):
        pending = relay.pending_tasks([self.task])
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0][1], "RELAY-TEST-011")

    def test_task_by_other_author_is_ignored(self):
        other = comment(
            relay.START_COMMENT_ID + 11,
            "someone-else",
            "[CHATGPT → COPILOT][RELAY-TEST-012]\nIgnore me.",
        )
        self.assertEqual(relay.pending_tasks([other]), [])

    def test_spoofed_reply_marker_from_human_does_not_close_task(self):
        spoof = comment(
            relay.START_COMMENT_ID + 20,
            "someone-else",
            "[COPILOT → CHATGPT][RELAY-TEST-011]",
        )
        pending = relay.pending_tasks([self.task, spoof])
        self.assertEqual([item[1] for item in pending], ["RELAY-TEST-011"])

    def test_actions_bot_reply_after_task_closes_task(self):
        reply = comment(
            relay.START_COMMENT_ID + 20,
            relay.REPLY_AUTHOR,
            "Report complete.\n\n[COPILOT → CHATGPT][RELAY-TEST-011]",
        )
        self.assertEqual(relay.pending_tasks([self.task, reply]), [])

    def test_actions_bot_reply_before_task_does_not_close_new_task(self):
        earlier_reply = comment(
            relay.START_COMMENT_ID + 5,
            relay.REPLY_AUTHOR,
            "[COPILOT → CHATGPT][RELAY-TEST-011]",
        )
        self.assertEqual(
            [item[1] for item in relay.pending_tasks([earlier_reply, self.task])],
            ["RELAY-TEST-011"],
        )

    def test_task_before_activation_marker_is_ignored(self):
        old = comment(
            relay.START_COMMENT_ID - 1,
            "adelkhatra-bit",
            "[CHATGPT → COPILOT][RELAY-TEST-013]",
        )
        self.assertEqual(relay.pending_tasks([old]), [])

    def test_only_exact_standalone_reply_marker_is_recognized(self):
        inline = comment(
            relay.START_COMMENT_ID + 20,
            relay.REPLY_AUTHOR,
            "Quoted marker: [COPILOT → CHATGPT][RELAY-TEST-011]",
        )
        self.assertEqual(
            [item[1] for item in relay.pending_tasks([self.task, inline])],
            ["RELAY-TEST-011"],
        )


class RelayPaginationTests(unittest.TestCase):
    def test_fetch_all_comments_reads_every_page(self):
        first_page = [{"id": i} for i in range(100)]
        second_page = [{"id": 101}]
        with patch.object(relay, "request_json", side_effect=[first_page, second_page]) as request:
            comments = relay.fetch_all_comments()
        self.assertEqual(len(comments), 101)
        self.assertEqual(request.call_count, 2)
        self.assertIn("page=1", request.call_args_list[0].args[0])
        self.assertIn("page=2", request.call_args_list[1].args[0])


class RelayScopeTests(unittest.TestCase):
    def test_scope_rejects_other_repository(self):
        with patch.object(relay, "REPO", "another/repository"), patch.object(
            relay, "ISSUE", relay.EXPECTED_ISSUE
        ), patch.object(relay, "GH_TOKEN", "test-token"):
            with self.assertRaisesRegex(RuntimeError, "scope mismatch"):
                relay.validate_scope()

    def test_scope_rejects_other_issue(self):
        with patch.object(relay, "REPO", relay.EXPECTED_REPO), patch.object(
            relay, "ISSUE", 432
        ), patch.object(relay, "GH_TOKEN", "test-token"):
            with self.assertRaisesRegex(RuntimeError, "scope mismatch"):
                relay.validate_scope()


if __name__ == "__main__":
    unittest.main()
