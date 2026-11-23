import subprocess
import sys
import unittest
from pathlib import Path


class ProductionMarketCoverageTest(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.workflow = (root / ".github" / "workflows" / "align-bot.yml").read_text(encoding="utf-8")
        self.rollover = (root / ".github" / "workflows" / "align-bot-rollover.yml").read_text(encoding="utf-8")
        self.sniper_workflow = (root / ".github" / "workflows" / "sniper-replay.yml").read_text(encoding="utf-8")
        self.sniper_replay = (Path(__file__).parent / "replay_sniper.py").read_text(encoding="utf-8")
        self.bot = (Path(__file__).parent / "align_bot.py").read_text(encoding="utf-8")

    def test_telegram_preflight_accepts_only_the_canonical_align_bot(self):
        self.assertIn('BOT_USERNAME_ATTENDU = "align_mtf_adel_bot"', self.workflow)
        self.assertIn('if username != BOT_USERNAME_ATTENDU:', self.workflow)
        self.assertIn('if (payload.get("result") or {}).get("is_bot") is not True:', self.workflow)
        self.assertIn('ÉCHEC: le secret TELEGRAM_TOKEN ne correspond pas au bot ALIGN attendu', self.workflow)
        self.assertIn('is_bot") is not True', self.workflow)
        self.assertIn('TELEGRAM_API_OK bot=@' + username', self.workflow)

    def test_worker_operational_scope_is_btc_and_gold_only(self):
        self.assertIn("required_symbols = align_bot.symboles_bridge_obligatoires(time.time())", self.workflow)
        self.assertIn("for symbol in required_symbols:", self.workflow)
        self.assertIn("def symboles_bridge_obligatoires(ts=None):", self.bot)
        self.assertIn("BRIDGE_SESSION_CLOSED symbol=XAUUSD", self.workflow)
        self.assertIn("Analyse BTC + Gold et envoi Telegram", self.workflow)
        self.assertNotIn("NAS100", self.workflow)
        self.assertNotIn('report["nasdaq_open_trade"]', self.workflow)
        self.assertNotIn('report["nasdaq_auto_follow_count"]', self.workflow)
        self.assertIn('MARCHES = {"BTC": "XBTUSD", "GOLD": "XAUUSD"}', self.bot)
        self.assertIn('AUTO_MARCHES = ("BTC", "GOLD")', self.bot)
        self.assertNotIn('"NASDAQ": "💠 NASDAQ"', self.bot)
        self.assertIn("def marche_retiree_demande(txt):", self.bot)
        self.assertIn("if marche_retiree_demande(txt):", self.bot)
        self.assertIn("MARCHES_HISTORIQUES = tuple(MARCHES)", self.bot)
        self.assertIn("STATE_SCHEMA_VERSION = 4", self.bot)
        self.assertIn("def migrer_scope_marches_btc_gold_only(etat):", self.bot)
        self.assertIn('report["active_markets"] = state.get("marches_actifs", [])', self.workflow)
        self.assertIn('report["nasdaq_active_root_key"] = "NASDAQ" in state', self.workflow)
        self.assertIn('report["nasdaq_archive_count"]', self.workflow)
        self.assertIn('report["nasdaq_preference_count"]', self.workflow)
        self.assertIn('"canal_live", "liens_marche", "veille_cloture", "pause_auto"', self.bot)
        self.assertIn('LIVE_CHOIX = {', self.bot)
        self.assertNotIn('"NASDAQ": ("sym"', self.bot)
        self.assertIn('"GOLD et BTC", "GOLD and BTC"', self.bot)
        self.assertNotIn('"GOLD et BTC", "NASDAQ, GOLD and BTC"', self.bot)

    def test_worker_cycle_exception_emits_bounded_traceback(self):
        self.assertIn("traceback.print_exc(limit=8)", self.bot)
        self.assertIn('print("tour", ex, flush=True)', self.bot)

    def test_post_run_memory_audit_checks_persisted_btc_gold_scope(self):
        self.assertIn("Auditer la mémoire persistée après migration BTC + GOLD", self.workflow)
        self.assertIn('if state.get("marches_actifs") != ["BTC", "GOLD"]:', self.workflow)
        self.assertIn('if "NASDAQ" in state:', self.workflow)
        self.assertIn("state.json absent après le worker", self.workflow)
    def test_sniper_replay_exposes_and_accepts_only_btc_and_gold(self):
        self.assertIn("type: choice", self.sniper_workflow)
        self.assertIn("- XAUUSD", self.sniper_workflow)
        self.assertIn("- XBTUSD", self.sniper_workflow)
        self.assertIn("- GOLD", self.sniper_workflow)
        self.assertIn("- BTC", self.sniper_workflow)
        self.assertNotIn("NASDAQ", self.sniper_workflow)
        self.assertNotIn("NAS100", self.sniper_workflow)
        self.assertIn('MARCHE_PAIRS = {"GOLD": "XAUUSD", "BTC": "XBTUSD"}', self.sniper_replay)
        self.assertIn('if a.marche not in MARCHE_PAIRS or a.pair != MARCHE_PAIRS[a.marche]:', self.sniper_replay)

    def test_sniper_replay_rejects_nasdaq_before_fetching_market_data(self):
        script = Path(__file__).parent / "replay_sniper.py"
        result = subprocess.run(
            [sys.executable, str(script), "--pair", "NAS100", "--marche", "NASDAQ"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("--marche et --pair doivent correspondre", result.stderr)
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
        self.assertIn('MARCHES = {"BTC": "XBTUSD", "GOLD": "XAUUSD"}', bot)
        self.assertIn("MARCHES_HISTORIQUES = tuple(MARCHES)", bot)
        self.assertIn('for nom_marche, pair in MARCHES.items():', bot)
        self.assertIn('for marche in MARCHES:', bot)
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
