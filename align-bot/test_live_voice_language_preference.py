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
        # v12.2.7 (règle d'Adel) : plus de choix de langue, la voix dit le français PUIS l'anglais.
        self.assertIn("const suiteAnglaise = anglais && maintenant - voixDerniereFR < 60000;", source)
        self.assertIn("if (!anglais) window.speechSynthesis.cancel();", source)
        self.assertIn("utterance.lang = anglais ? 'en-US' : 'fr-FR';", source)
        self.assertIn("🇫🇷 → 🇬🇧 Voix", source)

    def test_voice_never_says_risk_and_prefers_natural_voice(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("\\brisques?\\b|\\brisks?\\b", source)
        self.assertIn("function choisirVoix(lang)", source)
        self.assertIn("if (v) utterance.voice = v;", source)

    def test_animation_toggle_remains_independent_and_persisted(self):
        source = LIVE_JS.read_text(encoding="utf-8")
        self.assertIn("align-live-animations", source)
        self.assertIn("localStorage.getItem('alignAnimationsEnabled')", source)
        self.assertIn("localStorage.setItem('alignAnimationsEnabled'", source)
        self.assertIn("document.documentElement.classList.toggle('align-animations-off', !animationsActives)", source)


if __name__ == "__main__":
    unittest.main()
