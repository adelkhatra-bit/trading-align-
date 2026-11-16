import unittest
from pathlib import Path


class TradingViewVisualContractTest(unittest.TestCase):
    def setUp(self):
        self.pine = (Path(__file__).parent / "pine" / "ALIGN_MTF_PRO_v25_PROPOSITION.pine").read_text(encoding="utf-8")

    def test_tp2_has_its_own_projected_line_and_label(self):
        self.assertIn("lTP2 := line.new(x1, tp2", self.pine)
        self.assertIn('eTP2 := label.new(x1, tp2, "TP2 "', self.pine)

    def test_weekly_is_visible_without_changing_eleven_timeframe_score(self):
        self.assertIn("request.security(syminfo.tickerid, \"W\"", self.pine)
        self.assertIn("var table t = table.new(pos, 12, 3", self.pine)
        self.assertIn('table.cell(t, 11, 0, "W"', self.pine)
        self.assertIn("ne modifie pas le score des 11 UT", self.pine)
        self.assertIn("table.merge_cells(t, 0, 2, 11, 2)", self.pine)


if __name__ == "__main__":
    unittest.main()
