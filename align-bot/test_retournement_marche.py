import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def bar(t, c, h=None, l=None, v=100):
    return dict(t=t, o=c, h=h if h is not None else c + 1, l=l if l is not None else c - 1, c=c, v=v)


def r_(dirs, vol_dernier=100, prix=100.0):
    b5 = [bar(i * 300, 100 - (i % 3)) for i in range(20)]
    b15 = [bar(i * 900, 100) for i in range(50)]
    b15[-2]["v"] = vol_dernier
    b1 = [bar(i * 3600, 100, h=110, l=90) for i in range(10)]
    b4 = [bar(i * 14400, 100, h=130, l=70) for i in range(10)]
    return dict(dirs=dirs, b5=b5, b15=b15, b15_long=b15, b1h=b1, b4h=b4, m1=[bar(0, prix)], t=10000)


LONG_GOLD = [1, 1, 1, 0, 1, 0, -1, -1, -1, -1, -1]
LONG_BTC  = [1, 1, 1, 0, 1, 1, 1, 1, -1, -1, -1]


class RetournementParMarche(unittest.TestCase):
    def test_gold_contre_h1_h4_est_une_observation_sans_niveaux(self):
        cle = {}
        t = ab.retournement_marche("GOLD", r_(LONG_GOLD), cle)
        self.assertIn("RETOURNEMENT EN OBSERVATION", t)
        self.assertIn("H1 est baissier et H4 baissier", t)
        self.assertIn("PAS DE POSITION", t)
        self.assertNotIn("Entrée", t)
        self.assertNotIn("SL :", t)
        self.assertNotIn("TP", t)
        self.assertIsNone(ab.retournement_marche("GOLD", r_(LONG_GOLD), cle))

    def test_gold_rearme_apres_confirmation_ou_fin_du_mouvement(self):
        cle = {}
        self.assertIsNotNone(ab.retournement_marche("GOLD", r_(LONG_GOLD), cle))
        dirs = list(LONG_GOLD); dirs[7] = dirs[9] = 1
        self.assertIsNone(ab.retournement_marche("GOLD", r_(dirs), cle))
        self.assertEqual(cle["rv_watch_sens"], 0)

    def test_nasdaq_garde_le_filtre_volume_et_ne_propose_pas_de_position_inverse(self):
        self.assertIsNone(ab.retournement_marche("NASDAQ", r_(LONG_GOLD, vol_dernier=100), {}))
        t = ab.retournement_marche("NASDAQ", r_(LONG_GOLD, vol_dernier=500), {})
        self.assertIn("RETOURNEMENT EN OBSERVATION", t)
        self.assertIn("Volume M15", t)
        self.assertIn("PAS DE POSITION", t)
        self.assertNotIn("Entrée", t)

    def test_btc_garde_exactement_le_signal_historique(self):
        self.assertIsNone(ab.retournement_marche("BTC", r_(LONG_GOLD), {}))
        t = ab.retournement_marche("BTC", r_(LONG_BTC), {})
        self.assertIn("RETOURNEMENT LONG", t)
        self.assertIn("le 1h a suivi", t)
        self.assertIn("Cible 1", t)
        self.assertIn("mets-toi à BE", t)

    def test_short_gold_est_egalement_une_observation(self):
        t = ab.retournement_marche("GOLD", r_([-x for x in LONG_GOLD]), {})
        self.assertIn("RETOURNEMENT EN OBSERVATION", t)
        self.assertIn("à la baisse", t)
        self.assertIn("PAS DE POSITION", t)


if __name__ == "__main__":
    unittest.main()
