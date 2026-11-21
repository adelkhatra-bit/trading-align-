"""Hard guard: production ALIGN market providers, analysis and chart links accept BTC + GOLD only."""
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import align_bot as ab


class ActiveMarketsBTCGoldOnly(unittest.TestCase):
    def test_registry_and_price_references_contain_only_active_markets(self):
        self.assertEqual(ab.MARCHES, {"BTC": "XBTUSD", "GOLD": "XAUUSD"})
        self.assertEqual(ab.MARCHES_HISTORIQUES, ("BTC", "GOLD"))
        self.assertEqual(set(ab.TV_ETALON), {"XBTUSD", "XAUUSD"})
        self.assertEqual(set(ab.ICONE), {"BTC", "GOLD"})
        self.assertEqual(set(ab.PIP), {"BTC", "GOLD"})

    def test_legacy_nasdaq_pair_is_rejected_before_any_price_provider(self):
        with mock.patch.object(ab, "kraken") as kraken, mock.patch.object(ab, "paxg_or") as gold:
            for pair in ("NAS100", "NASDAQ", "NQ=F"):
                with self.subTest(pair=pair):
                    with self.assertRaises(ValueError):
                        ab.bougies(pair, 5)
            kraken.assert_not_called()
            gold.assert_not_called()

    def test_removed_nasdaq_provider_functions_are_not_available(self):
        self.assertFalse(hasattr(ab, "yahoo_nasdaq"))
        self.assertFalse(hasattr(ab, "nasdaq_direct"))

    def test_chart_link_does_not_redirect_unknown_market_to_gold(self):
        self.assertIn("KRAKEN%3AXBTUSD", ab.url_tradingview("BTC", "5"))
        self.assertIn("FOREXCOM%3AXAUUSD", ab.url_tradingview("GOLD", "5"))
        with self.assertRaises(ValueError):
            ab.url_tradingview("NASDAQ", "5")

    def test_retired_market_is_still_explicitly_refused_not_remapped(self):
        for request in ("NASDAQ", "NAS100", "NQ"):
            with self.subTest(request=request):
                self.assertTrue(ab.marche_retiree_demande(request))
                self.assertIsNone(ab.marche_demande(request))

    def test_retired_market_labels_are_not_in_active_telegram_menus(self):
        self.assertNotIn("💠 Analyse Nasdaq", ab.TRAD)
        self.assertFalse(any("nasdaq" in row[1].lower() or "nasdaq" in row[2].lower()
                             for row in ab.SESSIONS))

    def test_nasdaq_only_legacy_alert_is_not_routed_to_telegram_channel(self):
        message = ab.Msg("NASDAQ : ancienne alerte")
        message.marches = frozenset({"NASDAQ"})
        self.assertEqual(ab.destinataires_message({"canal": "-100123"}, ["12345"], message), [])
        self.assertEqual(ab.destinataires_message({"canal": "-100123"}, ["12345"],
                                                  "NASDAQ : ancienne alerte"), [])


if __name__ == "__main__":
    unittest.main()
