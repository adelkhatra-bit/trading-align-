"""Entrée sur retest (règle d'Adel 15/11) : résistance cassée à la clôture → support, le marché bloque → entrée, SL sous la mèche."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab

UP = [1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1]


def serie(retest=True):
    b = [dict(t=i * 900, o=99, h=100.0, l=98, c=99, v=1) for i in range(30)]
    for i in range(25, 29):                                 # cassure à la clôture au-dessus de 100
        b[i].update(o=100.5, h=103, l=100.2, c=102)
    b[29] = dict(t=29 * 900, o=100.4, h=101.5, l=99.9 if retest else 101.0, c=101.2, v=1)   # retour sur 100 puis clôture au-dessus
    b.append(dict(t=30 * 900, o=101.2, h=101.3, l=101.1, c=101.2, v=1))                   # en formation
    return dict(b15=b, dirs=UP, atr=2.0, atr5=2.0,
                 b5=[dict(t=0, o=101.2, h=102.0, l=100.5, c=101.2), dict(t=300, o=101.2, h=102.0, l=100.5, c=101.2)],
                 m1=[dict(t=int(__import__("time").time()), o=101.2, h=101.2, l=101.2, c=101.2)],
                 grosses=[(105.0, "4h"), (110.0, "Daily")], t=30 * 900)


class Retest(unittest.TestCase):
    def test_long_propose(self):
        cle = {}
        t = ab.entree_retest("GOLD", serie(), cle)
        self.assertIn("ENTRÉE POSSIBLE SUR RETEST : LONG", t); self.assertIn("devient support", t)
        self.assertIn("TP1 :", t); self.assertIn("TP2 :", t); self.assertIn("Gain/risque", t)
        self.assertIn("SL : 99,70", t); self.assertIn("DYOR", t)
        self.assertIsNone(ab.entree_retest("GOLD", serie(), cle))

    def test_pas_de_retest_rien(self):
        self.assertIsNone(ab.entree_retest("GOLD", serie(retest=False), {}))

    def test_unites_pas_d_accord_rien(self):
        r = serie(); r["dirs"] = [1, 1, 1, 0, 1, 0, 0, -1, 0, 1, 1]
        self.assertIsNone(ab.entree_retest("GOLD", r, {}))


if __name__ == "__main__":
    unittest.main()
