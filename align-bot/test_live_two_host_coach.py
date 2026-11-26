"""Regression tests for the two-host live coach and its TradingView sync protocol."""
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"
OVERLAY = ROOT.parent / "docs" / "live" / "index.html"


class LiveTwoHostCoach(unittest.TestCase):
    def setUp(self):
        self.userscript = LIVE_JS.read_text(encoding="utf-8")
        self.overlay = OVERLAY.read_text(encoding="utf-8")

    def test_chart_voice_selects_distinct_speakers_for_french_and_english(self):
        self.assertIn("const speaker = anglais ? 'l' : 't'", self.userscript)
        self.assertIn("function choisirVoix(lang, speaker)", self.userscript)
        self.assertIn("paul", self.userscript.lower())
        self.assertIn("hortense", self.userscript.lower())
        self.assertIn("david", self.userscript.lower())
        self.assertIn("zira", self.userscript.lower())
        self.assertIn("utterance.voice = v;", self.userscript)

    def test_coach_toggle_controls_two_host_overlay_and_chart_speaker_id(self):
        self.assertIn("signalVoix('COACH_ON', 'fr')", self.userscript)
        self.assertIn("signalVoix('COACH_OFF', 'fr')", self.userscript)
        self.assertIn("function signalVoix(action, lang, speaker)", self.userscript)
        self.assertIn("(speaker || '')", self.userscript)
        self.assertIn("parts[1] === 'COACH_ON'", self.overlay)
        self.assertIn("parts[1] === 'COACH_OFF'", self.overlay)
        self.assertIn("parts[4] === 't' || parts[4] === 'l'", self.overlay)

    def test_thomas_and_leila_speak_only_when_coach_is_enabled(self):
        self.assertIn("function choisirVoixHote(qui)", self.overlay)
        self.assertIn("function direDialogue(qui, texte)", self.overlay)
        self.assertIn("if (!coachActif || voixSourceChartActive", self.overlay)
        self.assertIn("window.speechSynthesis.speak(utterance)", self.overlay)
        self.assertIn("voixSourceChartActive = true", self.overlay)
        self.assertIn("annulerVoixDialogue()", self.overlay)

    def test_existing_hosts_dialogues_and_animation_design_are_preserved(self):
        for fragment in (
            'id="av-t"', 'id="av-l"', 'id="b-t"', 'id="b-l"',
            "<span>Thomas</span>", "<span>Leïla</span>",
            "@keyframes flotte", "@keyframes cligne", "@keyframes parle",
            "var DIALOGUES = {", "function echange()", "setInterval(echange, 11000)",
        ):
            self.assertIn(fragment, self.overlay)

    def test_overlay_inline_javascript_passes_node_syntax_check(self):
        scripts = re.findall(r"<script>(.*?)</script>", self.overlay, flags=re.S)
        self.assertEqual(len(scripts), 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "overlay.js"
            path.write_text(scripts[0], encoding="utf-8")
            result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
