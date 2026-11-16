"""Regression tests for ALIGN live speech/display language synchronization."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"


class LiveVoiceDisplayLanguage(unittest.TestCase):
    def test_speech_runs_after_the_current_item_language_is_displayed(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("const anglais = langueBande() === 'en';", source)
        self.assertIn("if (!!item.en !== anglais) return;", source)
        queue = source[source.index("function suivant() {"):source.index("let extra = [];")]
        self.assertLess(queue.index("flash.className ="), queue.index("bande.classList.add('on')"))
        self.assertLess(queue.index("bande.classList.add('on')"), queue.index("parlerLive(m);"))

    def test_voice_stays_locked_to_the_language_currently_shown(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("const anglais = langueBande() === 'en';", source)
        self.assertIn("if (!!item.en !== anglais) return;", source)


if __name__ == "__main__":
    unittest.main()
