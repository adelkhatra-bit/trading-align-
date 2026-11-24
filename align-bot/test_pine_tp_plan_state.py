from pathlib import Path
import re
import unittest


PINE = Path(__file__).resolve().parent / "pine" / "ALIGN_MTF_PRO_v25.pine"
TIMEFRAMES = ("M1", "M3", "M5", "M10", "M15", "M30", "M45", "H1", "H2", "H4", "D1", "W1")


class PineTpPlanStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PINE.read_text(encoding="utf-8")

    def test_tp_touch_state_is_bound_to_current_plan_levels(self):
        start = self.source.index("// TP1 touché :")
        end = self.source.index("// ═════════ LIGNES BLANCHES D'EXPLICATION", start)
        block = self.source[start:end]
        self.assertIn("(not na(tp1) and tp1 != tp1M)", block)
        self.assertIn("(not na(tp2) and tp2 != tp2M)", block)
        self.assertIn("(na(tp1) != na(tp1M))", block)
        self.assertIn("(na(tp2) != na(tp2M))", block)
        self.assertLess(block.index("if planTpChange"), block.index("if not tp1Ok and dirPlan"))

    def test_visual_confirmation_line_and_label_are_preserved_without_entry_marker(self):
        self.assertIn("lConf := line.new(bar_index, ent, bar_index + 30, ent", self.source)
        self.assertIn('eConf := label.new(bar_index + 30, ent, "✅ CONFIRMATION"', self.source)
        self.assertIn("line.delete(lConf)", self.source)
        self.assertIn("label.delete(eConf)", self.source)
        self.assertNotIn('eE := label.new(x1, ent, "ENTRÉE "', self.source)
        self.assertNotIn("lE := line.new(x1, ent", self.source)
        self.assertIn("var table t = table.new(pos, 11, 3", self.source)
        self.assertIn("lZH := line.new(x1, zMil", self.source)

    def test_targets_and_stop_visual_contract_is_preserved(self):
        self.assertIn('eTP1 := label.new(x1, tp1, "TP1 " + px(tp1)', self.source)
        self.assertIn('eTP2 := label.new(x1, tp2, "TP2 " + px(tp2)', self.source)
        self.assertIn('eSL  := label.new(x1, sl, "STOP " + px(sl)', self.source)
        self.assertIn('voirTP2  = input.bool(false, "TP1 touché : garder TP1 + afficher TP2", group=grpX)', self.source)
        self.assertIn('label.set_text(eTP1, "✅ TP1 TOUCHÉ " + px(tp1M)', self.source)
        self.assertIn('label.set_text(eTP2, "🎯 TP2 VISÉ " + px(tp2M)', self.source)

    def test_bridge_exports_all_twelve_timeframes_and_strategy_trigger_map(self):
        self.assertIn("bridgePayload =", self.source)
        for tf in TIMEFRAMES:
            self.assertRegex(self.source, rf'"{tf}"\s*:\{{')
        self.assertIn('strat == "SWING" ? "H1"', self.source)
        self.assertIn('strat == "DAY" ? "M5"', self.source)
        self.assertIn('strat == "SCALPING" ? "M1"', self.source)

    def test_entry_sl_tp_geometry_is_guarded_before_bridge_publication(self):
        self.assertIn("bridgePlanValid =", self.source)
        self.assertRegex(self.source, r"bridgePlanValid\s*=\s*dirPlan != 0")
        self.assertIn('f_align_v25_json_num(bridgePlanValid ? ent : na)', self.source)
        self.assertIn('f_align_v25_json_num(bridgePlanValid ? sl : na)', self.source)
        self.assertIn('f_align_v25_json_num(bridgePlanValid ? tp1 : na)', self.source)
        self.assertIn('f_align_v25_json_num(bridgePlanValid ? tp2 : na)', self.source)


if __name__ == "__main__":
    unittest.main()
