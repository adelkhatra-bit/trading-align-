"""Regression tests for persistent visual animation control and coach button."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceLanguagePreference(unittest.TestCase):
    def test_language_selector_remains_separate_and_coach_button_remains(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("align-live-voice", source)
        self.assertIn("voixLangueBtn", source)
        self.assertIn("localStorage.getItem('alignVoixLangue')", source)
        self.assertIn("localStorage.setItem('alignVoixLangue'", source)
        self.assertIn("if (!!item.en !== anglais) return 0;", source)
        self.assertIn("utterance.lang = anglais ? 'en-US' : 'fr-FR';", source)
        self.assertIn("Voix FR", source)
        self.assertIn("Voix EN", source)

    def test_animation_toggle_remains_independent_and_persisted(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("align-live-animations", source)
        self.assertIn("localStorage.getItem('alignAnimationsEnabled')", source)
        self.assertIn("localStorage.setItem('alignAnimationsEnabled'", source)
        self.assertIn("document.documentElement.classList.toggle('align-animations-off', !animationsActives)", source)


if __name__ == "__main__":
    unittest.main()
