"""Regression tests for persistent visual animation control and coach button."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceLanguagePreference(unittest.TestCase):
    def test_language_selector_is_removed_but_coach_button_remains(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("align-live-voice", source)
        self.assertNotIn("voixLangueBtn", source)
        self.assertNotIn("Voix FR", source)
        self.assertNotIn("Voix EN", source)

    def test_animation_toggle_remains_independent_and_persisted(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("align-live-animations", source)
        self.assertIn("localStorage.getItem('alignAnimationsEnabled')", source)
        self.assertIn("localStorage.setItem('alignAnimationsEnabled'", source)
        self.assertIn("document.documentElement.classList.toggle('align-animations-off', !animationsActives)", source)


if __name__ == "__main__":
    unittest.main()
