import os
import re
import unittest

import align_bot as ab

HERE = os.path.dirname(os.path.abspath(__file__))


class RRMinEntree(unittest.TestCase):
    """Décision trader : gain/risque minimum 1:2 pour autoriser une entrée (sinon ATTENTE)."""

    def test_seuil_entree_est_deux(self):
        self.assertEqual(ab.RR_MIN_ENTREE, 2.0)

    def test_indicateur_garde_son_gain_min_de_parite(self):
        # GAIN_MIN reste celui de l'indicateur Pine (1.5) : il sert aux projections et à la parité.
        self.assertEqual(ab.GAIN_MIN, 1.5)

    def test_aucune_porte_d_entree_ne_repasse_a_gain_min(self):
        src = open(os.path.join(HERE, "align_bot.py"), encoding="utf-8").read()
        # Une porte d'entrée compare un ratio calculé à un seuil : aucune ne doit garder GAIN_MIN.
        self.assertIsNone(re.search(r"\brr\s*<\s*GAIN_MIN\b", src))
        self.assertIsNone(re.search(r"\brr\"?\]?\s*<\s*GAIN_MIN\b", src))
        self.assertIsNone(re.search(r"rr\", 0\) >= GAIN_MIN", src))
        self.assertGreaterEqual(src.count("RR_MIN_ENTREE"), 5)


if __name__ == "__main__":
    unittest.main()


class RRAttenteExplicite(unittest.TestCase):
    def test_message_radar_affiche_attente_avec_le_ratio(self):
        src = open(os.path.join(HERE, "align_bot.py"), encoding="utf-8").read()
        self.assertIn("🟡 ATTENTE — gain/risque 1:{rr:.1f} sous le minimum 1:{RR_MIN_ENTREE:g}", src)


class MargeSLNeCasseJamaisLeRatio(unittest.TestCase):
    def _cle(self):
        return {"sl_appris": {"hist": [4.0]}}

    def test_marge_qui_fait_passer_sous_1_2_est_refusee_sans_modifier_le_trade(self):
        tr = {"d": 1, "e": 100.0, "sl": 96.0, "tp1": 108.0}   # ratio 2.0 avant marge
        ok = ab.appliquer_marge_sl("NASDAQ", self._cle(), tr, {"atr": 10.0})
        self.assertFalse(ok)
        self.assertEqual(tr["sl"], 96.0)
        self.assertNotIn("marge_sl", tr)

    def test_marge_acceptee_si_le_ratio_reste_au_minimum(self):
        tr = {"d": 1, "e": 100.0, "sl": 96.0, "tp1": 120.0}   # ratio 5.0 avant marge -> 2.5 après
        ok = ab.appliquer_marge_sl("NASDAQ", self._cle(), tr, {"atr": 10.0})
        self.assertTrue(ok)
        self.assertEqual(tr["sl"], 92.0)
        self.assertGreaterEqual(tr["rr"], ab.RR_MIN_ENTREE)
