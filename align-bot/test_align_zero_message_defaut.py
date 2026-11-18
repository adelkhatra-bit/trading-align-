"""Règle d'Adel : aucun message privé Telegram par défaut.

Une personne ne reçoit que ce qu'elle a demandé (marché choisi + coach activé, ou une commande).
Les envois spontanés (question du jour, nouveaux boutons, règles épinglées en privé, relance VIP)
sont éteints par défaut ; la chaîne VIP garde ses règles épinglées.
"""
import json
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
        # Une seule exception voulue par Adel : la question du jour (1 notification spontanée par jour).
        self.assertEqual(ab.envois_spontanes_prives(),
                         {"question_quotidienne": True, "clavier": False,
                          "regles_privees": False, "relance_vip": False})

    def test_aucune_variable_ne_les_rallume_par_defaut(self):
        self.assertIn('os.environ.get("ALIGN_QUESTION_QUOTIDIENNE", "1") == "1"', SOURCE)
        for var in ("ALIGN_ENVOI_CLAVIER_SPONTANE",
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


class ParcoursLiveEtBudget(unittest.TestCase):
    def test_bouton_live_commence_par_le_choix_du_marche_meme_sans_live(self):
        etat = {"live_on": False}
        kb = json.loads(ab.clavier_live(etat, "7"))["inline_keyboard"]
        self.assertEqual([b["callback_data"] for b in kb[0]], ["livemkt:BTC", "livemkt:GOLD", "livemkt:NASDAQ"])

    def test_choix_du_marche_propose_la_seule_prochaine_position(self):
        kb = json.loads(ab.clavier_choix_coach("GOLD"))["inline_keyboard"]
        self.assertEqual(kb[0][0]["callback_data"], "auto:GOLD")
        self.assertIn("prochaine position", kb[0][0]["text"])
        t = ab.texte_choix_coach("GOLD")
        self.assertIn("UNIQUEMENT la prochaine position", t)
        self.assertIn("se coupe tout seul", t)

    def test_aucun_niveau_en_prive_avant_validation(self):
        etat = {"canal": "-100", "marches_par_chat": {"11": ["BTC"]}, "auto": {"BTC": ["11"]}}
        with mock.patch.object(ab, "bot_on", return_value=True):
            prep = ab.destinataires_message(etat, {"11"}, "🔔 JE PRÉPARE UNE POSITION — BTC\n🛑 SL 64 980.5\n🎯 TP1 66 200.0")
            pre_alerte = ab.destinataires_message(etat, {"11"}, "👀 ÇA ARRIVE — BTC\nPrépare-toi, attends mon feu vert")
        self.assertEqual(prep, ["-100"])            # niveaux avant validation : chaîne VIP seulement
        self.assertIn("11", pre_alerte)             # pré-alerte sans niveau : le coaché la reçoit

    def test_entree_validee_arrive_avec_ses_niveaux(self):
        etat = {"canal": "-100", "marches_par_chat": {"11": ["BTC"]}, "auto": {"BTC": ["11"]}}
        with mock.patch.object(ab, "bot_on", return_value=True), mock.patch.object(ab, "est_entree", return_value=True):
            dest = ab.destinataires_message(etat, {"11"}, "🟢 BTC - LONG\n📍 Entrée 65 000.0\n🛑 SL 64 500.0\n🎯 TP1 66 000.0")
        self.assertIn("11", dest)

    def test_une_seule_notification_spontanee_par_jour(self):
        etat = {}
        self.assertTrue(ab.notif_du_jour_libre(etat, "11", "2026-11-18"))
        ab.marquer_notif_du_jour(etat, "11", "2026-11-18")
        self.assertFalse(ab.notif_du_jour_libre(etat, "11", "2026-11-18"))
        self.assertTrue(ab.notif_du_jour_libre(etat, "11", "2026-11-19"))

    def test_annonce_du_live_respecte_le_budget_du_jour(self):
        jour = ab.datetime.datetime.now(ab.PARIS).strftime("%Y-%m-%d")
        etat = {"question_quotidienne": {"11": jour}, "quiet": ["33"]}
        envois = []
        with mock.patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: envois.append(str(c))), \
             mock.patch.object(ab, "clavier_live", return_value=None):
            ab.live_annoncer_debut(etat, {"11", "22", "33"})
            ab.live_annoncer_debut(etat, {"11", "22", "33"})
        self.assertEqual(envois, ["22"])            # 11 déjà notifié, 33 a dit « pas aujourd'hui », 22 une seule fois

    def test_le_coach_se_coupe_apres_l_entree(self):
        """Une fois la position donnée, la personne sort de la liste d'attente : pas de 2e position."""
        self.assertIn('for cid in list(dict.fromkeys(etat.get("auto", {}).pop(m, []) + auto)):', SOURCE)


if __name__ == "__main__":
    unittest.main()
