import unittest
from pathlib import Path


class PrimaryTimeframeVisualContractTest(unittest.TestCase):
    def setUp(self):
        self.pine = (Path(__file__).parent / "pine" / "ALIGN_MTF_PRO_v25.pine").read_text(encoding="utf-8")

    def test_weekly_is_visible_as_closed_context_without_changing_eleven_tf_score(self):
        self.assertIn('[dW, sW, rW, dWFermee, rWFermee, bridgeTimeW1] = f_etat_mtf("W")', self.pine)
        self.assertIn("var table t = table.new(pos, 12, 3", self.pine)
        self.assertIn('table.cell(t, 11, 0, "1W"', self.pine)
        self.assertIn('dvW = nz(dWFermee)', self.pine)
        self.assertIn('rvW = nz(rWFermee, 50)', self.pine)
        self.assertIn("hors score d'alignement des 11 UT", self.pine)
        self.assertIn("table.merge_cells(t, 0, 2, 11, 2)", self.pine)

    def test_visual_rsi_matches_closed_direction_state(self):
        self.assertIn("rv = array.get(rsisFermees, i)", self.pine)
        self.assertIn("RSI clôturé :", self.pine)
        self.assertIn("Compression en formation :", self.pine)

    def test_primary_decision_timeframes_remain_explicit_in_strategy_roles(self):
        for role in ("déclenchement DAY", "direction SCALP", "confirmation SWING", "contexte DAY", "direction SWING"):
            self.assertIn(role, self.pine)
        # This presentation-only change must not alter the scoring loop or its 11-UT threshold.
        self.assertIn("minAlign = input.int(8, \"UT alignées mini (sur 11)\"", self.pine)
        self.assertIn("for i = 0 to 10", self.pine)


if __name__ == "__main__":
    unittest.main()
