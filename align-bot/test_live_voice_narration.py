"""Regression : la narration de marché affichée sur la bande doit être lue à voix haute (v12.2.9)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceNarration(unittest.TestCase):
    def setUp(self):
        self.source = LIVE_JS.read_text(encoding="utf-8")

    def test_voice_accepts_market_narration_source(self):
        self.assertIn("item.source !== 'ia' && item.source !== 'marche'", self.source)

    def test_bandeshow_forwards_source_to_montrer(self):
        self.assertIn("function bandeShow(txt, source)", self.source)
        self.assertIn("montrer(txt, false, 1, undefined, false, source)", self.source)

    def test_narration_branch_is_tagged_as_spoken_market_source(self):
        self.assertIn("const parleNarration = L.length === 1 && L[0] === narration;", self.source)
        self.assertIn("parleNarration ? 'marche' : undefined", self.source)

    def test_ai_comments_still_spoken(self):
        self.assertIn("montrer('🧠 ' + phrase, false, 2, 'membre', false, 'ia');", self.source)


if __name__ == "__main__":
    unittest.main()
