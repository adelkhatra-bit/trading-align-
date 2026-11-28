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


    def test_strategy_specific_bridge_gates_use_closed_timeframes(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn("d1Fermee", source)
        self.assertIn("dDFermee", source)
        self.assertIn("dWFermee", source)
        self.assertIn(
            'strat == "SWING" ? (nz(dDFermee) == dirPlan and nz(d60Fermee) == dirPlan and nz(d240Fermee) != -dirPlan and nz(dWFermee) != -dirPlan)',
            source,
        )
        self.assertIn(
            'strat == "DAY" ? (nz(d60Fermee) == dirPlan and nz(d5Fermee) == dirPlan and nz(d240Fermee) != -dirPlan)',
            source,
        )
        self.assertIn(
            'strat == "SCALPING" ? (nz(d60Fermee) != -dirPlan and nz(d15Fermee) == dirPlan and nz(d5Fermee) == dirPlan and nz(d1Fermee) == dirPlan)',
            source,
        )

    def test_visual_and_bridge_share_the_same_strategy_confirmation_gate(self):
        source = PINE.read_text(encoding="utf-8")
        ui_line = next(line for line in source.splitlines() if line.startswith("planClosedMtfOkUi = "))
        bridge_line = next(line for line in source.splitlines() if line.startswith("bridgeClosedMtfOk = "))
        for gate in (
            'strat == "SWING" ?',
            'strat == "DAY" ?',
            'strat == "SCALPING" ?',
            'nz(dDFermee) == dirPlan',
            'nz(d5Fermee) == dirPlan',
            'nz(d1Fermee) == dirPlan',
        ):
            self.assertIn(gate, ui_line)
            self.assertIn(gate, bridge_line)

    def test_direction_confirmation_uses_closed_htf_candles_not_live_ones(self):
        # The executable direction is a pure projection of already-confirmed MTF states.
        source = PINE.read_text(encoding="utf-8")
        self.assertIn("dirStable = dirBrut", source)
        self.assertNotIn("var int dirStable = 0", source)
        # Include the confirmation declarations: they intentionally precede dirBrut.
        decision_start = source.index("zoneLongConfirmee =")
        decision_end = source.index("// GOLD : aucune direction de trade", decision_start)
        decision = source[decision_start:decision_end]
        self.assertNotIn("nz(d15)", decision)
        self.assertNotIn("nz(d60)", decision)
        self.assertIn("zoneLongConfirmee = (zoneHaut or retHaut) and retLongConfirme", decision)
        self.assertIn("zoneShortConfirmee = (zoneBas or retBas) and retShortConfirme", decision)


if __name__ == "__main__":
    unittest.main()
