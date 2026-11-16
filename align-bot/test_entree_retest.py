"""Entrée sur retest (règle d'Adel 15/11) : résistance cassée à la clôture → support, le marché bloque → entrée, SL sous la mèche."""
import os, sys, unittest, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab

UP = [1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1]


def serie(retest=True):
    now = int(time.time())
    b = [dict(t=now - (30 - i) * 900, o=99, h=100.0, l=98, c=99, v=1) for i in range(30)]
    for i in range(25, 29):
        b[i].update(o=100.5, h=103, l=100.2, c=102)
    b[29] = dict(t=now - 900, o=100.4, h=101.5, l=99.9 if retest else 101.0, c=101.2, v=1)
    b.append(dict(t=now, o=101.2, h=101.3, l=101.1, c=101.2, v=1))
    return dict(b15=b, b5=[dict(t=now-600,o=101,h=102,l=100,c=101.2,v=1),dict(t=now-300,o=101.2,h=101.3,l=101.1,c=101.2,v=1)],
                b1h=[dict(t=now-7200,o=100,h=101,l=99,c=100,v=1),dict(t=now-3600,o=100,h=101,l=99,c=100,v=1)],
                b4h=[dict(t=now-28800,o=100,h=101,l=99,c=100,v=1),dict(t=now-14400,o=100,h=101,l=99,c=100,v=1)],
                m1=[dict(t=now-30,o=101.2,h=101.3,l=101.1,c=101.2,v=1)], dirs=UP, dirs_cloturees=UP,
                r5=[50,50,50], grosses=[(110.0,"4h"),(120.0,"Daily")], atr=2.0, atr5=1.0, t=now)


class Retest(unittest.TestCase):
    def test_long_propose(self):
        cle = {}
        t = ab.entree_retest("GOLD", serie(), cle)
        self.assertIn("ENTRÉE POSSIBLE SUR RETEST : LONG", t); self.assertIn("devient support", t)
        self.assertIn("SL : 99,70", t); self.assertIn("DYOR", t)
        self.assertIsNone(ab.entree_retest("GOLD", serie(), cle))

    def test_pas_de_retest_rien(self):
        self.assertIsNone(ab.entree_retest("GOLD", serie(retest=False), {}))

    def test_unites_pas_d_accord_rien(self):
        r = serie(); r["dirs"] = [1, 1, 1, 0, 1, 0, 0, -1, 0, 1, 1]
        self.assertIsNone(ab.entree_retest("GOLD", r, {}))


if __name__ == "__main__":
    unittest.main()
