"""Demande d'Adel 15/11 : après un TP, le parrainage revient dans la chaîne avec les boutons (au plus toutes les 3 h)."""
import json, os, sys, unittest, unittest.mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class PromoTP(unittest.TestCase):
    def test_une_fois_toutes_les_3h(self):
        etat, envoyes = {"canaux_marche": {"BTC": -100}}, []
        with unittest.mock.patch.object(ab, "TOKEN", "x"), \
             unittest.mock.patch.object(ab, "_envoi_sur", lambda cid, **k: envoyes.append(k)):
            self.assertTrue(ab.promo_apres_tp(etat, "BTC", now=1000))
            self.assertFalse(ab.promo_apres_tp(etat, "BTC", now=2000))
            self.assertTrue(ab.promo_apres_tp(etat, "BTC", now=1000 + 3 * 3600))
        self.assertIn("DÉMO", envoyes[0]["text"]); self.assertIn(ab.FUNDEDNEXT_CODE, envoyes[0]["text"])
        boutons = [b["text"] for r in json.loads(envoyes[0]["reply_markup"])["inline_keyboard"] for b in r]
        self.assertIn("🏦 Topstep -15 %", boutons)


if __name__ == "__main__":
    unittest.main()
