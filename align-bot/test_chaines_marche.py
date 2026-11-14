import unittest
from unittest import mock
import align_bot as ab


class PreparerChaines(unittest.TestCase):
    def setUp(self):
        self.appels = []
        self.p = [mock.patch.object(ab, "TOKEN", "x"),
                  mock.patch.object(ab, "photo_canal", side_effect=lambda c: self.appels.append(("photo", c)) or True),
                  mock.patch.object(ab, "telegram", side_effect=lambda meth, **k: self.appels.append((meth, k["chat_id"])) or {"ok": True})]
        for x in self.p:
            x.start()

    def tearDown(self):
        for x in self.p:
            x.stop()

    def test_logo_et_description_pour_les_3_chaines_meme_marche_ferme(self):
        etat = {"canaux_marche": {"BTC": -1, "GOLD": -2, "NASDAQ": -3}}
        ab.preparer_chaines(etat)
        for c in (-1, -2, -3):
            self.assertIn(("photo", c), self.appels)
            self.assertIn(("setChatDescription", c), self.appels)
        self.appels.clear()
        ab.preparer_chaines(etat)                       # déjà fait : rien n'est renvoyé
        self.assertEqual(self.appels, [])

    def test_echec_photo_reessaye_plus_tard(self):
        etat = {"canaux_marche": {"GOLD": -2}}
        with mock.patch.object(ab, "photo_canal", return_value=False):
            ab.preparer_chaines(etat)
        self.assertFalse(etat["canal_live"]["GOLD"]["photo_ok"])
        etat["canal_live"]["GOLD"]["photo_essai"] = 0  # une heure plus tard
        ab.preparer_chaines(etat)
        self.assertTrue(etat["canal_live"]["GOLD"]["photo_ok"])


class PasDeDoublon(unittest.TestCase):
    def setUp(self):
        ab._CACHE_CHAINE.clear()
        self.etat = {"canaux_marche": {"BTC": -1, "GOLD": -2}}

    def test_commentaire_saute_si_dans_la_chaine(self):
        with mock.patch.object(ab, "TOKEN", "x"), \
             mock.patch.object(ab, "telegram", return_value={"ok": True, "result": {"status": "member"}}):
            self.assertTrue(ab.doublon_chaine(self.etat, 5, "🎙 ÇA BOUGE !\n🟠 BTC : 66000"))
            self.assertFalse(ab.doublon_chaine(self.etat, 5, "🚦 🟢 J'ENTRE MAINTENANT — BTC"))   # perso : reste dans le bot

    def test_commentaire_garde_si_pas_dans_la_chaine(self):
        with mock.patch.object(ab, "TOKEN", "x"), \
             mock.patch.object(ab, "telegram", return_value={"ok": True, "result": {"status": "left"}}):
            self.assertFalse(ab.doublon_chaine(self.etat, 6, "🎙 ÇA BOUGE !\n🟠 BTC : 66000"))

    def test_ca_bouge_dit_ou_ca_va(self):
        m1 = [{"o": 100, "h": 100, "l": 90, "c": 95}, {"o": 95, "h": 95, "l": 85, "c": 88}, {"o": 88, "h": 88, "l": 80, "c": 82}]
        t = ab.flash_commentateur("BTC", {"m1": m1, "atr": 10}, {"trade": {"d": -1, "e": 101, "sl": 110, "tp1": 85}})
        self.assertIn("ÇA BOUGE", t); self.assertIn("Direction TP2", t)
        t = ab.flash_commentateur("BTC", {"m1": m1, "atr": 10, "confirme": -1}, {})
        self.assertIn("sens de la tendance", t)


