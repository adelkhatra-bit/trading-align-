"""Contrôle statique du petit popup animé du coach TradingView."""
import os
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CoachShowcaseMarkup(unittest.TestCase):
    def test_popup_accessible_et_animation_presente(self):
        path = os.path.join(ROOT, "tradingview-analyzer", "popup.html")
        with open(path, encoding="utf-8-sig") as f:
            html = f.read()
        self.assertIn('id="coachShow"', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn("@keyframes coachShowIn", html)
        self.assertIn("prefers-reduced-motion:reduce", html)

    def test_evenements_coach_declenchent_le_show_sans_repetition(self):
        path = os.path.join(ROOT, "tradingview-analyzer", "popup.js")
        with open(path, encoding="utf-8-sig") as f:
            js = f.read()
        self.assertIn("function showCoachShowcase", js)
        self.assertIn("showCoachShowcase(txt, color, _p)", js)
        self.assertIn("_coachShowLastKey", js)
        self.assertIn("clearTimeout(_coachShowTimer)", js)


if __name__ == "__main__":
    unittest.main()
