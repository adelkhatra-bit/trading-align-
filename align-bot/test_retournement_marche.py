import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def bar(t, c, h=None, l=None, v=100):
    return dict(t=t, o=c, h=h if h is not None else c + 1, l=l if l is not None else c - 1, c=c, v=v)


def r_(dirs, vol_dernier=100, prix=100.0):
    b5 = [bar(i * 300, 100 - (i % 3)) for i in range(20)]
    b15 = [bar(i * 900, 100) for i in range(50)]
    b15[-1]["v"] = vol_dernier
    b1 = [bar(i * 3600, 100, h=110, l=90) for i in range(10)]
    b4 = [bar(i * 14400, 100, h=130, l=70) for i in range(10)]
    return dict(dirs=dirs, b5=b5, b15=b15, b1h=b1, b4h=b4, m1=[bar(0, prix)], t=10000)


#        1m 3m 5m 10m 15m 30m 45m 1h 2h 4h D
LONG_GOLD = [1, 1, 1, 0, 1, 0, -1, -1, -1, -1, -1]
LONG_BTC  = [1, 1, 1, 0, 1, 1, 1, 1, -1, -1, -1]


class RetournementParMarche(unittest.TestCase):
    def test_gold_contre_h1_h4_est_une_observation_pas_une_position(self):
        cle = {}
        t = ab.retournement_marche("GOLD", r_(LONG_GOLD), cle)
        self.assertIn("RETOURNEMENT EN OBSERVATION", t)
        self.assertIn("PAS DE POSITION", t)
        self.assertIn("H1 reste baissier et H4 baissier", t)
        self.assertNotIn("Entrée ≈", t)
        self.assertNotIn("Cible 1", t)
        self.assertNotIn("TP1", t)
        self.assertIsNone(ab.retournement_marche("GOLD", r_(LONG_GOLD), cle))

    def test_only_explicitly_forming_bars_are_excluded(self):
        base = r_(LONG_GOLD)
        expected = ab.retournement_marche("GOLD", base, {})
        live = r_(LONG_GOLD)
        for key in ("b5", "b15", "b1h", "b4h"):
            last = dict(live[key][-1])
            last.update(t=last["t"] + 999999, h=999.0, l=1.0, forming=True)
            live[key] = live[key] + [last]
        self.assertEqual(ab.retournement_marche("GOLD", live, {}), expected)

    def test_gold_ne_declenche_plus_de_veille_si_h1_h4_ont_confirme(self):
        dirs = list(LONG_GOLD)
        dirs[7], dirs[9] = 1, 1
        self.assertIsNone(ab.retournement_marche("GOLD", r_(dirs), {}))

    def test_btc_garde_sa_regle_historique(self):
        self.assertIsNone(ab.retournement_marche("BTC", r_(LONG_GOLD), {}))
        t = ab.retournement_marche("BTC", r_(LONG_BTC), {})
        self.assertIn("le 1h a suivi", t)
        self.assertIn("Cible 1", t)

    def test_btc_reversal_uses_closed_higher_timeframe_readings(self):
        r = r_(LONG_BTC)
        r["dirs"] = list(LONG_BTC)
        r["dirs_cloturees"] = list(LONG_GOLD)  # H1/H4 clôturées restent baissières
        self.assertIsNone(ab.retournement_marche("BTC", r, {}))
        r["dirs_cloturees"] = list(LONG_BTC)  # H1 clôturée confirme le retournement, H4 reste contre
        msg = ab.retournement_marche("BTC", r, {})
        self.assertIn("le 1h a suivi", msg)

    def test_nasdaq_demande_du_volume_et_ne_donne_pas_de_position_inverse(self):
        self.assertIsNone(ab.retournement_marche("NASDAQ", r_(LONG_GOLD, vol_dernier=100), {}))
        t = ab.retournement_marche("NASDAQ", r_(LONG_GOLD, vol_dernier=500), {})
        self.assertIn("RETOURNEMENT EN OBSERVATION", t)
        self.assertIn("PAS DE POSITION", t)
        self.assertNotIn("Entrée ≈", t)

    def test_short_symetrique_reste_une_observation(self):
        t = ab.retournement_marche("GOLD", r_([-x for x in LONG_GOLD]), {})
        self.assertIn("RETOURNEMENT EN OBSERVATION", t)
        self.assertIn("à la baisse", t)
        self.assertIn("PAS DE POSITION", t)

    def test_cible_deja_depassee(self):
        self.assertIsNone(ab.retournement_marche("GOLD", r_(LONG_GOLD, prix=115.0), {}))


if __name__ == "__main__":
    unittest.main()
