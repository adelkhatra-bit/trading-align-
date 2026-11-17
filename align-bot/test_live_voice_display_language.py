"""Regression tests: visual animation control remains independent and voice UI is absent."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceDisplayLanguage(unittest.TestCase):
    def test_voice_controls_and_speech_synthesis_are_absent(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        for obsolete in ("align-live-voice", "voixLangueBtn", "speechSynthesis", "parlerLive"):
            self.assertNotIn(obsolete, source)

    def test_animation_toggle_remains_present_and_persisted(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("align-live-animations", source)
        self.assertIn("localStorage.getItem('alignAnimationsEnabled')", source)
        self.assertIn("localStorage.setItem('alignAnimationsEnabled'", source)
        self.assertIn("appliquerAnimations();", source)


if __name__ == "__main__":
    unittest.main()
