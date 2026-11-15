"""Demande d'Adel 15/11 : boutons admin pour allumer / éteindre chaque marché, tout arrêter, tout relancer."""
import json, os, sys, unittest, unittest.mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class AdminAuto(unittest.TestCase):
    def test_boutons_et_stop_go(self):
        etat, vus = {}, []
        with unittest.mock.patch.object(ab, "_envoi_sur", lambda c, **k: vus.append(k)):
            ab.commande_auto(etat, 1, "/auto_go")
            self.assertTrue(all(etat["auto_marches"][m] for m in ab.AUTO_MARCHES))
            ab.commande_auto(etat, 1, "/auto_stop")
            self.assertFalse(any(etat["auto_marches"][m] for m in ab.AUTO_MARCHES))
            ab.commande_auto(etat, 1, "/auto_btc")
            self.assertTrue(etat["auto_marches"]["BTC"])
        cb = [b["callback_data"] for r in json.loads(vus[-1]["reply_markup"])["inline_keyboard"] for b in r]
        self.assertIn("auto:stop", cb); self.assertIn("auto:go", cb); self.assertIn("auto:BTC", cb)
        self.assertIn("TEST", vus[-1]["text"])


if __name__ == "__main__":
    unittest.main()
