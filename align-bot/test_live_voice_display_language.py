"""Regression tests for the bottom-positioned ALIGN live controls."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceDisplayLanguage(unittest.TestCase):
    def test_voice_and_animation_controls_are_positioned_at_chart_bottom(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("id = 'align-live-voice'", source)
        self.assertIn("left:18px;bottom:22px", source)
        self.assertIn("id = 'align-live-animations'", source)
        self.assertIn("left:18px;bottom:72px", source)

    def test_voice_is_optional_and_reads_french_live_comments(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("function parlerLive(item)", source)
        self.assertIn("if (!voixActive || !item", source)
        self.assertIn("parlerLive(m);", source)
        self.assertIn("window.speechSynthesis.speak(utterance)", source)


if __name__ == "__main__":
    unittest.main()
