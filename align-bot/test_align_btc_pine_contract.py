"""Contract tests for the dedicated BTC-only TradingView Pine indicator."""
from pathlib import Path
import unittest

PINE = Path(__file__).resolve().parent / "pine" / "ALIGN_BTC_MTF_PRO_v25.pine"


class AlignBtcPineContract(unittest.TestCase):
    def test_indicator_is_a_distinct_btc_only_script(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn('indicator("ALIGN BTC MTF PRO v25 (Dedicated)", shorttitle="ALIGN BTC v25"', source)
        self.assertIn('isBtc = str.contains(tickerUpper, "BTC") or str.contains(tickerUpper, "XBT")', source)
        self.assertIn("isGold = false", source)
        self.assertIn("isSupportedMarket = isBtc", source)
        self.assertIn('bridgeMarket = isBtc ? "BTCUSD" : "UNSUPPORTED"', source)
        self.assertIn('"source":"ALIGN_MTF_PRO_V25"', source)
        self.assertNotIn('bridgeMarket = isBtc ? "BTCUSD" : isGold ? "XAUUSD"', source)

    def test_btc_ui_and_bridge_require_the_same_closed_h1_h4_confirmation(self):
        source = PINE.read_text(encoding="utf-8")
        required = "nz(d60Fermee) == dirPlan and nz(d240Fermee) == dirPlan"
        ui = next(line for line in source.splitlines() if line.startswith("planClosedMtfOkUi = "))
        bridge = next(line for line in source.splitlines() if line.startswith("bridgeClosedMtfOk = "))
        self.assertIn(required, ui)
        self.assertIn(required, bridge)
        self.assertIn("planConfirmedUi", source)
        self.assertIn("bridgeSignal = bridgeConfirmed ?", source)

    def test_gold_routing_is_not_present_in_the_dedicated_btc_export(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertNotIn('"XAUUSD"', source)
        self.assertNotIn('isGold = str.contains', source)
        self.assertIn('"UNSUPPORTED"', source)


if __name__ == "__main__":
    unittest.main()
