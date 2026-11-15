"""Demande d'Adel 15/11 : « la team : X TP • Y SL » sans montant, la phrase sur les profits seulement si c'est vrai."""
import os, sys, unittest, unittest.mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class Team(unittest.TestCase):
    def test_phrase_seulement_si_vraie(self):
        self.assertIn("ont couvert les SL 😉", ab.texte_team({"tp": 2, "sl": 1, "pct": 0.4}))
        self.assertNotIn("couvert", ab.texte_team({"tp": 1, "sl": 2, "pct": -0.3}))
        self.assertIn("zéro SL", ab.texte_team({"tp": 3, "sl": 0, "pct": 1.0}))
        self.assertIsNone(ab.texte_team({"tp": 0, "sl": 0, "pct": 0}))

    def test_compte_du_jour_sans_montant(self):
        etat = {}
        with unittest.mock.patch.object(ab, "live_bande", lambda *a, **k: None), unittest.mock.patch.object(ab, "TOKEN", ""):
            ab.bilan_team(etat, 0.5, now=1_800_000_000)
            t = ab.bilan_team(etat, -0.2, now=1_800_000_100)
        self.assertIn("✅ 1 TP • ❌ 1 SL", t)
        self.assertNotIn("$", t); self.assertNotIn("%", t)


if __name__ == "__main__":
    unittest.main()
