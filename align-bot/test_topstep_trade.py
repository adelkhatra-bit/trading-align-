import datetime, unittest, unittest.mock
from zoneinfo import ZoneInfo
import topstep_trade as ts

CHI = ZoneInfo("America/Chicago")


def a(j, h, mi):  # jour de novembre 2026 (16 = lundi), heure de Chicago
    return datetime.datetime(2026, 11, j, h, mi, tzinfo=CHI)


class TestPhases(unittest.TestCase):
    def test_journee_ouverte(self):
        self.assertEqual(ts.phase(a(17, 10, 0)), "ouvert")

    def test_annonce_1h_puis_10min(self):
        self.assertEqual(ts.phase(a(17, 13, 30)), "annonce_1h")
        self.assertEqual(ts.phase(a(17, 14, 5)), "annonce_10min")

    def test_fermeture_1h_avant_la_limite(self):
        self.assertEqual(ts.phase(a(17, 14, 10)), "fermeture")
        self.assertEqual(ts.phase(a(17, 15, 30)), "ferme")
        self.assertEqual(ts.phase(a(17, 17, 5)), "ouvert")

    def test_week_end(self):
        self.assertEqual(ts.phase(a(20, 15, 30)), "ferme")   # vendredi après la limite
        self.assertEqual(ts.phase(a(21, 12, 0)), "ferme")    # samedi
        self.assertEqual(ts.phase(a(22, 17, 30)), "ouvert")  # dimanche soir

    def test_annonces_une_seule_fois(self):
        etat = {}
        self.assertEqual(ts.annonces(etat, a(17, 13, 30))[0]["type"], "annonce_1h")
        self.assertEqual(ts.annonces(etat, a(17, 13, 40)), [])
        self.assertEqual(ts.annonces(etat, a(17, 14, 5))[0]["type"], "annonce_10min")
        ts.annonces(etat, a(17, 14, 20))
        self.assertEqual(ts.annonces(etat, a(17, 17, 10))[0]["type"], "reouverture")

    def test_bande_sans_prix_ni_telegram(self):
        for t in ts.BANDE.values():
            self.assertNotIn("Telegram", t)
            self.assertFalse(any(ch.isdigit() and t[i + 1:i + 2].isdigit() and t[i + 2:i + 3].isdigit() for i, ch in enumerate(t)))


class TestRisque(unittest.TestCase):
    def test_sl_plafonne_a_75_dollars(self):
        # MNQ : tick 0,25 = 0,5 $ → 75 $ max = 150 ticks
        self.assertEqual(ts.ticks(500, 0.25, 0.5), 150)
        self.assertEqual(ts.ticks(10, 0.25, 0.5), 50)   # 10 pts ×1,25 = 12,5 pts = 50 ticks

    def test_garde_fou_jour_et_plancher(self):
        etat = {}
        with unittest.mock.patch.object(ts, "PLANCHER", 97649.8):
            self.assertFalse(ts.garde_fou(etat, 97700)[0])
        etat = {}
        self.assertTrue(ts.garde_fou(etat, 50000)[0])
        self.assertFalse(ts.garde_fou(etat, 49840)[0])

    def test_pas_de_position_pres_de_la_fermeture(self):
        with unittest.mock.patch.object(ts, "phase", return_value="annonce_10min"):
            r = ts.executer({"auto_marches": {"NASDAQ": True}}, {"marche": "NASDAQ", "sens": "LONG", "e": 1, "sl": 0, "tp": 2})
        self.assertFalse(r["ok"])

    def test_marche_eteint(self):
        r = ts.executer({}, {"marche": "GOLD", "sens": "LONG", "e": 1, "sl": 0, "tp": 2})
        self.assertFalse(r["ok"])


class TestGestion(unittest.TestCase):
    """Demande d'Adel (15/11) : sur Topstep, TP1 → 50 % coupés + SL à BE, puis TP2 ; ou 1 contrat gardé avec SL à BE."""
    def pos(self, n=2):
        return {"topstep_pos": {"marche": "NASDAQ", "d": 1, "n": n, "etape": 0, "contractId": "X", "tick": 0.25,
                                "e": 100.0, "sl": 90.0, "tp1": 110.0, "tp2": 120.0, "test": True}}

    def test_deux_contrats_si_le_risque_tient(self):
        self.assertEqual(ts.nb_contrats(50, 0.5), 2)     # 2 × 25 $ = 50 $ ≤ 75 $
        self.assertEqual(ts.nb_contrats(100, 0.5), 1)    # 2 × 50 $ = 100 $ > 75 $

    def test_tp1_puis_be_puis_tp2(self):
        etat = self.pos()
        self.assertEqual(ts.gerer(etat, 105, journal=lambda *_: None), [])
        m = ts.gerer(etat, 110.5, journal=lambda *_: None)
        self.assertIn("50 %", m[0]); self.assertIn("BE", m[0])
        self.assertEqual(etat["topstep_pos"]["sl"], 100.0)
        m = ts.gerer(etat, 120, journal=lambda *_: None)
        self.assertIn("TP2", m[0]); self.assertNotIn("topstep_pos", etat)

    def test_un_contrat_garde_avec_be(self):
        etat = self.pos(1)
        m = ts.gerer(etat, 111, journal=lambda *_: None)
        self.assertNotIn("50 %", m[0]); self.assertIn("BE", m[0])
        m = ts.gerer(etat, 99.5, journal=lambda *_: None)
        self.assertIn("BE touché", m[0]); self.assertNotIn("topstep_pos", etat)

    def test_sl_touche(self):
        etat = self.pos()
        self.assertIn("SL touché", ts.gerer(etat, 89, journal=lambda *_: None)[0])


if __name__ == "__main__":
    unittest.main()
