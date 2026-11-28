import os, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab

class CoachAvantEntree(unittest.TestCase):
    def test_temps_restant_fvg_et_validation_annoncee(self):
        with mock.patch.object(ab, "timeframe_attendu", return_value="15 min"), \
             mock.patch.object(ab, "prochaine_cloture_bougie", side_effect=lambda r, tf, now: now + 125):
            t = ab.avant_entree("BTC", {}, {}, {"src": "Order block + FVG rouge 15 min"}, -1)
        self.assertIn("clôture dans", t)
        self.assertIn("FVG", t)
        self.assertIn("rebondit", t)
        self.assertIn("✅ VALIDÉ 🔴 SHORT", t)

    def test_sans_fvg_pas_de_phrase_rebond(self):
        with mock.patch.object(ab, "timeframe_attendu", side_effect=Exception("x")):
            t = ab.avant_entree("GOLD", {}, {}, {"src": "plan"}, 1)
        self.assertNotIn("FVG", t)
        self.assertIn("✅ VALIDÉ 🟢 LONG", t)

class ApprocheTP(unittest.TestCase):
    def test_direction_tp2_si_ca_pousse(self):
        t = ab.approche_tp("BTC", {"dirs": [-1, -1, -1, 0, -1, 0, 0, -1, 0, -1, -1]}, -1, 65000, "TP2")
        self.assertIn("DIRECTION TP2", t); self.assertIn("café", t)

    def test_perturbation_expliquee(self):
        t = ab.approche_tp("GOLD", {"dirs": [1, 1, 1, 0, 0, 0, 0, -1, 0, -1, -1]}, -1, 3800, "TP1")
        self.assertIn("PETITE PERTURBATION", t); self.assertIn("3/5", t); self.assertIn("BE", t)

class CoachEnDirect(unittest.TestCase):
    def test_carte_a_chaque_cloture_puis_pas_de_doublon(self):
        envoyes = []
        etat = {"coach_live": {"BTC": {"9": {"expire": 9e12, "dernier_t": 0}}}}
        b15 = [dict(t=900 * i, o=100, h=101, l=98, c=99) for i in range(5)]
        r = {"b15": b15, "m1": [dict(c=99)], "confirme": -1, "dirs": [0] * 11}
        with mock.patch.object(ab, "_envoi_sur", side_effect=lambda cid, **k: envoyes.append(k["text"]) or {"ok": True}), \
             mock.patch.object(ab, "raison_attente", return_value="J'attends la zone"):
            ab.notifier_coach_live(etat, "BTC", r, {})
            ab.notifier_coach_live(etat, "BTC", r, {})
        self.assertEqual(len(envoyes), 1)
        self.assertIn("COACH COMMENTATEUR", envoyes[0]); self.assertIn("Bougie en baisse", envoyes[0]); self.assertIn("BILAN 15 MIN", envoyes[0])

    def test_ancienne_expiration_de_2h_est_ignoree(self):
        envoyes = []
        etat = {"coach_live": {"GOLD": {"9": {"expire": 0, "dernier_t": 0}}}}
        r = {"b15": [dict(t=0, o=1, h=1, l=1, c=1), dict(t=900, o=1, h=1, l=1, c=1)]}
        with mock.patch.object(ab, "bot_on", return_value=True), mock.patch.object(ab, "dans_chaine", return_value=False), mock.patch.object(ab, "_envoi_sur", side_effect=lambda cid, **k: envoyes.append(k["text"]) or {"ok": True}), mock.patch.object(ab, "texte_coach_live", return_value="COACH GOLD"), mock.patch.object(ab, "markup_analyse", return_value=None), mock.patch.object(ab, "positions_bot", return_value=[]), mock.patch.object(ab.time, "time", return_value=1000):
            ab.notifier_coach_live(etat, "GOLD", r, {})
        self.assertIn("9", etat["coach_live"]["GOLD"])
        self.assertFalse(any("TERMINÉ" in x for x in envoyes))


