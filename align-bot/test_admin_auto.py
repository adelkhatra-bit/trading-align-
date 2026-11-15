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
        self.assertIn("autoadm:stop", cb); self.assertIn("autoadm:go", cb); self.assertIn("autoadm:BTC", cb)
        self.assertNotIn("auto:BTC", cb)     # jamais le même bouton que le « Coach : préviens-moi » des abonnés
        self.assertIn("TEST", vus[-1]["text"])

    def test_bouton_admin_dans_mon_bot_pour_le_proprio_seulement(self):
        vus = []
        with unittest.mock.patch.object(ab, "_envoi_sur", lambda c, **k: vus.append(k)), \
             unittest.mock.patch.object(ab, "proprio", return_value=[7]), unittest.mock.patch.object(ab, "vue_gratuite", return_value=False):
            ab.menu_bot({}, 7)
            ab.menu_bot({}, 8)
        cb = lambda k: [b.get("callback_data") for r in json.loads(k["reply_markup"])["inline_keyboard"] for b in r]
        self.assertIn("autoadm:menu", cb(vus[0])); self.assertNotIn("autoadm:menu", cb(vus[1]))


if __name__ == "__main__":
    unittest.main()