class TpFrole(unittest.TestCase):
    def test_frole_puis_recule_rassure_une_fois(self):
        tr = {"e": 100, "sl": 100}                        # SHORT, SL à BE
        r = {"m1": [{"h": 99, "l": 80.5, "c": 81}], "dirs": [-1] * 11}
        self.assertIsNone(ab.frole_tp("BTC", r, tr, -1, 100, 80, "TP1", 81))      # tout près : pas encore de recul
        t = ab.frole_tp("BTC", {"m1": [{"h": 88, "l": 85, "c": 86}], "dirs": [-1] * 11}, tr, -1, 100, 80, "TP1", 86)
        self.assertIn("TP1 FRÔLÉ", t); self.assertIn("T'inquiète", t); self.assertIn("BE", t); self.assertIn("on y retourne", t)
        self.assertIsNone(ab.frole_tp("BTC", {"m1": [{"h": 88, "l": 85, "c": 86}], "dirs": [-1] * 11}, tr, -1, 100, 80, "TP1", 86))

    def test_retour_vers_entree_rassure_avec_pastilles(self):
        tr = {"e": 100, "sl": 100, "frole_TP1_max": 0.95}
        t = ab.retour_entree("BTC", {"dirs": [-1] * 11}, tr, -1, 100, 80, 97)
        for x in ("RETOUR VERS L'ENTRÉE", "🔵 TP1", "🟡 Entrée", "🔴 SL", "BE", "peu probable", "T'inquiète"):
            self.assertIn(x, t)
        self.assertIsNone(ab.retour_entree("BTC", {"dirs": [-1] * 11}, tr, -1, 100, 80, 97))   # une seule fois

    def test_pas_de_frole_si_loin(self):
        tr = {"e": 100, "sl": 110}
        self.assertIsNone(ab.frole_tp("BTC", {"m1": [{"h": 99, "l": 90, "c": 95}]}, tr, -1, 100, 80, "TP1", 95))

    def test_chaine_et_bande_sans_niveaux(self):
        env, pub = [], []
        with mock.patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: env.append(k["text"])), \
             mock.patch.object(ab, "live_publier", side_effect=lambda t: pub.append(t) or True), \
             mock.patch.object(ab, "LIVE_SUJET", "x"):
            etat = {"canaux_marche": {"BTC": -1}, "live_on": True}
            ab.canal_resultats(etat, "BTC", ["😅 TP1 FRÔLÉ — 🟠 BTC\n🎯 TP1 : 80"])
            ab.live_annonces(etat, "BTC", ["😅 TP1 FRÔLÉ — 🟠 BTC\n🎯 TP1 : 80"])
        self.assertIn("TP FRÔLÉ", env[0]); self.assertNotIn("80", env[0])
        self.assertIn("frôlé", pub[0]); self.assertNotIn("Telegram", pub[0])


    def test_fin_de_trade_une_seule_carte_dans_la_chaine(self):
        env = []
        with mock.patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: env.append(k["text"])):
            etat = {"canaux_marche": {"BTC": -1}}
            ab.canal_resultats(etat, "BTC", ["🛑 STOP TOUCHÉ — 🟠 BTC", "🎯 TP2 TOUCHÉ · OBJECTIF FINAL ATTEINT — 🟠 BTC"])
        self.assertEqual(env, [])          # la carte résultat (publier_resultat) est le seul message

    def test_resultat_part_dans_la_chaine_du_marche(self):
        vus = []
        with mock.patch.object(ab, "telegram", side_effect=lambda meth, **k: vus.append((meth, k.get("chat_id"), k.get("text", ""))) or {}), \
             mock.patch.object(ab, "_envoi_sur", return_value=None):
            etat = {"canaux_marche": {"BTC": -7}, "canal_preuves": -9}
            ab.publier_resultat(etat, "BTC", {"d": -1, "e": 100.0, "cree": 0}, 101.0, "SL", -1.0)
        envois = [v for v in vus if v[0] == "sendMessage"]
        self.assertEqual(envois[0][1], -7)
        self.assertIn("STOP TOUCHÉ", envois[0][2])
        self.assertFalse(any(v[1] == -9 for v in envois))

    def test_boutons_chaine_vip_et_live_en_bas(self):
        import json
        kb = json.loads(ab.boutons_menu_rapide({}))["inline_keyboard"]
        self.assertIn("VIP", kb[-1][0]["text"])
        self.assertTrue(any("live" in b["text"].lower() for b in kb[-1]))

    def test_nouveau_clavier_envoye_une_seule_fois(self):
        env = []
        with mock.patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: env.append(c)), mock.patch.object(ab, "TOKEN", "x"):
            etat = {"prospects": ["5"]}
            ab.renvoyer_claviers(etat, {"5", "6"})
            ab.renvoyer_claviers(etat, {"5", "6"})
        self.assertEqual(sorted(env), ["5", "6"])


    def test_une_seule_meche_par_bougie_15(self):
        env = []
        r = {"b15": [{"t": 1, "o": 1, "h": 2, "l": 0, "c": 1}, {"t": 2, "o": 1, "h": 2, "l": 0, "c": 1}]}
        etat = {"canaux_marche": {"BTC": -1}, "canal_live": {"BTC": {"dernier_t": 99}}}
        with mock.patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: env.append(k["text"])), \
             mock.patch.object(ab, "flash_commentateur", return_value="🎣 GROSSE MÈCHE !"), \
             mock.patch.object(ab, "live_bande", return_value=None), \
             mock.patch.object(ab, "boutons_chaine_marche", return_value="{}"):
            ab.notifier_canal_marche(etat, "BTC", r, {})
            etat["canal_live"]["BTC"]["flash_t"] = 0
            ab.notifier_canal_marche(etat, "BTC", r, {})
        self.assertEqual(len(env), 1)


    def test_ia_jamais_automatique(self):
        with mock.patch.object(ab, "ia", side_effect=AssertionError("IA appelée")):
            self.assertEqual(ab.commentaires_ia_temps_reel({}, "BTC", {}, {}, ["🛑 STOP TOUCHÉ — 🟠 BTC"]), [])


if __name__ == "__main__":
    unittest.main()
