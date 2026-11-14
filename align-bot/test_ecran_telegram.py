import unittest
from unittest import mock
import align_bot as ab


class EcranVersTelegram(unittest.TestCase):
    def r(self):
        b = [{"t": i, "o": 100, "h": 101 + i, "l": 99 - i, "c": 100} for i in range(10)]
        return {"m1": [{"c": 95.5}], "b15": b}

    def test_message_detaille_couleur_et_sans_plan(self):
        t = ab.texte_ecran("BTC", "pression", -1, 7, self.r(), {})
        self.assertIn("🔴 GROSSE DISTRIBUTION", t)
        self.assertIn("dans 7 min", t)
        self.assertIn("Dernier plus bas 15 min", t)
        self.assertIn("pas une entrée", t.lower().replace("ce n'est ", ""))
        self.assertNotIn("Telegram", t)

    def test_publie_dans_la_chaine_une_fois(self):
        envois = []
        etat = {"canaux_marche": {"BTC": -5}}
        with mock.patch.object(ab, "ecran_lire", return_value=["EVT|BTC|manip|1|4", "EVT|BTC|manip|1|4", "n'importe quoi"]), \
             mock.patch.dict(ab.DERNIERS, {"BTC": self.r()}), \
             mock.patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: envois.append((c, k["text"]))), \
             mock.patch.object(ab, "boutons_chaine_marche", return_value='{"inline_keyboard": []}'):
            ab._LIVE_DERNIER.pop("ecranBTCmanip1", None)
            ab.ecran_vers_telegram(etat)
        self.assertEqual(len(envois), 1)
        self.assertEqual(envois[0][0], -5)
        self.assertIn("🟢 MANIPULATION", envois[0][1])
        self.assertIn("En savoir plus", envois[0][1])
        self.assertIn("Dernier plus haut", etat["ecran_detail"]["BTC"])


if __name__ == "__main__":
    unittest.main()
