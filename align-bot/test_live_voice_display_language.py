"""Regression tests for independent ALIGN live speech/display language."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceDisplayLanguage(unittest.TestCase):
    def test_speech_runs_after_the_current_item_is_displayed(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        start = source.index("function suivant() {")
        render = source.index("flash.className =", start)
        show = source.index("bande.classList.add('on')", start)
        speak = source.index("parlerLive(m);", start)
        self.assertLess(render, show)
        self.assertLess(show, speak)

    def test_voice_uses_its_own_selected_language_not_the_display_language(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        start = source.index("function parlerLive(item)")
        end = source.index("let extra = [];", start)
        speech = source[start:end]
        self.assertIn("const anglais = voixLangue === 'en';", speech)
        self.assertIn("if (!!item.en !== anglais) return;", speech)
        self.assertNotIn("langueBande()", speech)


if __name__ == "__main__":
    unittest.main()
