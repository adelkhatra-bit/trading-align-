"""Régression Fibonacci Telegram : Gold/NASDAQ commentés une fois à l'entrée de zone ; BTC inchangé."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def hausse(n=48, top=200.0):
    return [dict(t=i, o=100 + i * (top - 100) / (n - 1),
                 h=100 + i * (top - 100) / (n - 1),
                 l=100 + i * (top - 100) / (n - 1),
                 c=100 + i * (top - 100) / (n - 1), v=1) for i in range(n)]


class FiboTelegram(unittest.TestCase):
    def test_gold_annonce_la_zone_15m_une_fois(self):
        r = dict(b15_fibo=hausse(), b1h_fibo=[], b4h_fibo=[], m1=[dict(c=132.0)])
        cle = {}
        t = ab.fibo_zones("GOLD", r, cle)
        self.assertIn("ZONE FIBONACCI", t)
        self.assertIn("Fibo 15 min : on est à 68 %", t)
        self.assertIn("hausse", t)
        self.assertIsNone(ab.fibo_zones("GOLD", r, cle))

    def test_nouvel_extreme_dans_la_meme_zone_ne_repete_pas_le_message(self):
        b = hausse()
        r = dict(b15_fibo=b, b1h_fibo=[], b4h_fibo=[], m1=[dict(c=132.0)])
        cle = {}
        self.assertIsNotNone(ab.fibo_zones("NASDAQ", r, cle))
        b2 = hausse(top=202.0)
        r["b15_fibo"] = b2
        self.assertIsNone(ab.fibo_zones("NASDAQ", r, cle))

    def test_sortie_puis_reentree_dans_la_zone_rearme_une_annonce(self):
        r = dict(b15_fibo=hausse(), b1h_fibo=[], b4h_fibo=[], m1=[dict(c=132.0)])
        cle = {}
        self.assertIsNotNone(ab.fibo_zones("GOLD", r, cle))
        r["m1"] = [dict(c=180.0)]  # retracement hors zone
        self.assertIsNone(ab.fibo_zones("GOLD", r, cle))
        r["m1"] = [dict(c=132.0)]
        self.assertIsNotNone(ab.fibo_zones("GOLD", r, cle))

    def test_une_heure_utilise_bien_48_bougies(self):
        r = dict(b15_fibo=[], b1h_fibo=hausse(), b4h_fibo=[], m1=[dict(c=132.0)])
        t = ab.fibo_zones("GOLD", r, {})
        self.assertIn("Fibo 1h : on est à 68 %", t)

    def test_donnees_incompletes_ne_declenchent_pas_de_fausse_zone(self):
        r = dict(b15_fibo=hausse(47), b1h_fibo=[], b4h_fibo=[], m1=[dict(c=132.0)])
        self.assertIsNone(ab.fibo_zones("GOLD", r, {}))

    def test_btc_garde_le_comportement_historique(self):
        r = dict(b15=hausse(), b1h=[], b4h=[], m1=[dict(c=132.0)])
        t = ab.fibo_zones("BTC", r, {})
        self.assertIn("Fibo 15 min : on est à 68 %", t)

    def test_calculer_analyse_expose_les_fenetres_completes_gold_nasdaq(self):
        def series(n, step):
            return [dict(t=i * step, o=100+i*0.01, h=100.5+i*0.01,
                         l=99.5+i*0.01, c=100+i*0.01, v=100) for i in range(n)]
        s = dict(m1=series(600, 60), m5=series(120, 300), m15=series(150, 900),
                 m30=series(60, 1800), h1=series(100, 3600), h4=series(60, 14400),
                 d1=series(60, 86400), w1=series(60, 604800))
        r = ab.calculer_analyse(s)
        self.assertEqual(len(r["b15_fibo"]), 48)
        self.assertEqual(len(r["b1h_fibo"]), 48)
        self.assertEqual(len(r["b4h_fibo"]), 30)


if __name__ == "__main__":
    unittest.main()
