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
