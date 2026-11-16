"""Static regression checks for the TradingView closed-timeframe safety gate."""
from pathlib import Path
import unittest

PINE = Path(__file__).resolve().parent / "pine" / "ALIGN_MTF_PRO_v25.pine"


class PineClosedMtfGuard(unittest.TestCase):
    def test_gold_nasdaq_use_previous_closed_candle_for_m5_m15_h1_h4(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn("f_dir_confirme() =>", source)
        self.assertIn("d[1]", source)
        for tf in ('"5"', '"15"', '"60"', '"240"'):
            self.assertIn(f"request.security(syminfo.tickerid, {tf}, f_dir_confirme(), lookahead=barmerge.lookahead_on)", source)

    def test_gold_nasdaq_trade_direction_is_blocked_without_four_way_confluence(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn("isGoldNasdaq", source)
        self.assertIn("gnConfluence = dirStable != 0 and nz(d5Fermee) == dirStable and nz(d15Fermee) == dirStable", source)
        self.assertIn("nz(d60Fermee) == dirStable and nz(d240Fermee) == dirStable", source)
        self.assertIn("dirPlan = isGoldNasdaq and not gnConfluence ? 0 : dirStable", source)
        self.assertIn("(not isGoldNasdaq or (gnConfluence and dirStable == 1))", source)
        self.assertIn("(not isGoldNasdaq or (gnConfluence and dirStable == -1))", source)


if __name__ == "__main__":
    unittest.main()
