"""Regression tests for an independent ALIGN live voice language preference."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceLanguagePreference(unittest.TestCase):
    def test_voice_defaults_to_french_and_uses_its_own_language_setting(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("let voixLangue = 'fr';", source)
        start = source.index("function parlerLive(item)")
        end = source.index("let extra = [];", start)
        speech = source[start:end]
        self.assertIn("const anglais = voixLangue === 'en';", speech)
        self.assertIn("if (!!item.en !== anglais) return;", speech)
        self.assertNotIn("langueBande()", speech)

    def test_voice_language_can_be_switched_and_persisted(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("voixLangue = voixLangue === 'fr' ? 'en' : 'fr';", source)
        self.assertIn("localStorage.setItem('alignVoixLangue', voixLangue)", source)
        self.assertIn("🇫🇷 Voix FR", source)
        self.assertIn("🇬🇧 Voix EN", source)

    def test_language_button_is_removed_when_userscript_stops(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("voixLangueBtn.remove()", source)


if __name__ == "__main__":
    unittest.main()
