import unittest
from pathlib import Path


class ProductionMarketCoverageTest(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.workflow = (root / ".github" / "workflows" / "align-bot.yml").read_text(encoding="utf-8")
        self.rollover = (root / ".github" / "workflows" / "align-bot-rollover.yml").read_text(encoding="utf-8")
        self.bot = (Path(__file__).parent / "align_bot.py").read_text(encoding="utf-8")

    def test_nasdaq_is_in_worker_bridge_preflight_and_live_analysis(self):
        self.assertIn('for symbol in ("BTCUSD", "XAUUSD", "NAS100")', self.workflow)
        self.assertIn("Analyse BTC + Gold + NASDAQ et envoi Telegram", self.workflow)
        self.assertIn('report["nasdaq_open_trade"]', self.workflow)
        self.assertIn('report["nasdaq_auto_follow_count"]', self.workflow)
        self.assertIn('"NASDAQ"', self.bot)

    def test_bridge_preflight_sets_success_and_failure_outputs_explicitly(self):
        bridge = self.workflow.split("id: bridge", 1)[1].split("- name: Analyse", 1)[0]
        self.assertNotIn("python3 - <<'PY' || {", bridge)
        self.assertIn("if python3 -<<'PY'", bridge)
        self.assertIn('echo "ALIGN_TV_BRIDGE_PRET=1" >> "$GITHUB_OUTPUT"', bridge)
        self.assertIn('echo "ALIGN_TV_BRIDGE_PRET=0" >> "$GITHUB_OUTPUT"', bridge)
        self.assertIn("\\n          then\\n            echo \\"ALIGN_TV_BRIDGE_PRET=1\\"".replace("\\n","\n"), bridge)
        self.assertIn("\\n          else\\n            echo \\"ALIGN_TV_BRIDGE_PRET=0\\"".replace("\\n","\n"), bridge)

    def test_worker_rollover_recognizes_both_legacy_and_renamed_worker(self):
        self.assertIn("if run.get(\"name\") in {", self.rollover)
        self.assertIn("ALIGN MTF BOT (signaux BTC + Gold Telegram)", self.rollover)
        self.assertIn("ALIGN MTF BOT (signaux BTC + Gold + NASDAQ Telegram)", self.rollover)

    def test_bridge_requires_fresh_m5_m15_h1_h4_daily_and_weekly(self):
        for timeframe in ("M5", "M15", "H1", "H4", "D1", "W1"):
            self.assertIn(f'"{timeframe}"', self.workflow)
        self.assertIn("snapshots TradingView absents/périmés", self.workflow)


if __name__ == "__main__":
    unittest.main()
