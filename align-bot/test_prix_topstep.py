"""Prix Topstep (demande d'Adel 15/11) : l'utilisateur qui trade sur Topstep reçoit les niveaux au vrai prix du contrat."""
import os, sys, unittest, unittest.mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab
import topstep_trade as ts

TR = {"d": 1, "e": 20000.0, "sl": 19950.0, "tp1": 20100.0, "tp2": 20200.0}


class TestNiveaux(unittest.TestCase):
    def test_decalage_et_tick(self):
        n = ts.niveaux_futures("NASDAQ", 20000.0, {"e": 20000.0, "sl": 19950.0}, 20123.4)
        self.assertEqual(n, {"e": 20123.5, "sl": 20073.5})          # tick MNQ = 0,25
        self.assertEqual(ts.niveaux_futures("BTC", 64000, {"e": 64000}, 64212)["e"], 64210.0)  # tick MBT = 5

    def test_sans_prix_rien(self):
        self.assertIsNone(ts.niveaux_futures("GOLD", 4000, {"e": 4000}, None))

    def test_texte(self):
        t = ab.texte_prix_topstep("NASDAQ", TR, 20000.0, 20120.0)
        self.assertIn("PRIX TOPSTEP", t); self.assertIn("MNQ", t)
        self.assertIn("20120", t); self.assertIn("20070", t); self.assertIn("20220", t)
        self.assertIn("DYOR", t)
        self.assertIn("Risque 1 micro-contrat ≈ 100 $", t)         # SL 50 pts MNQ = 200 ticks × 0,5 $
        self.assertNotIn("trop large", t)


class TestEnvoi(unittest.TestCase):
    def test_seuls_ceux_qui_ont_choisi_topstep(self):
        etat = {"plateforme": {"111": "topstep", "222": "tv"}, "coach_optin": {"NASDAQ": ["111"]}}
        envoyes = []
        with unittest.mock.patch.object(ab, "_envoi_sur", lambda cid, **k: envoyes.append((cid, k["text"]))), \
             unittest.mock.patch.object(ab, "marche_autorise", lambda e, c, m: True), \
             unittest.mock.patch.object(ts, "prix_futures", lambda m: 20120.0):
            self.assertEqual(ab.prix_topstep_inscrits(etat, "NASDAQ", TR, 20000.0), 1)
        self.assertEqual([c for c, _ in envoyes], ["111"])

    def test_topstep_absent_aucun_envoi(self):
        etat = {"plateforme": {"111": "topstep"}}
        with unittest.mock.patch.object(ab, "_envoi_sur", lambda *a, **k: self.fail("envoi")), \
             unittest.mock.patch.object(ab, "marche_autorise", lambda e, c, m: True), \
             unittest.mock.patch.object(ts, "prix_futures", lambda m: None):
            self.assertEqual(ab.prix_topstep_inscrits(etat, "NASDAQ", TR, 20000.0), 0)

    def test_choix_enregistre(self):
        etat = {}
        with unittest.mock.patch.object(ab, "_envoi_sur", lambda *a, **k: None):
            ab.regler_plateforme(etat, 111, "topstep")
        self.assertEqual(ab.plateforme(etat, "111"), "topstep")
        self.assertEqual(ab.bouton_plateforme(etat, 111)["callback_data"], "plateforme:menu")
        self.assertEqual(ab.plateforme({}, 5), "tv")

    def test_suivi_ponctuel_recoit_topstep_uniquement_pour_sa_position(self):
        etat = {"plateforme": {"111": "topstep"}, "coach_optin": {},
                "bot_off": [], "marches_par_chat": {"111": ["NASDAQ"]}}
        trade = dict(TR, qui={"111": {"e": TR["e"], "sl": TR["sl"], "tp1": TR["tp1"], "d": TR["d"], "t": 1}})
        envoyes = []
        with unittest.mock.patch.object(ab, "_envoi_sur", lambda cid, **k: envoyes.append(cid)), \\
             unittest.mock.patch.object(ab, "marche_autorise", lambda e, c, m: True), \\
             unittest.mock.patch.object(ts, "prix_futures", lambda m: 20120.0):
            self.assertEqual(ab.prix_topstep_inscrits(etat, "NASDAQ", trade, 20000.0), 1)
        self.assertEqual(envoyes, ["111"])
        self.assertFalse(ab.coach_abonne(etat, "111", "NASDAQ"))  # aucun abonnement permanent créé

    def test_les_deux_recoivent_aussi_topstep(self):
        etat = {"plateforme": {"111": "deux", "222": "tv", "333": "topstep"}, "coach_optin": {"NASDAQ": ["111", "333"]}}
        envoyes = []
        with unittest.mock.patch.object(ab, "_envoi_sur", lambda cid, **k: envoyes.append(cid)), \
             unittest.mock.patch.object(ab, "marche_autorise", lambda e, c, m: True), \
             unittest.mock.patch.object(ts, "prix_futures", lambda m: 20120.0):
            ab.prix_topstep_inscrits(etat, "NASDAQ", TR, 20000.0)
        self.assertEqual(sorted(envoyes), ["111", "333"])

    def test_menu_trois_choix(self):
        vus = []
        with unittest.mock.patch.object(ab, "_envoi_sur", lambda cid, **k: vus.append(k)):
            ab.regler_plateforme({}, 1, "menu")
        self.assertEqual(len(__import__("json").loads(vus[0]["reply_markup"])["inline_keyboard"]), 3)


if __name__ == "__main__":
    unittest.main()
