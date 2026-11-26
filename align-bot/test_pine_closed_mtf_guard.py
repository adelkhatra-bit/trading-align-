"""Static regression checks for the TradingView closed-timeframe safety gate."""
from pathlib import Path
import unittest

PINE = Path(__file__).resolve().parent / "pine" / "ALIGN_MTF_PRO_v25.pine"


class PineClosedMtfGuard(unittest.TestCase):
    def test_gold_uses_previous_closed_candle_for_m5_m15_h1_h4(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn("f_dir_confirme() =>", source)
        self.assertIn("d[1]", source)
        import re
        for tf in ('"5"', '"15"', '"60"', '"240"'):
            pattern = rf'request\.security\(syminfo\.tickerid,\s*{re.escape(tf)},\s*f_dir_confirme\(\),\s*lookahead=barmerge\.lookahead_on\)'
            self.assertRegex(source, pattern)

    def test_gold_requires_four_way_confluence_and_unsupported_markets_are_blocked(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn("isGold", source)
        self.assertIn("isSupportedMarket = isBtc or isGold", source)
        self.assertIn("goldConfluence = dirStable != 0 and nz(d5Fermee) == dirStable and nz(d15Fermee) == dirStable", source)
        self.assertIn("nz(d60Fermee) == dirStable and nz(d240Fermee) == dirStable", source)
        self.assertIn("dirPlan = not isSupportedMarket or (isGold and not goldConfluence) ? 0 : dirStable", source)
        self.assertIn("sigHaut = isSupportedMarket and sigHaut0", source)
        self.assertIn("sigBas  = isSupportedMarket and sigBas0", source)


    def test_btc_bridge_requires_both_closed_h1_and_h4(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn(
            'bridgeClosedMtfOk = isGold ? (nz(d5Fermee) == dirPlan and nz(d15Fermee) == dirPlan and nz(d60Fermee) == dirPlan and nz(d240Fermee) == dirPlan) : (nz(d60Fermee) == dirPlan and nz(d240Fermee) == dirPlan)',
            source,
        )

    def test_direction_confirmation_uses_closed_htf_candles_not_live_ones(self):
        # Régression : la confirmation du sens ne doit jamais lire la bougie 15 min / 1 h en formation
        # (nz(d15) / nz(d60)), sinon le sens SHORT/LONG bascule à chaque tick.
        source = PINE.read_text(encoding="utf-8")
        start = source.index("var int dirStable = 0")
        block = source[start:start + 700]
        self.assertNotIn("nz(d15)", block)
        self.assertNotIn("nz(d60)", block)
        self.assertIn("nz(d15Fermee) == dirBrut or nz(d60Fermee) == dirBrut", block)


if __name__ == "__main__":
    unittest.main()
