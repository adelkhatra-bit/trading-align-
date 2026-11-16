"""Regression tests for independent voice language preference."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoicePreference(unittest.TestCase):
    def test_voice_defaults_to_french_and_has_an_explicit_language_control(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("let voixLangue = 'fr';", source)
        self.assertIn("voixLangBtn.textContent = voixLangue === 'fr' ? '🇫🇷 FR' : '🇬🇧 EN';", source)
        self.assertIn("const anglais = voixLangue === 'en';", source)
        self.assertNotIn("const anglais = langueBande() === 'en';", source)

    def test_voice_language_control_is_removed_when_overlay_stops(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("voixBtn.remove(); voixLangBtn.remove();", source)


if __name__ == "__main__":
    unittest.main()
