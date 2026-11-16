import unittest
from pathlib import Path


class ProductionMarketCoverageTest(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.workflow = (root / ".github" / "workflows" / "align-bot.yml").read_text(encoding="utf-8")
        self.bot = (Path(__file__).parent / "align_bot.py").read_text(encoding="utf-8")

    def test_nasdaq_is_in_worker_bridge_preflight_and_live_analysis(self):
        self.assertIn('for symbol in ("BTCUSD", "XAUUSD", "NAS100")', self.workflow)
        self.assertIn("Analyse BTC + Gold + NASDAQ et envoi Telegram", self.workflow)
        self.assertIn('report["nasdaq_open_trade"]', self.workflow)
        self.assertIn('report["nasdaq_auto_follow_count"]', self.workflow)
        self.assertIn('"NASDAQ"', self.bot)

    def test_bridge_requires_fresh_m5_m15_h1_h4_daily_and_weekly(self):
        for timeframe in ("M5", "M15", "H1", "H4", "D1", "W1"):
            self.assertIn(f'"{timeframe}"', self.workflow)
        self.assertIn('snapshots absents/périmés', self.workflow)


if __name__ == "__main__":
    unittest.main()
