"""Regression tests for ALIGN live speech/display language synchronization."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceDisplayLanguage(unittest.TestCase):
    def test_speech_runs_after_the_current_item_language_is_displayed(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("const anglais = voixLangue === 'en';", source)
        self.assertIn("if (!!item.en !== anglais) return;", source)
        start = source.index("function suivant() {")
        render = source.index("flash.className =", start)
        show = source.index("bande.classList.add('on')", start)
        speak = source.index("parlerLive(m);", start)
        self.assertLess(render, show)
        self.assertLess(show, speak)

    def test_voice_stays_locked_to_the_language_currently_shown(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("const anglais = voixLangue === 'en';", source)
        self.assertIn("if (!!item.en !== anglais) return;", source)


if __name__ == "__main__":
    unittest.main()
