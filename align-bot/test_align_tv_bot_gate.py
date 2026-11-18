import pathlib
import unittest


BOT_SOURCE = pathlib.Path(__file__).with_name("align_bot.py").read_text(encoding="utf-8")


class TradingViewBridgeGateTests(unittest.TestCase):
    def test_signal_paths_require_tradingview_bridge_by_default(self):
        # Both production analysis paths must fail closed until the Pine v25 bridge is live.
        gate = 'os.environ.get("ALIGN_REQUIRE_TV_BRIDGE", "1") == "1"'
        self.assertEqual(BOT_SOURCE.count(gate), 2)
        self.assertNotIn('os.environ.get("ALIGN_REQUIRE_TV_BRIDGE", "0") == "1"', BOT_SOURCE)


if __name__ == "__main__":
    unittest.main()
