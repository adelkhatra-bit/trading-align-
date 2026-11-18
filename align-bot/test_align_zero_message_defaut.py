"""Règle d'Adel : aucun message privé Telegram par défaut.

Une personne ne reçoit que ce qu'elle a demandé (marché choisi + coach activé, ou une commande).
Les envois spontanés (question du jour, nouveaux boutons, règles épinglées en privé, relance VIP)
sont éteints par défaut ; la chaîne VIP garde ses règles épinglées.
"""
import os
import re
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("TELEGRAM_TOKEN", "")
import align_bot as ab  # noqa: E402

SOURCE = (Path(__file__).resolve().parent / "align_bot.py").read_text(encoding="utf-8")


class ZeroMessageParDefaut(unittest.TestCase):
    def test_tous_les_envois_spontanes_sont_eteints_par_defaut(self):
        self.assertEqual(ab.envois_spontanes_prives(),
                         {"question_quotidienne": False, "clavier": False,
                          "regles_privees": False, "relance_vip": False})

    def test_aucune_variable_ne_les_rallume_par_defaut(self):
        for var in ("ALIGN_QUESTION_QUOTIDIENNE", "ALIGN_ENVOI_CLAVIER_SPONTANE",
                    "ALIGN_REGLES_PRIVEES_SPONTANEES", "ALIGN_RELANCE_VIP_SPONTANEE"):
            self.assertIn(f'os.environ.get("{var}", "0") == "1"', SOURCE)

    def test_question_quotidienne_appelee_seulement_si_rallumee(self):
        appels = [l.strip() for l in SOURCE.splitlines() if re.search(r"\bquestion_quotidienne\(etat, chats\)", l)]
        self.assertEqual(appels, ["question_quotidienne(etat, chats)"])
        self.assertRegex(SOURCE, r"if QUESTION_QUOTIDIENNE:\n\s+question_quotidienne\(etat, chats\)")

    def test_nouveaux_boutons_envoyes_seulement_si_rallumes(self):
        self.assertRegex(SOURCE, r"if ENVOI_CLAVIER_SPONTANE:\n\s+renvoyer_claviers\(etat, chats\)")
        self.assertEqual(len(re.findall(r"^\s+renvoyer_claviers\(etat, chats\)", SOURCE, re.M)), 1)

    def test_regles_epinglees_en_prive_seulement_si_rallumees(self):
        self.assertRegex(SOURCE, r"if str\(cid\) == canal_ or REGLES_PRIVEES_SPONTANEES:\n\s+epingler\(etat, cid\)")

    def test_relance_vip_jamais_envoyee_par_defaut(self):
        bloc = SOURCE.split("if not RELANCE_VIP_SPONTANEE:", 1)
        self.assertEqual(len(bloc), 2, "garde de la relance VIP absente")
        self.assertTrue(bloc[1].lstrip().startswith("continue"))
        self.assertIn("Les positions en direct sont réservées aux VIP", bloc[1][:600])

    def test_destinataires_prives_exigent_marche_choisi_et_coach_actif(self):
        etat = {"canal": "-100", "marches_par_chat": {"11": ["BTC"], "22": ["BTC"]},
                "auto": {"BTC": ["11"]}}
        texte = "🟢 LONG BTC"
        with mock.patch.object(ab, "bot_on", return_value=True):
            dest = ab.destinataires_message(etat, {"11", "22", "33"}, texte)
        self.assertIn("-100", dest)          # chaîne VIP
        self.assertIn("11", dest)            # a choisi BTC ET activé le coach
        self.assertNotIn("22", dest)         # a choisi BTC mais coach éteint
        self.assertNotIn("33", dest)         # n'a rien demandé

    def test_aucune_diffusion_privee_pour_un_message_sans_marche(self):
        etat = {"canal": "-100", "auto": {m: ["11"] for m in ab.MARCHES}}
        with mock.patch.object(ab, "bot_on", return_value=True):
            dest = ab.destinataires_message(etat, {"11"}, "📰 Agenda du jour")
        self.assertEqual(dest, ["-100"])


if __name__ == "__main__":
    unittest.main()
