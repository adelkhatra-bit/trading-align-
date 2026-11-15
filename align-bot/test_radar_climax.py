"""Radar retournement (oui radar, 15/11) : volume climax + balayage + clôture au-dessus de l'EMA9."""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def serie(baisse=True, climax=True, remonte=True):
    b = []
    p = 65000.0
    for i in range(70):
        p -= 40 if baisse else 0
        b.append(dict(t=i * 900, o=p + 20, h=p + 40, l=p - 40, c=p, v=100))
    i = 66                                             # bougie de balayage (4e avant la fin, la 70e = en formation)
    b[i].update(l=b[i]["l"] - 600, v=500 if climax else 100)
    if remonte:
        for j, c in zip(range(67, 69), (b[i]["c"] + 300, b[i]["c"] + 500)):
            b[j].update(c=c, o=c - 50, h=c + 30, l=c - 80)
    return dict(b15=b, t=70 * 900)


class Radar(unittest.TestCase):
    def test_long_prenable(self):
        cle = {}
        t = ab.radar_climax("BTC", serie(), cle)
        self.assertIn("RETOURNEMENT : LONG prenable", t); self.assertIn("Volume ×", t); self.assertIn("DYOR", t)
        self.assertIn("ne la prend pas", t)
        self.assertIsNone(ab.radar_climax("BTC", serie(), cle))      # pas de doublon dans les 2 h

    def test_sans_climax_rien(self):
        self.assertIsNone(ab.radar_climax("BTC", serie(climax=False), {}))

    def test_sans_remontee_rien(self):
        self.assertIsNone(ab.radar_climax("BTC", serie(remonte=False), {}))

    def test_pas_de_feinte_juste_apres(self):
        cle = {"radar_dernier": 1000}
        r = dict(t=1500, m1=[dict(c=1.0)])
        self.assertIsNone(ab.texte_ecran("BTC", "feinte", 1, 5, r, cle))


class RadarBranche(unittest.TestCase):
    def test_le_vrai_bot_donne_assez_de_bougies_au_radar(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "align_bot.py"), encoding="utf-8").read()
        self.assertIn("b15_long=m15[-90:]", src)                       # ≥ 66 bougies 15 min, sinon le radar est muet
        b = serie()["b15"]
        self.assertIsNotNone(ab.radar_climax("BTC", {"b15": b[-30:], "b15_long": b, "t": 70 * 900}, {}))


if __name__ == "__main__":
    unittest.main()
