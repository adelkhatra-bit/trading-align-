"""Demande d'Adel 15/11 : TP1 touché + retour annoncé vers l'entrée → coupe tout, puis reprise à l'entrée."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab

CONTRE = [-1, -1, -1, -1, 1, 1, 1, 1, 1, 1, 1]


def r_(dirs, p, bougie15=-1, bougie5=1, t=1000):
    b15 = [dict(t=0, o=110, h=111, l=105, c=110 + 2 * bougie15, v=1), dict(t=900, o=1, h=1, l=1, c=1, v=1)]
    b5 = [dict(t=0, o=100, h=101, l=99, c=100 + bougie5, v=1), dict(t=300, o=1, h=1, l=1, c=1, v=1)]
    return dict(dirs=dirs, b15=b15, b5=b5, atr=4.0, t=t, m1=[dict(c=p)])


class Coupe(unittest.TestCase):
    def test_coupe_puis_reprise(self):
        cle, tr = {}, {"d": 1, "e": 100.0, "sl": 100.0, "sl0": 95.0, "tp1": 108.0, "tp2": 116.0, "statut": "tp1"}
        l = ab.coupe_et_reprends("GOLD", r_(CONTRE, 109), cle, tr, 109)
        self.assertTrue(any("encaisse TOUT" in x for x in l))
        self.assertIsNone(ab.coupe_et_reprends("GOLD", r_(CONTRE, 109), cle, tr, 109))   # une seule fois
        self.assertIsNone(ab.reprise_entree("GOLD", r_(CONTRE, 104), cle))              # pas encore revenu
        t = ab.reprise_entree("GOLD", r_([1] * 11, 100.5, t=2000), cle)
        self.assertIn("REPRISE À L'ENTRÉE : LONG", t); self.assertIn("SL : 95", t)
        self.assertIn("TP1 : 108", t); self.assertIn("TP2 : 116", t)
        self.assertNotIn("reprise", cle)

    def test_pas_de_coupe_si_unites_ok(self):
        tr = {"d": 1, "e": 100.0, "sl": 100.0, "tp1": 108.0, "statut": "tp1"}
        self.assertIsNone(ab.coupe_et_reprends("GOLD", r_([1] * 11, 109), {}, tr, 109))

    def test_plan_casse_pas_de_reprise(self):
        cle = {"reprise": {"d": 1, "e": 100.0, "sl": 95.0, "tp1": 108.0, "t": 0}}
        self.assertIsNone(ab.reprise_entree("GOLD", r_(CONTRE, 94), cle))
        self.assertNotIn("reprise", cle)


if __name__ == "__main__":
    unittest.main()
