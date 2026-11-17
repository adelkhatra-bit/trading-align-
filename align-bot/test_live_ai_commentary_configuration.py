"""Production workflow must opt into guarded AI commentary without enabling broker execution."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
WORKFLOW = ROOT.parent / ".github" / "workflows" / "align-bot.yml"


class LiveAiCommentaryConfiguration(unittest.TestCase):
    def test_production_worker_enables_guarded_ai_commentary(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        start = source.index("- name: Analyse BTC + Gold + NASDAQ et envoi Telegram")
        end = source.index("run: exec python3 align_bot.py", start)
        worker = source[start:end]
        self.assertIn('IA_AUTO: "1"', worker)
        self.assertIn('ALIGN_REQUIRE_TV_BRIDGE: "1"', worker)

    def test_real_broker_execution_remains_disabled(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        start = source.index("- name: Analyse BTC + Gold + NASDAQ et envoi Telegram")
        end = source.index("run: exec python3 align_bot.py", start)
        worker = source[start:end]
        self.assertIn('AUTO_TRADE: "0"', worker)
        self.assertIn('TOPSTEP_REEL: "0"', worker)

    def test_commentary_is_limited_to_existing_key_moments(self):
        bot = (ROOT / "align_bot.py").read_text(encoding="utf-8")
        self.assertIn("MOMENTS_IA = (", bot)
        self.assertIn("if not IA_AUTO:", bot)
        self.assertIn("delai", bot)
        self.assertIn("sens_ia_contradictoire(avis, r.get(\"sens\"))", bot)


if __name__ == "__main__":
    unittest.main()
