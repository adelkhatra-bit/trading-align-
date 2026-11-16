"""Les alertes privées Telegram sont réservées aux marchés explicitement activés dans le Coach."""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class TelegramCoachOptIn(unittest.TestCase):
    def test_selection_du_marche_seule_ne_donne_aucune_alerte_privee(self):
        state = {"marches_par_chat": {"10": ["GOLD"], "20": ["NASDAQ"]}}
        self.assertEqual(ab.destinataires_message(state, {"10", "20"}, "🥇 GOLD — SIGNAL LONG"), [])
        self.assertFalse(ab.coach_abonne(state, "10", "GOLD"))

    def test_activation_coach_est_explicite_et_isolee_par_marche(self):
        state = {
            "marches_par_chat": {"10": ["GOLD"], "20": ["NASDAQ"], "30": ["GOLD", "NASDAQ"]},
            "auto": {"GOLD": ["10", "30"], "NASDAQ": ["20"]},
        }
        self.assertEqual(ab.destinataires_message(state, {"10", "20", "30"}, "🥇 GOLD — LONG"), ["10", "30"])
        self.assertEqual(ab.destinataires_message(state, {"10", "20", "30"}, "💠 NASDAQ — SHORT"), ["20"])
        self.assertEqual(ab.destinataires_message(state, {"10", "20", "30"}, "🟠 BTC — LONG"), [])

    def test_message_global_est_reserve_aux_utilisateurs_ayant_un_coach_actif(self):
        state = {"auto": {"GOLD": ["10"], "NASDAQ": ["20"]}}
        self.assertEqual(ab.destinataires_message(state, {"10", "20", "30"}, "📅 Information générale"), ["10", "20"])

    def test_bouton_arret_desactive_immediatement_les_alertes_du_coach(self):
        state = {"auto": {"GOLD": ["10"]}, "marches_par_chat": {"10": ["GOLD"]}, "bot_off": ["10"]}
        self.assertFalse(ab.coach_abonne(state, "10", "GOLD"))
        self.assertEqual(ab.destinataires_message(state, {"10"}, "🥇 GOLD — LONG"), [])

    def test_chaine_publique_conserve_son_flux_mais_prives_requierent_le_coach(self):
        state = {"canal": "-100", "marches_par_chat": {"10": ["GOLD"], "20": ["GOLD"]},
                 "auto": {"GOLD": ["10"]}}
        self.assertEqual(ab.destinataires_message(state, {"10", "20", "-100"}, "🥇 GOLD — LONG"), ["-100", "10"])

    def test_prospects_et_rappels_gratuits_sont_silencieux(self):
        state = {"prospects": ["10", "11"], "auto": {}}
        self.assertEqual(ab.destinataires_gratuits(state), [])
        with patch.object(ab, "telegram") as tg:
            ab.envoyer_prospects(state, "🥇 GOLD — LONG\\nEntrée 3900", True)
        tg.assert_not_called()

    def test_anciens_messages_differes_sont_supprimes_sans_envoi(self):
        state = {"differe": [{"t": 0, "c": "10", "txt": "ancien signal"}]}
        with patch.object(ab, "telegram") as tg:
            ab.envoyer_differes(state, now=100, dodo=True)
        self.assertEqual(state["differe"], [])
        tg.assert_not_called()

    def test_jauge_privee_ne_se_cree_pas_sans_coach(self):
        state = {"marches_par_chat": {"10": ["GOLD"]}}
        cle = {"jauge": {}, "jauge_txt": {}}
        with patch.object(ab, "telegram") as tg:
            ab.maj_jauge(state, "GOLD", {"m1": [{"c": 3900}]}, cle, {"10"})
        self.assertFalse(any(c.args[0] in ("sendMessage", "editMessageText") for c in tg.call_args_list))

    def test_radar_prive_ne_cible_que_les_coachs_actifs(self):
        state = {"marches_par_chat": {"10": ["GOLD"], "20": ["GOLD"]},
                 "auto": {"GOLD": ["10"]},
                 "veille_cloture": {"GOLD": {"10": {"multi": True}, "20": {"multi": True}}}}
        self.assertEqual(ab.destinataires_radar(state, {"10", "20"}), ["10"])


if __name__ == "__main__":
    unittest.main()
