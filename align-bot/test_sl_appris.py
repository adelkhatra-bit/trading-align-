import os, sys, unittest
sys.path.insert(0, os.path.dirname(__file__))
import align_bot as ab


class SlAppris(unittest.TestCase):
    def test_pips(self):
        self.assertEqual(ab.pips("GOLD", 0.3), 3)
        self.assertEqual(ab.pips("BTC", 358.35), 358)
        self.assertEqual(ab.pips_txt("NASDAQ", 1), "1 pip")

    def _apres(self, d=-1, sl=100.0, tp1=90.0):
        return {"apres_sl": {"d": d, "e": 95.0, "sl": sl, "tp1": tp1, "t": 0, "pire": sl}}

    def test_short_chasse_puis_tp1_apprend(self):
        cle, out = self._apres(), []
        ab.suivre_apres_sl(out, "GOLD", {"t": 600, "atr": 5.0}, cle, 100.3, 99.0)   # mèche 3 pips au-dessus du SL
        self.assertFalse(out)
        ab.suivre_apres_sl(out, "GOLD", {"t": 1200, "atr": 5.0}, cle, 96.0, 89.5)   # puis TP1
        self.assertIn("3 pips", out[0])
        self.assertNotIn("apres_sl", cle)
        tr = {"d": -1, "e": 95.0, "sl": 100.0, "tp1": 90.0}
        ab.appliquer_marge_sl("GOLD", cle, tr, {"atr": 5.0})
        self.assertAlmostEqual(tr["sl"], 100.3)
        self.assertAlmostEqual(tr["marge_sl"], 0.3)

    def test_long_symetrique(self):
        cle, out = self._apres(d=1, sl=100.0, tp1=110.0), []
        ab.suivre_apres_sl(out, "BTC", {"t": 60, "atr": 50.0}, cle, 101.0, 96.0)
        ab.suivre_apres_sl(out, "BTC", {"t": 120, "atr": 50.0}, cle, 111.0, 104.0)
        self.assertIn("4 pips", out[0])
        tr = {"d": 1, "e": 105.0, "sl": 100.0, "tp1": 110.0}
        ab.appliquer_marge_sl("BTC", cle, tr, {"atr": 50.0})
        self.assertAlmostEqual(tr["sl"], 96.0)

    def test_vrai_retournement_pas_appris(self):
        cle, out = self._apres(), []
        ab.suivre_apres_sl(out, "GOLD", {"t": 60, "atr": 2.0}, cle, 106.0, 99.0)    # 6 $ au-delà du SL > 1 ATR
        ab.suivre_apres_sl(out, "GOLD", {"t": 120, "atr": 2.0}, cle, 95.0, 89.0)
        self.assertFalse(out)
        self.assertNotIn("sl_appris", cle)

    def test_expire_sans_tp1(self):
        cle, out = self._apres(), []
        ab.suivre_apres_sl(out, "GOLD", {"t": ab.APRES_SL_DUREE + 1, "atr": 5.0}, cle, 101.0, 99.0)
        self.assertFalse(out)
        self.assertNotIn("apres_sl", cle)

    def test_marge_plafonnee(self):
        cle = {"sl_appris": {"hist": [40.0]}}
        self.assertEqual(ab.marge_sl_apprise(cle, 10.0), 5.0)
        tr = {"d": -1, "e": 95.0, "sl": 100.0, "tp1": 90.0}
        ab.appliquer_marge_sl("BTC", {}, tr, {"atr": 10.0})
        self.assertEqual(tr["sl"], 100.0)          # rien appris = SL inchangé


if __name__ == "__main__":
    unittest.main()
