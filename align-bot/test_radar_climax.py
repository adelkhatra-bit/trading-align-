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


class RetournementPrecocePetitesUnites(unittest.TestCase):
    def test_micro_reversal_emits_long_then_short_watch_without_entries(self):
        dirs = [0] * 11
        dirs[2], dirs[4], dirs[7], dirs[9] = 1, -1, -1, -1
        r = {"retHaut": True, "retBas": False, "dirs_cloturees": dirs,
             "b15": [{"t": 12345}]}
        cle = {}
        long_msg = ab.alerte_retournement_micro("GOLD", r, cle)
        self.assertIn("PRÉ-ALERTE RETOURNEMENT LONG", long_msg)
        self.assertIn("aucune position", long_msg.lower())
        self.assertIn("H4", long_msg)
        self.assertIsNone(ab.alerte_retournement_micro("GOLD", r, cle))

        r["retHaut"] = False
        self.assertIsNone(ab.alerte_retournement_micro("GOLD", r, cle))
        r["retBas"] = True
        short_msg = ab.alerte_retournement_micro("GOLD", r, cle)
        self.assertIn("PRÉ-ALERTE RETOURNEMENT SHORT", short_msg)
        self.assertIn("aucune position", short_msg.lower())

    def test_early_radar_watch_does_not_consume_confirmed_cooldown(self):
        r = serie()
        r["b15_long"] = r["b15"]
        r["dirs"] = [0] * 11
        r["dirs_cloturees"] = [0] * 11
        r["grosses"] = [(63000.0, "4h")]
        cle = {}
        watch = ab.radar_climax("GOLD", r, cle)
        self.assertIn("SURVEILLANCE", watch)
        self.assertIn("SCÉNARIO LONG", watch)
        self.assertNotIn("radar_t", cle)

        r["dirs"] = [1] * 11
        r["dirs_cloturees"] = [1] * 11
        with unittest.mock.patch.object(ab, "direction_confirmee_marche", return_value=1), \\
             unittest.mock.patch.object(
                 ab, "objectifs",
                 side_effect=lambda market, sens, entry, risk:
                    ((entry + sens * 2 * risk, "TP1"), (entry + sens * 3 * risk, "TP2"))
             ):
            confirmed = ab.radar_climax("GOLD", r, cle)
        self.assertIn("RETOURNEMENT CONFIRMÉ — LONG", confirmed)
        self.assertEqual(cle["radar_t"]["1"], r["t"])


