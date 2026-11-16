"""Regression tests for independent ALIGN live voice language."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceDisplayLanguage(unittest.TestCase):
    def test_speech_uses_the_independent_voice_language_preference(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        start = source.index("function parlerLive(item)")
        end = source.index("let extra = [];", start)
        speech = source[start:end]
        self.assertIn("const anglais = voixLangue === 'en';", speech)
        self.assertIn("if (!!item.en !== anglais) return;", speech)
        self.assertNotIn("langueBande()", speech)

    def test_voice_language_switch_does_not_change_the_bilingual_display(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("const anglais = voixLangue === 'en';", source)
        self.assertIn("langueBande()", source)


if __name__ == "__main__":
    unittest.main()
