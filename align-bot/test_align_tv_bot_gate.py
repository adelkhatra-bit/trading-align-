from datetime import datetime, timezone
import pathlib
import unittest

import align_bot as ab


BOT_SOURCE = pathlib.Path(__file__).with_name("align_bot.py").read_text(encoding="utf-8")
WORKFLOW_SOURCE = pathlib.Path(__file__).resolve().parents[1].joinpath(".github", "workflows", "align-bot.yml").read_text(encoding="utf-8")


class TradingViewBridgeGateTests(unittest.TestCase):
    def test_bridge_failure_keeps_telegram_worker_alive_but_signals_fail_closed(self):
        # Manual diagnostics use 300s; production schedule/workflow_run retain 21000s.
        self.assertIn("DUREE_SEC: \"${{ github.event_name == 'workflow_dispatch' && '300' || '21000' }}\"", WORKFLOW_SOURCE)
        self.assertIn("Les workers schedule/workflow_run conservent leur durée de production.", WORKFLOW_SOURCE)
        self.assertIn('ALIGN_TV_BRIDGE_PRET: ${{ steps.bridge.outputs.ALIGN_TV_BRIDGE_PRET == \'0\' && \'0\' || \'1\' }}', WORKFLOW_SOURCE)
        self.assertIn('ALIGN_REQUIRE_TV_BRIDGE: "1"', WORKFLOW_SOURCE)
        self.assertRegex(
            WORKFLOW_SOURCE,
            r"if:\s*\$\{\{\s*always\(\)\s*&&\s*steps\.bridge\.outputs\.ALIGN_TV_BRIDGE_PRET\s*==\s*'0'\s*\}\}",
        )
        self.assertIn("Bridge TradingView obligatoire — échec signalé", WORKFLOW_SOURCE)
        self.assertIn("exit 1", WORKFLOW_SOURCE)
    def test_preflight_requires_btc_always_and_gold_only_during_cme_session(self):
        saturday_closed = datetime(2026, 11, 21, 12, 48, tzinfo=timezone.utc).timestamp()
        sunday_open = datetime(2026, 11, 22, 23, 30, tzinfo=timezone.utc).timestamp()
        maintenance = datetime(2026, 11, 24, 22, 30, tzinfo=timezone.utc).timestamp()

        self.assertEqual(ab.symboles_bridge_obligatoires(saturday_closed), ("BTCUSD",))
        self.assertEqual(ab.symboles_bridge_obligatoires(sunday_open), ("BTCUSD", "XAUUSD"))
        self.assertEqual(ab.symboles_bridge_obligatoires(maintenance), ("BTCUSD",))

    def test_workflow_uses_same_cme_session_rule_and_keeps_gold_fail_closed(self):
        self.assertIn("required_symbols = align_bot.symboles_bridge_obligatoires(time.time())", WORKFLOW_SOURCE)
        self.assertIn("for symbol in required_symbols:", WORKFLOW_SOURCE)
        self.assertIn("BRIDGE_SESSION_CLOSED symbol=XAUUSD", WORKFLOW_SOURCE)
        self.assertIn('ALIGN_REQUIRE_TV_BRIDGE: "1"', WORKFLOW_SOURCE)
        self.assertIn('"; active_age_ms=" + str(active_age)', WORKFLOW_SOURCE)
        self.assertIn('"; UT_périmées="', WORKFLOW_SOURCE)
        self.assertIn('"; last_rejection=" + rejection_text', WORKFLOW_SOURCE)
        self.assertIn("réponse bridge JSON non-objet pour", WORKFLOW_SOURCE)

    def test_bridge_failure_detail_reports_age_of_each_stale_timeframe(self):
        detail = ab.detail_bridge_invalide({
            "activeTimeframe": "M5",
            "activeTimeframeFresh": True,
            "activeTimeframeAgeMs": 59000,
            "snapshots": {
                "M5": {"fresh": False, "ageMs": 421000},
                "M15": {"fresh": True, "ageMs": 210000},
                "H1": {"fresh": True, "ageMs": 1200000},
                "H4": {"fresh": True, "ageMs": 7200000},
                "D1": {"fresh": True, "ageMs": 30000000},
                "W1": {"fresh": True, "ageMs": 100000000},
            },
            "lastRejection": {"error": "stale_or_future_entry_trigger_candle", "ageMs": 1000},
        })
        self.assertIn("UT active M5 fraîche (59 s)", detail)
        self.assertIn("UT périmées M5 (421 s)", detail)
        self.assertIn("dernier envoi refusé : stale_or_future_entry_trigger_candle", detail)

    def test_signal_paths_require_tradingview_bridge_by_default(self):
        # Both production analysis paths must fail closed until the Pine v25 bridge is live.
        gate = 'os.environ.get("ALIGN_REQUIRE_TV_BRIDGE", "1") == "1"'
        self.assertEqual(BOT_SOURCE.count(gate), 2)
        self.assertNotIn('os.environ.get("ALIGN_REQUIRE_TV_BRIDGE", "0") == "1"', BOT_SOURCE)


if __name__ == "__main__":
    unittest.main()
