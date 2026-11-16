"""Regression tests for ALIGN live speech language selection."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceLanguage(unittest.TestCase):
    def test_speech_uses_the_queued_item_language(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("const anglais = !!item.en;", source)
        self.assertNotIn("if (!!item.en !== anglais) return;", source)
        self.assertNotIn("const anglais = langueBande() === 'en';", source)


if __name__ == "__main__":
    unittest.main()
