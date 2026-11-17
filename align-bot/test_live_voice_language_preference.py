"""Regression tests: removing voice UI must not remove the visual animation switch."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceLanguagePreference(unittest.TestCase):
    def test_commentator_and_voice_language_buttons_are_removed(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        for obsolete in ("ACTIVER LE COMMENTATEUR", "Voix FR", "Voix EN", "align-live-voice"):
            self.assertNotIn(obsolete, source)

    def test_animation_toggle_is_the_only_live_control_retained(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("animationsBtn.id = 'align-live-animations';", source)
        self.assertIn("animationsBtn.addEventListener('click'", source)
        self.assertIn("document.documentElement.classList.toggle('align-animations-off', !animationsActives)", source)
        self.assertIn("animationsBtn.remove()", source)


if __name__ == "__main__":
    unittest.main()