class CoachStopPolicy(unittest.TestCase):
    def test_news_alert_never_advises_early_break_even_from_tp_progress_alone(self):
        now = 1_800_000_000
        sent = []
        etat = {"cal": {"ev": [{"t": now + 5 * 60, "titre": "CPI"}]}}
        tr = {
            "d": 1, "e": 100.0, "sl": 95.0, "tp1": 120.0, "tp2": 130.0,
            "statut": "entree", "qui": {"123": {"e": 100.0, "sl": 95.0, "tp1": 120.0, "fini": False}},
        }
        cle = {"trade": tr}
        r = {
            "m1": [{"c": 106.0}], "r5": [50.0], "dirs": [0] * 11,
            "niveaux": [], "atr": 1.0,
        }
        with mock.patch.object(ab.time, "time", return_value=now), mock.patch.object(ab, "gerer_stop"), mock.patch.object(ab, "_envoi_sur", side_effect=lambda cid, **kwargs: sent.append(kwargs["text"]) or {"ok": True}):
            ab.coach(etat, "BTC", r, cle)
        news = [message for message in sent if "News dans" in message]
        self.assertEqual(len(news), 1)
        self.assertIn("Vérifie ton stop personnel actuel", news[0])
        self.assertIn("Ne le déplace pas sans validation", news[0])
        self.assertNotIn("Mets ton SL à BE", news[0])


class FlashCommentateur(unittest.TestCase):
    def test_mouvement_brusque(self):
        r = {"atr": 100, "m1": [dict(o=1000, c=990), dict(o=990, c=960), dict(o=960, c=930)], "b15": []}
        t = ab.flash_commentateur("BTC", r, {"trade": {"d": -1}})
        self.assertIn("ÇA BOUGE", t); self.assertIn("vendeurs", t); self.assertIn("Dans le sens du bot", t)
        self.assertIn("Clôtures MTF : indisponibles", t)
        self.assertIn("pas une entrée", t)

    def test_grosse_meche_haute_est_clairement_un_rejet_baissier_non_confirme(self):
        r = {
            "atr": 100, "m1": [dict(o=1000, c=1000)] * 3,
            "b15": [dict(o=990, h=1080, l=985, c=1000)],
            "dirs_cloturees": [-1] * 8 + [1, 1, 0],
        }
        t = ab.flash_commentateur("GOLD", r, {})
        self.assertIn("PRESSION VENDEUSE POSSIBLE", t)
        self.assertIn("mèche haute", t)
        self.assertIn("résistance non vérifiée", t)
        self.assertIn("Biais de contexte : SHORT dominant", t)
        self.assertIn("8/11 baissières", t)
        self.assertIn("pas un signal", t)
        self.assertIn("M15 non clôturée", t)
        english = ab.traduire(t)
        self.assertIn("POSSIBLE SELLING PRESSURE", english)
        self.assertIn("Context bias: SHORT dominant", english)
        self.assertIn("M15 not closed", english)

    def test_grosse_meche_basse_est_clairement_un_rejet_haussier_non_confirme(self):
        r = {
            "atr": 100, "m1": [dict(o=1000, c=1000)] * 3,
            "b15": [dict(o=1010, h=1015, l=920, c=1000)],
            "dirs_cloturees": [1] * 7 + [-1] * 3 + [0],
        }
        t = ab.flash_commentateur("GOLD", r, {})
        self.assertIn("PRESSION ACHETEUSE POSSIBLE", t)
        self.assertIn("mèche basse", t)
        self.assertIn("support non vérifié", t)
        self.assertIn("Biais de contexte : LONG dominant", t)
        self.assertIn("7/11 haussières", t)
        self.assertIn("M15 non clôturée", t)

    def test_deux_meches_ne_sont_pas_forcees_en_direction(self):
        r = {
            "atr": 100, "m1": [dict(o=1000, c=1000)] * 3,
            "b15": [dict(o=1000, h=1080, l=920, c=1000)],
            "dirs_cloturees": [-1] * 6 + [1] * 5,
        }
        t = ab.flash_commentateur("GOLD", r, {})
        self.assertIn("INDÉCISION", t)
        self.assertIn("aucun rejet directionnel", t)
        self.assertNotIn("REJET BAISSIER POTENTIEL", t)
        self.assertNotIn("REJET HAUSSIER POTENTIEL", t)

    def test_active_trade_direction_is_the_mtf_reference(self):
        r = {
            "atr": 100, "m1": [dict(o=1000, c=1000)] * 3,
            "b15": [dict(o=990, h=1080, l=985, c=1000)],
            "confirme": 0,
            "dirs_cloturees": [1] * 11,
        }
        t = ab.flash_commentateur("BTC", r, {"trade": {"d": -1, "e": 1000, "sl": 1010, "tp1": 980}})
        self.assertIn("sens confirmé SHORT", t)
        self.assertIn("0/11 alignées", t)
        self.assertIn("11 opposées", t)

    def test_absence_de_clotures_mtf_n_est_pas_remplacee_par_les_ut_en_formation(self):
        r = {
            "atr": 100, "m1": [dict(o=1000, c=1000)] * 3,
            "b15": [dict(o=990, h=1080, l=985, c=1000)],
            "dirs": [-1] * 11,
        }
        t = ab.flash_commentateur("GOLD", r, {})
        self.assertIn("Clôtures MTF : indisponibles", t)
        self.assertNotIn("11/11", t)

    def test_rien_de_special(self):
        r = {"atr": 100, "m1": [dict(o=1000, c=1001)] * 3, "b15": [dict(o=1000, h=1010, l=995, c=1001)]}
        self.assertIsNone(ab.flash_commentateur("BTC", r, {}))

