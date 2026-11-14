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


class RebondSurLigne(unittest.TestCase):
    def test_rebond_tp_rassure(self):
        r = {"m1": [{"c": 95.5}], "b15": [{"t": i, "o": 100, "h": 101, "l": 99, "c": 100} for i in range(10)]}
        t = ab.texte_ecran("BTC", "rebond", 1, 0, r, {}, "TP1")
        self.assertIn("REBOND sur le TP1", t)
        self.assertIn("Pas de panique", t)
        self.assertIsNone(ab.texte_ecran("BTC", "rebond", 1, 0, r, {}, "XYZ"))


if __name__ == "__main__":
    unittest.main()


class RisqueFrEn(unittest.TestCase):
    def test_message_trading_rappelle_le_risque(self):
        t = ab.avec_risque("🔴 SHORT BTC\nSL au-dessus")
        self.assertIn("pas un conseil en investissement", t); self.assertIn("DYOR", t)
        self.assertIn("not financial advice", t)
        self.assertEqual(ab.avec_risque(t), t)                 # jamais deux fois

    def test_message_neutre_inchange(self):
        self.assertEqual(ab.avec_risque("⬇️ Tes boutons sont là 👇"), "⬇️ Tes boutons sont là 👇")


class UneAnnonceParQuart(unittest.TestCase):
    def test_pression_une_seule_fois_par_quart_d_heure(self):
        envois = []
        r = {"m1": [{"c": 95.5}], "b15": [{"t": i, "o": 100, "h": 101, "l": 99, "c": 100} for i in range(10)]}
        with mock.patch.object(ab, "ecran_lire", return_value=["EVT|BTC|pression|-1|9", "EVT|BTC|pression|-1|7"]), \
             mock.patch.dict(ab.DERNIERS, {"BTC": r}), mock.patch.object(ab.time, "time", return_value=900 * 5000 + 10), \
             mock.patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: envois.append(k["text"])), \
             mock.patch.object(ab, "boutons_chaine_marche", return_value='{"inline_keyboard": []}'):
            ab.ecran_vers_telegram({"canaux_marche": {"BTC": -5}})
        self.assertEqual(len(envois), 1)

    def test_respire_rassure(self):
        r = {"m1": [{"c": 95.5}], "b15": [{"t": i, "o": 100, "h": 101, "l": 99, "c": 100} for i in range(10)]}
        t = ab.texte_ecran("BTC", "respire", -1, 0, r, {})
        self.assertIn("le marché respire", t)
        self.assertIn("pas de panique", t)


class Feinte(unittest.TestCase):
    def test_feinte_explique_le_piege(self):
        r = {"m1": [{"c": 95.5}], "b15": [{"t": i, "o": 100, "h": 101, "l": 99, "c": 100} for i in range(10)]}
        t = ab.texte_ecran("BTC", "feinte", -1, 6, r, {})
        self.assertIn("FEINTE", t)
        self.assertIn("Ne cours pas après ce rebond", t)
        self.assertIn("dans 6 min", t)
