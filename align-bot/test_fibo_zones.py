"""Fibonacci en temps réel (demande d'Adel 15/11) : le bot dit à quel % du mouvement on est (15 min, 1h, 4h)."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def hausse(n=48):  # de 100 à 200
    return [dict(t=i, o=100 + i * 100 / (n - 1), h=100 + i * 100 / (n - 1), l=100 + i * 100 / (n - 1), c=100 + i * 100 / (n - 1), v=1) for i in range(n)]


class Fibo(unittest.TestCase):
    def test_zone_cle_annoncee_une_fois(self):
        r = dict(b15=hausse(), b1h=[], b4h=[], m1=[dict(c=132.0)])     # 200 - 132 = 68 % du mouvement
        cle = {}
        t = ab.fibo_zones("GOLD", r, cle)
        self.assertIn("ZONE FIBONACCI", t); self.assertIn("Fibo 15 min : on est à 68 %", t); self.assertIn("hausse", t)
        self.assertIn("DYOR", t)
        self.assertIsNone(ab.fibo_zones("GOLD", r, cle))

    def test_hors_zone_rien(self):
        self.assertIsNone(ab.fibo_zones("GOLD", dict(b15=hausse(), m1=[dict(c=180.0)]), {}))   # 20 %


if __name__ == "__main__":
    unittest.main()
