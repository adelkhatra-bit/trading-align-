"""Régression Fibonacci : affichage progressif sur TradingView, jamais dans Telegram."""
from pathlib import Path
import unittest

import align_bot as ab

ROOT = Path(__file__).resolve().parent
PINE = ROOT / "pine" / "ALIGN_MTF_PRO_v24_5_FIBO_PROPOSITION.pine"
REFERENCE = ROOT / "pine" / "ALIGN_MTF_PRO_v24.pine"


class FibonacciTradingView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pine = PINE.read_text(encoding="utf-8")
        cls.reference = REFERENCE.read_text(encoding="utf-8")
        cls.bot = (ROOT / "align_bot.py").read_text(encoding="utf-8")

    def test_fibonacci_is_not_sent_as_a_telegram_message(self):
        self.assertFalse(hasattr(ab, "fibo_zones"))
        self.assertNotIn("FIBO_UT", self.bot)
        self.assertNotIn("fibo_zones(", self.bot)
        self.assertNotIn("ZONE FIBONACCI", self.bot)

    def test_progress_is_visible_on_tradingview_and_updates_in_the_status_bar(self):
        self.assertIn('voirFiboProgression = input.bool(true,', self.pine)
        self.assertIn('ligne += "\\n📐 FIBO — "', self.pine)
        self.assertIn('f_fibo_txt("15 min"', self.pine)
        self.assertIn('f_fibo_txt("1h"', self.pine)
        self.assertIn('f_fibo_txt("4h"', self.pine)
        self.assertIn('⚠ ZONE CLÉ', self.pine)
        self.assertIn('_pct >= 61.8 and _pct <= 78.6', self.pine)

    def test_lookbacks_match_the_previous_fibonacci_rule(self):
        self.assertIn('request.security(syminfo.tickerid, "15", [ta.highest(high, 48)[1]', self.pine)
        self.assertIn('request.security(syminfo.tickerid, "60", [ta.highest(high, 48)[1]', self.pine)
        self.assertIn('request.security(syminfo.tickerid, "240", [ta.highest(high, 30)[1]', self.pine)
        self.assertIn('request.security(syminfo.tickerid, "15", [ta.highest(high, 24)[1], ta.lowest(low, 24)[1]])', self.pine)

    def test_no_duplicate_15m_midpoint_label_or_repeated_security_calls(self):
        self.assertNotIn("voirF50x", self.pine)
        self.assertEqual(self.pine.count('ligne += "\\n📐 FIBO — "'), 1)
        base_calls = self.reference.count("request.security(")
        new_calls = self.pine.count("request.security(")
        self.assertEqual(new_calls, base_calls + 1)
        self.assertLessEqual(new_calls, 40)


if __name__ == "__main__":
    unittest.main()
