"""Contrôles statiques de la proposition Pine non publiée : clôtures MTF et gate Gold/NASDAQ."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
PINE = ROOT / "pine" / "ALIGN_MTF_PRO_v25_PROPOSITION.pine"


class PineClosedMarketSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PINE.read_text(encoding="utf-8")

    def test_mtf_values_use_only_the_last_closed_candle(self):
        self.assertIn("f_etat_precedent() =>", self.source)
        self.assertIn("[d[1], sqz[1], rsiVal[1]]", self.source)
        self.assertEqual(self.source.count("lookahead=barmerge.lookahead_on"), 12)
        self.assertNotIn(", f_etat())", self.source)

    def test_gold_and_nasdaq_are_detected_without_touching_btc_logic(self):
        self.assertIn('str.contains(tickerUpper, "XAU")', self.source)
        self.assertIn('str.contains(tickerUpper, "NAS100")', self.source)
        self.assertIn("strictHtfMarket = isGoldMarket or isNasdaqMarket", self.source)
        self.assertIn("h1h4Confirmed = u1h and u4", self.source)

    def test_all_confirmed_strategies_require_h1_h4_confluence_on_gold_nasdaq(self):
        self.assertIn("and (not strictHtfMarket or h1h4Confirmed)", self.source)
        self.assertIn('strat := ""', self.source)
        self.assertIn('etatS := "EN ATTENTE"', self.source)
        self.assertIn("ANTICIPATION uniquement : H1 et H4 doivent clôturer", self.source)


if __name__ == "__main__":
    unittest.main()
