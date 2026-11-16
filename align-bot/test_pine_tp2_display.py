"""Non-regression checks for the isolated Pine v24.4 TP display proposal."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent / "pine"


class PineTp2Display(unittest.TestCase):
    def test_published_v24_reference_is_untouched(self):
        import hashlib
        source = (ROOT / "ALIGN_MTF_PRO_v24.pine").read_bytes()
        self.assertEqual(
            hashlib.sha256(source).hexdigest(),
            "0f1216cbb261eaaa3e019524071b67777cbecd0f5d10689cedf5727a06921085",
        )

    def test_v24_4_contains_only_the_tp_display_correction(self):
        base = (ROOT / "ALIGN_MTF_PRO_v24.pine").read_text(encoding="utf-8")
        proposal = (ROOT / "ALIGN_MTF_PRO_v24_4_PROPOSITION.pine").read_text(encoding="utf-8")
        expected = base.replace(
            "//@version=6\n",
            "//@version=6\n// PROPOSITION v24.4 — TP1 / TP2 visibles dès qu'un plan LONG / SHORT valide existe. NON PUBLIÉE.\n",
            1,
        )
        replacements = (
            (
                'voirTP2  = input.bool(false, "TP1 touché : garder TP1 + afficher TP2", group=grpX)',
                'voirTP2  = input.bool(true, "Afficher TP1 et TP2 sur le graphique", group=grpX)',
            ),
            (
                "    if voirTP2 and tp1Ok\n",
                "    if voirTP2 and dirPlan != 0 and not na(tp1M) and not na(tp2M)\n",
            ),
            (
                'eTk1 := label.new(bar_index + 12, tp1M, "✅ TP1 touché • SL à BE", style=label.style_label_left, color=color.new(color.lime, 10), textcolor=color.black, size=size.small)',
                'eTk1 := label.new(bar_index + 12, tp1M, tp1Ok ? "✅ TP1 touché • SL à BE" : "🎯 TP1 visé", style=label.style_label_left, color=color.new(color.lime, 10), textcolor=color.black, size=size.small)',
            ),
        )
        for old, new in replacements:
            self.assertEqual(expected.count(old), 1, old)
            expected = expected.replace(old, new, 1)
        self.assertEqual(proposal, expected)

    def test_tp2_lines_are_not_gated_by_tp1_hit(self):
        proposal = (ROOT / "ALIGN_MTF_PRO_v24_4_PROPOSITION.pine").read_text(encoding="utf-8")
        self.assertIn("voirTP2  = input.bool(true,", proposal)
        self.assertIn("if voirTP2 and dirPlan != 0 and not na(tp1M) and not na(tp2M)", proposal)
        self.assertNotIn("if voirTP2 and tp1Ok", proposal)
        self.assertIn('tp1Ok ? "✅ TP1 touché • SL à BE" : "🎯 TP1 visé"', proposal)
        self.assertIn('"🎯 TP2 visé"', proposal)


if __name__ == "__main__":
    unittest.main()
