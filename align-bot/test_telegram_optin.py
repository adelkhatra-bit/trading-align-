"""Telegram : aucune notification automatique privée sans activation explicite du coach par marché."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class TelegramOptIn(unittest.TestCase):
    def test_aucun_message_prive_sans_activation_coach(self):
        etat = {"auto": {}, "coach_optin": {}, "marches_par_chat": {"10": ["GOLD"], "20": ["NASDAQ"]}, "bot_off": []}
        self.assertEqual(ab.destinataires_message(etat, ["10", "20"], "🥇 GOLD\nTP1 : 3900"), [])
        self.assertFalse(ab.coach_abonne(etat, "10", "GOLD"))

    def test_un_seul_marche_choisi_et_active_recoit_ses_alertes(self):
        etat = {"auto": {}, "coach_optin": {"GOLD": ["10"], "NASDAQ": ["20"]},
                "marches_par_chat": {"10": ["GOLD"], "20": ["NASDAQ"], "30": ["GOLD"]}, "bot_off": []}
        self.assertEqual(ab.destinataires_message(etat, ["10", "20", "30"], "🥇 GOLD\nTP1 : 3900"), ["10"])
        self.assertEqual(ab.destinataires_message(etat, ["10", "20", "30"], "💠 NASDAQ\nTP1 : 22000"), ["20"])

    def test_chaine_publique_conserve_son_flux_et_prives_restent_optin(self):
        etat = {"canal": "-100", "auto": {}, "coach_optin": {"GOLD": ["10"]},
                "marches_par_chat": {"10": ["GOLD"], "20": ["GOLD"]}, "bot_off": []}
        self.assertEqual(ab.destinataires_message(etat, ["10", "20", "-100"], "🥇 GOLD\nTP1 : 3900"), ["-100", "10"])

    def test_file_auto_a_usage_unique_ne_vaut_pas_optin_persistant(self):
        etat = {"auto": {"GOLD": ["10"]}, "coach_optin": {},
                "marches_par_chat": {"10": ["GOLD"]}, "bot_off": []}
        self.assertFalse(ab.coach_abonne(etat, "10", "GOLD"))
        self.assertEqual(ab.destinataires_message(etat, ["10"], "🥇 GOLD\nTP1 : 3900"), [])

    def test_activation_persistante_sur_un_marche_et_pas_les_autres(self):
        etat = {"auto": {}, "coach_optin": {}, "bot_off": []}
        ab.activer_coach_optin(etat, "10", "GOLD", True)
        self.assertTrue(ab.coach_abonne(etat, "10", "GOLD"))
        self.assertFalse(ab.coach_abonne(etat, "10", "NASDAQ"))
        ab.selectionner_coach_optin(etat, "10", ["NASDAQ"])
        self.assertFalse(ab.coach_abonne(etat, "10", "GOLD"))
        self.assertTrue(ab.coach_abonne(etat, "10", "NASDAQ"))

    def test_arret_bot_coupe_immediatement_le_flux_prive(self):
        etat = {"auto": {}, "coach_optin": {"GOLD": ["10"]}, "marches_par_chat": {"10": ["GOLD"]}, "bot_off": ["10"]}
        self.assertEqual(ab.destinataires_message(etat, ["10"], "🥇 GOLD\nTP1 : 3900"), [])

    def test_une_personne_dans_chats_ne_recoit_pas_une_position_sans_optin(self):
        etat = {"auto": {}, "coach_optin": {}, "bot_off": [], "marches_par_chat": {"10": ["GOLD"]}}
        trade = {"d": 1, "e": 3900.0, "sl": 3890.0, "tp1": 3920.0, "tp2": 3940.0, "qui": {}, "sl_h": "mèche basse"}
        with mock.patch.object(ab, "_envoi_sur") as send:
            ab.entrer_inscrits(etat, "GOLD", trade, {"10"})
        self.assertEqual(trade["qui"], {})
        send.assert_not_called()

    def test_optin_coach_persistant_recoit_la_position_du_marche_choisi(self):
        etat = {"auto": {}, "coach_optin": {"GOLD": ["10"]}, "bot_off": [],
                "marches_par_chat": {"10": ["GOLD"], "20": ["NASDAQ"]}}
        trade = {"d": 1, "e": 3900.0, "sl": 3890.0, "tp1": 3920.0, "tp2": 3940.0, "qui": {}, "sl_h": "mèche basse"}
        with mock.patch.object(ab, "_envoi_sur") as send:
            ab.entrer_inscrits(etat, "GOLD", trade, {"10", "20"})
        self.assertIn("10", trade["qui"])
        self.assertNotIn("20", trade["qui"])
        self.assertEqual(send.call_count, 1)

    def test_file_auto_ponctuelle_issue_d_un_clic_reste_valide_une_fois(self):
        etat = {"auto": {"GOLD": ["10"]}, "coach_optin": {}, "bot_off": [],
                "marches_par_chat": {"10": ["GOLD"]}}
        trade = {"d": -1, "e": 3900.0, "sl": 3910.0, "tp1": 3880.0, "tp2": 3860.0, "qui": {}, "sl_h": "mèche haute"}
        with mock.patch.object(ab, "_envoi_sur") as send:
            ab.entrer_inscrits(etat, "GOLD", trade, set())
        self.assertIn("10", trade["qui"])
        self.assertEqual(send.call_count, 1)
        self.assertEqual(etat.get("auto", {}).get("GOLD", []), [])
        self.assertTrue(ab.coach_abonne(etat, "10", "GOLD"))

    def test_prospects_et_rappels_gratuits_sont_silencieux_sans_optin(self):
        etat = {"prospects": ["10", "11"], "auto": {}, "coach_optin": {}, "bot_off": []}
        self.assertEqual(ab.destinataires_gratuits(etat), [])
        with mock.patch.object(ab, "TOKEN", "test"), mock.patch.object(ab, "telegram") as tg:
            ab.envoyer_prospects(etat, "🥇 GOLD - LONG\nEntrée 3900\nTP1 3920", True)
            ab.envoyer_differes({"differe": [{"t": 0, "c": "10", "txt": "🥇 GOLD - LONG"}]}, now=100, dodo=False)
        tg.assert_not_called()

    def test_veille_cloture_ancienne_est_retiree_si_plus_optin(self):
        etat = {"auto": {}, "coach_optin": {"GOLD": ["10"]}, "marches_par_chat": {"10": ["GOLD"]},
                "veille_cloture": {"GOLD": {"10": {"tf": "15 min", "dernier_t": 0}}}}
        ab.selectionner_coach_optin(etat, "10", [])
        with mock.patch.object(ab, "_envoi_sur") as send:
            ab.notifier_clotures(etat, "GOLD", {}, {})
        self.assertEqual(etat["veille_cloture"]["GOLD"], {})
        send.assert_not_called()

    def test_clavier_de_demarrage_n_est_pas_pousse_sans_optin(self):
        etat = {"prospects": ["10"], "coach_optin": {}, "auto": {}, "clavier_v": {}}
        with mock.patch.object(ab, "TOKEN", "test"), mock.patch.object(ab, "_envoi_sur") as send:
            ab.renvoyer_claviers(etat, {"10"})
        send.assert_not_called()

    def test_jauge_ne_cree_aucun_message_sans_optin(self):
        etat = {"auto": {}, "coach_optin": {}, "marches_par_chat": {"10": ["GOLD"]}}
        with mock.patch.object(ab, "telegram") as tg:
            ab.maj_jauge(etat, "GOLD", {"m1": [{"c": 3900}], "confirme": 0}, {}, {"10"})
        tg.assert_not_called()

    def test_accueil_precise_que_le_coach_est_optionnel(self):
        envoyes = []
        with mock.patch.object(ab, "_envoi_sur", side_effect=lambda cid, **kw: envoyes.append(kw)):
            ab.accueil_liens({"liens_marche": {}}, "10", "GOLD")
        self.assertIn("Aucune alerte privée avant activation du coach", envoyes[0]["text"])
        self.assertIn("Activer le coach GOLD", envoyes[0]["reply_markup"])

    def test_texte_telegram_de_preparation_ne_parle_pas_de_fibonacci(self):
        tr = dict(d=-1, e=3900.0, sl=3910.0, tp1=3880.0, tp2=3860.0,
                  rr=2.0, strat="SWING", src="Fibonacci 50 → 78,6 %", n1="support 4h", n2="projection 2R", sl_ut="15 min", sl_h="02:00", za=3898.0, zb=3902.0)
        self.assertNotIn("Fibonacci", ab.fmt_trade("GOLD", tr, 3901.0))


if __name__ == "__main__":
    unittest.main()
