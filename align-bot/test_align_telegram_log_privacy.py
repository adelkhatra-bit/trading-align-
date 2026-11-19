"""Regression tests for Telegram recipient-ID redaction in public logs."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).with_name("align_bot.py")


def _contains_direct_recipient_id(node):
    forbidden = {"cid", "chat_id"}
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "bool":
        if len(node.args) == 1 and isinstance(node.args[0], ast.Name) and node.args[0].id in forbidden:
            return False  # Presence-only boolean is safe.
    if isinstance(node, ast.Name) and node.id in forbidden:
        return True
    return any(_contains_direct_recipient_id(child) for child in ast.iter_child_nodes(node))


class TelegramLogPrivacyTests(unittest.TestCase):
    def test_print_calls_do_not_include_chat_identifiers(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
                if any(_contains_direct_recipient_id(arg) for arg in node.args):
                    offenders.append(ast.unparse(node))
        self.assertEqual([], offenders, "Console logs must not expose Telegram recipient IDs")

    def test_pull_and_delivery_failure_logs_are_presence_only(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("TELEGRAM_PULL_BLOCK method={methode} chat_id_present={bool(cid)}", source)
        self.assertIn("ANALYSE_NON_LIVREE market={m} chat_id_present={bool(cid)}", source)
        self.assertIn("TELEGRAM_OUTBOX_QUEUED chat_id_present={bool(cid)}", source)

if __name__ == "__main__":
    unittest.main()
