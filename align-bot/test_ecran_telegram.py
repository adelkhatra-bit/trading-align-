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
        self.assertIn("Dernier support 15 min", t)
        self.assertIn("pas une entrée", t.lower().replace("ce n'est ", ""))
        self.assertNotIn("Telegram", t)

    def test_publie_dans_la_chaine_une_fois(self):
        envois = []
        etat = {"canaux_marche": {"BTC": -5}}
        with mock.patch.object(ab, "ecran_lire", return_value=["EVT|BTC|manip|1|4", "EVT|BTC|manip|1|4", "n'importe quoi"]), \
             mock.patch.dict(ab.DERNIERS, {"BTC": self.r()}), \
             mock.patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: envois.append((c, k["text"])) or {"ok": True}), \
             mock.patch.object(ab, "boutons_chaine_marche", return_value='{"inline_keyboard": []}'):
            ab._LIVE_DERNIER.pop("ecranBTCmanip1", None)
            ab.ecran_vers_telegram(etat)
        self.assertEqual(len(envois), 1)
        self.assertEqual(envois[0][0], -5)
        self.assertIn("🟢 MANIPULATION", envois[0][1])
        self.assertIn("En savoir plus", envois[0][1])
        self.assertIn("Dernière résistance", etat["ecran_detail"]["BTC"])


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
             mock.patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: envois.append(k["text"]) or {"ok": True}), \
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


class DirectionZonesSpectacle(unittest.TestCase):
    def test_zone_basse_est_un_scenario_haussier(self):
        texte = ab.texte_ecran("GOLD", "zone", 1, 0, {
            "m1": [{"c": 100}], "b15": []
        }, {}, "FVG")
        self.assertIn("SCÉNARIO HAUSSIER", texte)
        self.assertIn("Fair Value Gap", texte)
        self.assertIn("support", texte.lower())
        self.assertNotIn("SCÉNARIO BAISSIER", texte)

    def test_zone_haute_est_un_scenario_baissier(self):
        texte = ab.texte_ecran("GOLD", "zone", -1, 0, {
            "m1": [{"c": 100}], "b15": []
        }, {}, "OB")
        self.assertIn("SCÉNARIO BAISSIER", texte)
        self.assertIn("Order Block", texte)
        self.assertIn("résistance", texte.lower())
        self.assertNotIn("SCÉNARIO HAUSSIER", texte)

    def test_fvg_neutre_ne_devient_pas_un_long_ou_short(self):
        texte = ab.texte_ecran("GOLD", "zone", 0, 0, {
            "m1": [{"c": 100}], "b15": []
        }, {}, "FVG")
        self.assertIn("BIAIS NON DÉFINI", texte)
        self.assertNotIn("SCÉNARIO HAUSSIER", texte)
        self.assertNotIn("SCÉNARIO BAISSIER", texte)


class LivraisonEvenementLive(unittest.TestCase):
    def test_absence_de_chaine_ne_fait_pas_avancer_le_curseur(self):
        etat = {"ecran_id": "ancien"}
        evenement = {"id": "nouvel-id", "message": "EVT|BTC|acc|1|5"}
        with mock.patch.object(ab, "ecran_lire", return_value=[evenement]), \\
             mock.patch.dict(ab.DERNIERS, {"BTC": {"m1": [{"c": 100}], "b15": []}}):
            ab.ecran_vers_telegram(etat)
        self.assertEqual(etat["ecran_id"], "ancien")

    def test_echec_telegram_ne_consomme_pas_levenement(self):
        etat = {"ecran_id": "ancien", "canaux_marche": {"BTC": "-5"}}
        evenement = {"id": "a-retenter", "message": "EVT|BTC|casse|1|5"}
        with mock.patch.object(ab, "ecran_lire", return_value=[evenement]), \\
             mock.patch.dict(ab.DERNIERS, {"BTC": {"m1": [{"c": 100}], "b15": []}}), \\
             mock.patch.object(ab, "_envoi_sur", return_value={"ok": False}), \\
             mock.patch.object(ab, "boutons_chaine_marche", return_value='{"inline_keyboard": []}'):
            ab.ecran_vers_telegram(etat)
        self.assertEqual(etat["ecran_id"], "ancien")
        self.assertNotIn("ecranBTCcasse1", ab._LIVE_DERNIER)

    def test_direction_zero_est_conservee_pour_un_fvg(self):
        etat = {"canaux_marche": {"GOLD": "-6"}}
        evenement = {"id": "zone-neutre", "message": "EVT|GOLD|zone|0||FVG"}
        envois = []
        with mock.patch.object(ab, "ecran_lire", return_value=[evenement]), \\
             mock.patch.dict(ab.DERNIERS, {"GOLD": {"m1": [{"c": 100}], "b15": []}}), \\
             mock.patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: envois.append(k["text"]) or {"ok": True}), \\
             mock.patch.object(ab, "boutons_chaine_marche", return_value='{"inline_keyboard": []}'):
            ab.ecran_vers_telegram(etat)
        self.assertIn("BIAIS NON DÉFINI", envois[0])
        self.assertEqual(etat["ecran_id"], "zone-neutre")
