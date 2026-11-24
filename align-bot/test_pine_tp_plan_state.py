from pathlib import Path
import unittest


PINE = Path(__file__).resolve().parent / "pine" / "ALIGN_MTF_PRO_v25.pine"


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

    def test_visual_contract_is_unchanged(self):
        self.assertIn('voirTP2  = input.bool(false, "TP1 touché : garder TP1 + afficher TP2", group=grpX)', self.source)
        self.assertIn('label.set_text(eTP1, "✅ TP1 TOUCHÉ " + px(tp1M)', self.source)
        self.assertIn('label.set_text(eTP2, "🎯 TP2 VISÉ " + px(tp2M)', self.source)
        self.assertIn("line.set_color(lTP1, color.lime)", self.source)
        self.assertIn("line.set_color(lTP2, color.aqua)", self.source)
        self.assertIn("line.set_width(lTP2, 3)", self.source)


if __name__ == "__main__":
    unittest.main()
