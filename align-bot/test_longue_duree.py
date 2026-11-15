"""Demande d'Adel 15/11 : position de plusieurs jours → message à part (CFD on garde, Topstep on ferme) + tapote / partage / cadeau."""
import os, sys, unittest, unittest.mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def r_(taille):
    return {"m1": [{"h": 100 + taille, "l": 100, "c": 100} for _ in range(60)]}


class Longue(unittest.TestCase):
    def test_longue_une_fois(self):
        etat, envoyes = {"canaux_marche": {"GOLD": -1}}, []
        tr = {"e": 100.0, "tp1": 130.0}                       # 30 / 0,5 = 60 → 0,5 × 3600 = 1800 min
        with unittest.mock.patch.object(ab, "TOKEN", "x"), unittest.mock.patch.object(ab, "_envoi_sur", lambda c, **k: envoyes.append(k["text"])), \
             unittest.mock.patch.object(ab, "live_bande", lambda *a, **k: None):
            self.assertTrue(ab.message_longue_duree(etat, "GOLD", tr, r_(0.5)))
            self.assertFalse(ab.message_longue_duree(etat, "GOLD", tr, r_(0.5)))
        self.assertIn("FundedNext / FTMO", envoyes[0]); self.assertIn("Topstep", envoyes[0]); self.assertIn("cadeau", envoyes[0])

    def test_courte_rien(self):
        self.assertFalse(ab.message_longue_duree({}, "GOLD", {"e": 100.0, "tp1": 101.0}, r_(0.5)))


if __name__ == "__main__":
    unittest.main()
