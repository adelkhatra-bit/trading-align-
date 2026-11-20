import unittest
from pathlib import Path


class ProductionMarketCoverageTest(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.workflow = (root / ".github" / "workflows" / "align-bot.yml").read_text(encoding="utf-8")
        self.rollover = (root / ".github" / "workflows" / "align-bot-rollover.yml").read_text(encoding="utf-8")
        self.bot = (Path(__file__).parent / "align_bot.py").read_text(encoding="utf-8")

    def test_worker_operational_scope_is_btc_and_gold_only(self):
        self.assertIn('for symbol in ("BTCUSD", "XAUUSD")', self.workflow)
        self.assertIn("Analyse BTC + Gold et envoi Telegram", self.workflow)
        self.assertNotIn("NAS100", self.workflow)
        self.assertNotIn('report["nasdaq_open_trade"]', self.workflow)
        self.assertNotIn('report["nasdaq_auto_follow_count"]', self.workflow)
        self.assertIn('MARCHES = {"BTC": "XBTUSD", "GOLD": "XAUUSD"}', self.bot)
        self.assertIn('AUTO_MARCHES = ("BTC", "GOLD")', self.bot)
        self.assertIn('LIVE_CHOIX = {', self.bot)
        self.assertNotIn('"NASDAQ": ("sym"', self.bot)
        self.assertIn('"GOLD et BTC", "GOLD and BTC"', self.bot)
        self.assertNotIn('"GOLD et BTC", "NASDAQ, GOLD and BTC"', self.bot)

    def test_worker_rollover_recognizes_both_legacy_and_renamed_worker(self):
        self.assertIn("if run.get(\"name\") in {", self.rollover)
        self.assertIn("ALIGN MTF BOT (signaux BTC + Gold Telegram)", self.rollover)
        self.assertIn("ALIGN MTF BOT (signaux BTC + Gold + NASDAQ Telegram)", self.rollover)  # legacy worker drained safely

    def test_nasdaq_not_available_to_auto_execution(self):
        auto_trade = (Path(__file__).parent / "auto_trade.py").read_text(encoding="utf-8")
        topstep = (Path(__file__).parent / "topstep_trade.py").read_text(encoding="utf-8")
        self.assertNotIn('"NASDAQ":', auto_trade)
        symbol_map = next(line for line in topstep.splitlines() if line.startswith("SYMBOLES = "))
        self.assertNotIn('"NASDAQ"', symbol_map)
        self.assertIn('if m not in SYMBOLES:', auto_trade)
        self.assertIn('if m not in SYMBOLES:', topstep)

    def test_active_metaapi_and_public_market_channels_are_btc_gold_only(self):
        bot = self.bot
        metaapi = (Path(__file__).parent / "metaapi_check.py").read_text(encoding="utf-8")
        self.assertIn('for m, pair in MARCHES.items()', bot)
        self.assertIn('MARCHES_HISTORIQUES = (*MARCHES, "NASDAQ")', bot)
        self.assertIn('LIENS_CHAINES = {"BTC":', bot)
        self.assertNotIn('"NASDAQ": "https://t.me/', bot)
        self.assertNotIn('"NASDAQ": "🎙', bot)
        channel_attach = bot[bot.index("def connecter_canal("):bot.index("\ndef ", bot.index("def connecter_canal(") + 5)]
        self.assertIn('if mk_ == "NASDAQ":', channel_attach)
        self.assertIn("ne plus enregistrer de nouvelle chaîne NASDAQ", channel_attach)
        self.assertIn('for m in ("BTC", "GOLD")', metaapi)
        self.assertNotIn('"NASDAQ"', metaapi)

    def test_news_ai_scope_is_btc_and_gold_only(self):
        start = self.bot.index("def news_urgentes(")
        end = self.bot.index("\ndef ", start + 5)
        block = self.bot[start:end]
        self.assertIn("BTC / Gold", block)
        self.assertNotIn("NASDAQ", block)

    def test_bridge_requires_fresh_m5_m15_h1_h4_daily_and_weekly(self):
        for timeframe in ("M5", "M15", "H1", "H4", "D1", "W1"):
            self.assertIn(f'"{timeframe}"', self.workflow)
        self.assertIn("snapshots TradingView absents/périmés", self.workflow)


if __name__ == "__main__":
    unittest.main()