class CanalMarche(unittest.TestCase):
    def test_connexion_canal_btc_sans_toucher_au_vip(self):
        etat = {"canal": "VIP"}
        with mock.patch.object(ab, "_envoi_sur"), mock.patch.object(ab, "proprio", return_value=[]):
            ab.connecter_canal(etat, {"chat": {"id": -100, "title": "ALIGN BTC", "username": "alignbtc"}, "new_chat_member": {"status": "administrator"}})
        self.assertEqual(etat["canaux_marche"]["BTC"], "-100"); self.assertEqual(etat["canal"], "VIP")

    def test_canal_sans_niveaux(self):
        envoyes = []
        etat = {"canaux_marche": {"BTC": "-100"}}
        b15 = [dict(t=900 * i, o=100, h=101, l=98, c=99) for i in range(5)]
        r = {"b15": b15, "m1": [dict(c=99)], "confirme": -1, "dirs": [0] * 11}
        cle = {"trade": {"d": -1, "e": 120, "sl": 130, "tp1": 90}}
        with mock.patch.object(ab, "_envoi_sur", side_effect=lambda cid, **k: envoyes.append((cid, k["text"])) or {"ok": True}):
            ab.notifier_canal_marche(etat, "BTC", r, cle)
        self.assertEqual(envoyes[0][0], "-100")
        self.assertIn("pas une entrée", envoyes[0][1]); self.assertNotIn("130", envoyes[0][1])

class Accueil(unittest.TestCase):
    def test_questionnaire_puis_liens(self):
        envoyes = []
        etat = {"liens_marche": {"BTC": "https://t.me/+abc"}}
        with mock.patch.object(ab, "_envoi_sur", side_effect=lambda cid, **k: envoyes.append(k) or {"ok": True}):
            ab.accueil_questionnaire(etat, "7")
            ab.accueil_marches(etat, "7")
            ab.accueil_liens(etat, "7", "BTC")
        self.assertIn("niveau", envoyes[0]["text"]); self.assertIn("marché", envoyes[1]["text"])
        self.assertIn("https://t.me/+abc", envoyes[2]["reply_markup"])
        self.assertEqual(ab.marches_choisis(etat, "7"), {"BTC"})

if __name__ == "__main__":
    unittest.main()
