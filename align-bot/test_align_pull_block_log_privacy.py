"""Prevent public Actions logs from exposing Telegram chat identifiers."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parent / "align_bot.py").read_text(encoding="utf-8")


class PullBlockLogPrivacyTests(unittest.TestCase):
    def test_pull_block_log_redacts_chat_identifier(self):
        block = SOURCE.split("def _telegram_sortant_autorise", 1)[1].split("def chaine_silencieuse", 1)[0]
        self.assertIn("chat_id_present=", block)
        self.assertNotIn("chat={cid or", block)


if __name__ == "__main__":
    unittest.main()
