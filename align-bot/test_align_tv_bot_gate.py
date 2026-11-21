import pathlib
import unittest


BOT_SOURCE = pathlib.Path(__file__).with_name("align_bot.py").read_text(encoding="utf-8")
WORKFLOW_SOURCE = pathlib.Path(__file__).resolve().parents[1].joinpath(".github", "workflows", "align-bot.yml").read_text(encoding="utf-8")


class TradingViewBridgeGateTests(unittest.TestCase):
    def test_invalid_bridge_shortens_bot_run_but_keeps_final_failure_gate(self):
        # Guard the exact fail-fast expression: bridge invalid -> 120s, valid -> normal 21000s.
        self.assertRegex(
            WORKFLOW_SOURCE,
            r"DUREE_SEC:\s*\$\{\{\s*steps\.bridge\.outputs\.ALIGN_TV_BRIDGE_PRET\s*==\s*'0'\s*&&\s*'120'\s*\|\|\s*'21000'\s*\}\}",
        )
        self.assertRegex(
            WORKFLOW_SOURCE,
            r"if:\s*\$\{\{\s*always\(\)\s*&&\s*steps\.bridge\.outputs\.ALIGN_TV_BRIDGE_PRET\s*==\s*'0'\s*\}\}",
        )
        self.assertIn("Bridge TradingView obligatoire — échec signalé", WORKFLOW_SOURCE)
        self.assertIn("exit 1", WORKFLOW_SOURCE)

    def test_signal_paths_require_tradingview_bridge_by_default(self):
        # Both production analysis paths must fail closed until the Pine v25 bridge is live.
        gate = 'os.environ.get("ALIGN_REQUIRE_TV_BRIDGE", "1") == "1"'
        self.assertEqual(BOT_SOURCE.count(gate), 2)
        self.assertNotIn('os.environ.get("ALIGN_REQUIRE_TV_BRIDGE", "0") == "1"', BOT_SOURCE)


if __name__ == "__main__":
    unittest.main()
