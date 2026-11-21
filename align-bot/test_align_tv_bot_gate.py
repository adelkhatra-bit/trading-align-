import pathlib
import unittest


BOT_SOURCE = pathlib.Path(__file__).with_name("align_bot.py").read_text(encoding="utf-8")
WORKFLOW_SOURCE = pathlib.Path(__file__).resolve().parents[1].joinpath(".github", "workflows", "align-bot.yml").read_text(encoding="utf-8")


class TradingViewBridgeGateTests(unittest.TestCase):
    def test_invalid_bridge_shortens_bot_run_but_keeps_final_failure_gate(self):
        self.assertIn("120", WORKFLOW_SOURCE)
        self.assertIn("DUREE_SEC:", WORKFLOW_SOURCE)
        self.assertIn("Bridge TradingView obligatoire — échec signalé", WORKFLOW_SOURCE)
        self.assertIn("exit 1", WORKFLOW_SOURCE)

    def test_signal_paths_require_tradingview_bridge_by_default(self):
        # Both production analysis paths must fail closed until the Pine v25 bridge is live.
        gate = 'os.environ.get("ALIGN_REQUIRE_TV_BRIDGE", "1") == "1"'
        self.assertEqual(BOT_SOURCE.count(gate), 2)
        self.assertNotIn('os.environ.get("ALIGN_REQUIRE_TV_BRIDGE", "0") == "1"', BOT_SOURCE)


if __name__ == "__main__":
    unittest.main()
