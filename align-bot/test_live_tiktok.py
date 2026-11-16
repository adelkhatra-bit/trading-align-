import unittest.mock
"""LIVE TikTok : bande qui défile, bulles, boost, télécommande payante (Stars) — jamais de niveaux sur l'écran."""
import json
import os
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class LiveTikTok(unittest.TestCase):
    def setUp(self):
        ab._LIVE_BOOSTS.clear()
        ab._LIVE_DERNIER.clear()
        self.publie = []
        self.envoye = []
        self.tg = []
        self.p = [mock.patch.object(ab, "LIVE_SUJET", "test-sujet"),
                  mock.patch.object(ab, "live_publier", side_effect=lambda t: self.publie.append(t) or True),
                  mock.patch.object(ab, "_envoi_sur", side_effect=lambda cid, **kw: self.envoye.append((cid, kw))),
                  mock.patch.object(ab, "telegram", side_effect=lambda m, **kw: self.tg.append((m, kw)) or {"ok": True})]
        for x in self.p:
            x.start()
        self.etat = {"proprio": ["1"], "prenoms": {"2": "Karim"}, "prospects": ["3"], "coach_optin": {"GOLD": ["2"], "BTC": ["3"]}}

    def tearDown(self):
        for x in self.p:
            x.stop()

    def test_bouton_live_dans_les_deux_claviers(self):
        for c in (ab.CLAVIER, ab.CLAVIER_VISITEUR):
            textes = [b["text"] for ligne in json.loads(c)["keyboard"] for b in ligne]
            self.assertIn("🔴 Live", textes)

    def test_live_24h_toujours_actif_par_defaut(self):
        self.assertTrue(ab.live_actif({}))

    def test_entree_toujours_sur_la_bande_meme_live_eteint(self):
        # Règle d'Adel (14/11) : l'entrée en position passe toujours sur la bande (elle n'existe que sur l'écran du live)
        with mock.patch.object(ab, "LIVE_24H", False):
            ab.live_annonces(self.etat, "BTC", ["🟢🟢🟢 J'ENTRE MAINTENANT — BTC"])
        self.assertEqual(len(self.publie), 1)
        self.assertIn("lien en bio", self.publie[0]); self.assertNotIn("Telegram", self.publie[0])

    def test_tp_touche_toujours_sur_la_bande(self):
        ab.live_annonces(self.etat, "BTC", ["🎯 BTC : TP1 TOUCHÉ"])
        self.assertTrue(any("TP1 TOUCHÉ" in x for x in self.publie))
        self.assertTrue(any("lien en bio" in x for x in self.publie))
        self.assertFalse(any("Telegram" in x for x in self.publie))

    def test_proprio_lance_le_live_et_tout_le_monde_est_prevenu(self):
        ab.live_callback(self.etat, {"2"}, {"id": "x"}, "liveon", "x", "1")
        self.assertTrue(self.etat["live_on"])
        dest = {cid for cid, _ in self.envoye}
        self.assertEqual(dest, {"2", "3"})
        self.assertTrue(any("EN LIVE" in kw["text"] for _, kw in self.envoye))

    def test_un_abonne_ne_peut_pas_lancer_le_live(self):
        ab.live_callback(self.etat, {"2"}, {"id": "x"}, "liveon", "x", "2")
        self.assertFalse(self.etat.get("live_on"))

    def test_annonces_sans_aucun_niveau(self):
        self.etat["live_on"] = True
        ab.live_annonces(self.etat, "BTC", ["🟢🟢🟢 J'ENTRE MAINTENANT — BTC\n📌 Entrée 68459,14\n🛑 SL 69105", "🎯 TP1 TOUCHÉ — BTC 67167"])
        self.assertEqual(len(self.publie), 2)          # entrée + TP1 (chacun finit par « lien en bio »)
        self.assertTrue(all("lien en bio" in t for t in self.publie))
        for t in self.publie:
            self.assertIsNone(re.search(r"\d{3,}", t), t)
            self.assertNotIn("SHORT", t)
            self.assertNotIn("LONG", t)
        ab.live_annonces(self.etat, "BTC", ["🟢🟢🟢 J'ENTRE MAINTENANT — BTC"])
        self.assertEqual(len(self.publie), 2)          # pas de doublon

    def test_bulle_zone(self):
        self.etat["live_on"] = True
        ab.live_annonces(self.etat, "GOLD", ["🟥🟥 POINT D'ENTRÉE À VENIR — 🥇 GOLD\n🟨 Le prix entre dans la zone\n📍 Zone ≈ 3990 – 4012"])
        self.assertTrue(self.publie[0].startswith("BULLE:"))
        self.assertIsNone(re.search(r"\d{3,}", self.publie[0]))
        self.assertTrue(self.publie[0].startswith("BULLE:🎯 Le prix arrive dans une zone clé 👀 • ⏱ verdict dans "))
        self.assertTrue(self.publie[0].endswith("les infos en temps réel : lien en bio 🎁 gratuit"))
        for mot in ("GOLD", "SHORT", "LONG", "ZONE", "position"):
            self.assertNotIn(mot, self.publie[0])

    def test_reinjection_arrete_tous_les_animateurs_periodiques(self):
        bande = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "live", "align-bande-live.user.js"), encoding="utf-8").read()
        stop = bande[bande.index("stop() { vivant = false;"):]
        for timer in ("coachT", "iaT", "astuceT", "regardT", "chronoT", "coeurT", "posT", "masqueT", "etiqT"):
            self.assertIn(f"clearInterval({timer})", stop, f"timer non arrêté lors de la réinjection : {timer}")

    def test_jamais_le_mot_telegram_a_l_ecran(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "align_bot.py"), encoding="utf-8").read()
        for ligne in src.splitlines():
            if ("live_bande(" in ligne or "live_publier(" in ligne) and '"' in ligne:
                self.assertNotIn("Telegram", ligne, ligne)
        bande = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "live", "align-bande-live.user.js"), encoding="utf-8").read()
        self.assertNotIn("sur Telegram", bande)

    def test_boost_limite_par_personne(self):
        self.etat["live_on"] = True
        ab.live_callback(self.etat, set(), {"id": "x"}, "liveboost", "x", "2")
        ab.live_callback(self.etat, set(), {"id": "y"}, "liveboost", "x", "2")
        self.assertEqual(self.publie, ["🙏 MERCI KARIM ! Karim BOOSTE LE LIVE 🚀 ABONNE-TOI • PARTAGE"])

    def test_facture_en_stars(self):
        self.etat["live_on"] = True
        ab.live_callback(self.etat, set(), {"id": "x"}, "livemain", "5", "2")
        m, kw = self.tg[-1]
        self.assertEqual(m, "sendInvoice")
        self.assertEqual(kw["currency"], "XTR")
        self.assertEqual(kw["provider_token"], "")
        self.assertEqual(json.loads(kw["prices"])[0]["amount"], ab.PRIX_MAIN_STARS)
        self.assertEqual(kw["payload"], "livemain:5")

    def test_admin_prend_la_main_sans_payer(self):
        self.etat["live_on"] = True
        ab.live_callback(self.etat, set(), {"id": "x"}, "livemain", "15", "1")
        self.assertFalse(any(m == "sendInvoice" for m, _ in self.tg))
        self.assertTrue(self.publie[-1].startswith("CMD:tf:15:"))
        self.assertIn("capture", self.envoye[-1][1]["text"])

    def test_ordre_btc_gold_nasdaq_en_premier(self):
        self.etat["live_on"] = True
        kb = json.loads(ab.clavier_live(self.etat, "2"))["inline_keyboard"]
        self.assertEqual([b["text"] for b in kb[2]], ["🟠 BTC", "🥇 Gold", "💠 NASDAQ"])
        self.assertIn("capture", ab.texte_live(self.etat))

    def test_paiement_refuse_si_live_eteint(self):
        p24 = mock.patch.object(ab, "LIVE_24H", False)
        p24.start()
        self.addCleanup(p24.stop)
        self.assertFalse(ab.live_pre_checkout(self.etat, {"id": "q", "invoice_payload": "livemain:5"}))
        self.assertEqual(self.tg[-1][1]["ok"], "false")
        self.etat["live_on"] = True
        self.assertTrue(ab.live_pre_checkout(self.etat, {"id": "q", "invoice_payload": "livemain:5"}))
        self.assertEqual(self.tg[-1][1]["ok"], "true")
        self.assertFalse(ab.live_pre_checkout(self.etat, {"id": "q", "invoice_payload": "autre:5"}))

    def test_ecran_muet_l_abonne_est_prevenu(self):
        self.etat["live_on"] = True
        with mock.patch.object(ab, "live_publier", return_value=False):
            self.assertFalse(ab.live_paiement_recu(self.etat, "2", {"invoice_payload": "livemain:5"}))
        self.assertIn("n'a pas répondu", self.envoye[-1][1]["text"])

    def test_admin_voit_le_code_ecran(self):
        ab.menu_live(self.etat, "1")
        self.assertIn("Code écran (admin) : test-sujet", self.envoye[-1][1]["text"])
        ab.menu_live(self.etat, "2")
        self.assertNotIn("Code écran", self.envoye[-1][1]["text"])

    def test_paiement_recu_envoie_l_ordre_au_graphique(self):
        self.etat["live_on"] = True
        ab.live_paiement_recu(self.etat, "2", {"invoice_payload": "livemain:GOLD", "total_amount": 25, "telegram_payment_charge_id": "c1"})
        self.assertEqual(self.publie, ["CMD:sym:FOREXCOM:XAUUSD:Karim"])
        self.assertEqual(self.etat["live_paiements"][-1]["id"], "c1")
        self.assertIn("C'est à toi", self.envoye[-2][1]["text"])
        self.assertIn("PRENDS LA MAIN", self.envoye[-1][1]["text"])      # le menu du live redescend en bas

class CartesRelieesAuGraphique(unittest.TestCase):
    def test_zone_parle_comme_le_graphique_en_anglais_aussi(self):
        fr = ("🟩 Le prix entre dans la ZONE du graphique\n🟨 Ligne jaune ENTRÉE : attends la CLÔTURE 15 min EN DESSOUS\n"
              "🙅 Une mèche seule ne suffit pas\n🛑 SL = ligne rouge du graphique")
        en = ab.traduire(fr)
        self.assertIn("chart ZONE", en)
        self.assertIn("CLOSE BELOW", en)
        self.assertIn("red line", en)
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "align_bot.py"), encoding="utf-8").read()
        self.assertIn("CLÔTURE SOUS l'étiquette « ENTRÉE »", src)
        self.assertIn("REJOINT LA TEAM ALIGN", src)



class LectureTP1(unittest.TestCase):
    def r_(self, dirs, rsis=None, sqzs=None):
        return {"dirs": dirs + [0] * (11 - len(dirs)), "rsis": rsis or [50] * 11, "sqzs": sqzs or [0] * 11}

    def test_continue_vers_tp2(self):
        l = ab.lecture_tp1(self.r_([-1, -1, -1, -1, 0]), -1)
        self.assertIn("🚀 ÇA PEUT CONTINUER VERS LE TP2", l)
        self.assertTrue(any("EN DESSOUS" in x for x in l))

    def test_risque_de_retour(self):
        rs = [50] * 11; rs[4] = 25
        l = ab.lecture_tp1(self.r_([1, 1, 1, 0, -1], rs), -1)
        self.assertEqual(l[0], "⚠️ RISQUE DE RETOUR VERS L'ENTRÉE")
        self.assertTrue(any("RSI 15 min 25" in x for x in l))

    def test_hesitation_et_long(self):
        l = ab.lecture_tp1(self.r_([1, 0, -1, 0, 1]), 1)
        self.assertEqual(l[0], "🟨 LE MARCHÉ HÉSITE AU TP1")
        self.assertTrue(any("AU-DESSUS" in x for x in l))
        self.assertIn("IT CAN GO ON TO TP2", ab.traduire("🚀 ÇA PEUT CONTINUER VERS LE TP2"))


class CartesCouleursGraphique(unittest.TestCase):
    def test_cartes_parlent_des_lignes(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "align_bot.py"), encoding="utf-8").read()
        for mot in ("(étiquette ENTRÉE)", "(ligne rouge)", "(ligne bleue)", "🔒 SL protégé", "🟨 Entrée {px(tr['e'])} • 🛑 SL"):
            self.assertIn(mot, src)
        self.assertIn("(red line)", ab.traduire("🛑 SL : 1 (ligne rouge)"))



class TestFinDeTradeBande(unittest.TestCase):
    def test_tp_final_et_sl_sur_la_bande(self):
        pub = []
        with mock.patch.object(ab, "live_publier", side_effect=lambda t: pub.append(t) or True):
            ab._LIVE_DERNIER.clear()
            ab.live_fin_de_trade({}, "BTC", {"e": 100.0}, 102.0, 2.0)
            ab.live_fin_de_trade({}, "BTC", {"e": 100.0}, 102.0, 2.0)      # même annonce : une seule fois
            ab.live_fin_de_trade({}, "GOLD", {"e": 100.0}, 99.0, -1.0)
        self.assertEqual(len(pub), 2)
        self.assertIn("TP TOUCHÉ", pub[0]); self.assertIn("lien en bio", pub[0]); self.assertNotIn("Telegram", pub[0])
        self.assertIn("stop touché", pub[1])

    def test_compte_a_rebours(self):
        self.assertEqual(ab.min_avant_cloture15(900 * 10 + 1), 15)
        self.assertEqual(ab.min_avant_cloture15(900 * 10 + 840), 1)



class TestPrepareToiLive(unittest.TestCase):
    def test_fenetre_prepare_toi_sans_niveau(self):
        pub = []
        props = [{"m": "BTC", "d": -1, "rang": 0, "za": 65717.0, "zb": 65965.0}]
        with mock.patch.object(ab, "classer_marches", return_value=props), mock.patch.object(ab, "_radar_pret", return_value=True), \
             mock.patch.object(ab, "live_publier", side_effect=lambda t: pub.append(t) or True):
            ab._LIVE_DERNIER.clear()
            ab.live_prepare_toi({}, {}, 1000.0)
            ab.live_prepare_toi({}, {}, 1060.0)
        self.assertEqual(len(pub), 3)                # prépare-toi + chrono « une position arrive » (v8.5) + jeu « tapote l'écran », une seule fois
        self.assertIn("couler", pub[0]); self.assertIn("verdict dans", pub[0]); self.assertIn("lien en bio", pub[0])
        self.assertEqual(pub[1], "CMD:chrono:800:BTC")   # chrono jusqu'à la clôture 15 min, jamais de prix
        self.assertIn("tapote", pub[2])
        for t in pub:
            self.assertNotIn("65", t); self.assertNotIn("Telegram", t)



class TestSpectacleV85(unittest.TestCase):
    def test_phrases_ia_filtrees(self):
        brut = ("ça monte ou ça descend ? dis-le en commentaire 👇 | up or down? tell us in the comments 👇\n"
                "BTC à 65000 ce soir | BTC at 65000 tonight\n"
                "rejoins le Telegram | join the Telegram\n"
                "prépare ton entrée | get your entry ready\n"
                "phrase sans anglais")
        p = ab.phrases_bande_propres(brut)
        self.assertEqual(p, [["ça monte ou ça descend ? dis-le en commentaire 👇", "up or down? tell us in the comments 👇"]])

    def test_agenda_discours_et_ouverture(self):
        pub = []
        t0 = int(ab.datetime.datetime(2026, 11, 16, 15, 15, tzinfo=ab.PARIS).timestamp())   # lundi 15 h 15
        evts = [{"titre": "Fed Chair Powell Speaks", "t": t0 + 15 * 60}]
        with mock.patch.object(ab, "calendrier", return_value=evts), \
             mock.patch.object(ab, "live_publier", side_effect=lambda t: pub.append(t) or True):
            ab._LIVE_DERNIER.clear()
            ab.live_agenda({}, t0)
            ab.live_agenda({}, t0 + 30)                # pas de doublon
        self.assertEqual(len(pub), 2)
        self.assertTrue(any("DISCOURS" in x and "Powell" in x for x in pub))
        self.assertTrue(any("NEW YORK" in x for x in pub))
        for x in pub:
            self.assertNotIn("Telegram", x)


class TestIABandeNumerotee(unittest.TestCase):
    def test_lignes_numerotees_acceptees(self):
        brut = "1. ça monte ou ça descend ? dis-le en commentaire 👇 | up or down? tell us in the comments 👇\n- **tapote l'écran si t'es là 👆** | **tap the screen if you are here 👆**"
        p = ab.phrases_bande_propres(brut)
        self.assertEqual(len(p), 2)
        self.assertTrue(p[0][0].startswith("ça monte"))
        self.assertNotIn("**", p[1][0])


class TestBandeRassure(unittest.TestCase):
    def test_contre_le_bot_rassure_sans_niveau(self):
        t = ab.texte_bande_flash("🎙 ÇA BOUGE !\n🟠 BTC : 65000\n⚠️ Contre le bot", -1, "BTC")
        for x in ("pas de panique", "clôture dans", "reprendre la descente", "lien en bio"):
            self.assertIn(x, t)
        self.assertNotIn("65000", t); self.assertNotIn("Telegram", t)



class LiveOutbox(unittest.TestCase):
    def test_live_publier_persists_and_deduplicates_until_sent(self):
        previous = ab._ETAT_COURANT.get("etat")
        state = {}
        ab._ETAT_COURANT["etat"] = state
        try:
            with mock.patch.object(ab, "LIVE_SUJET", "test-sujet"):
                self.assertTrue(ab.live_publier("NEWS:message de test"))
                self.assertTrue(ab.live_publier("NEWS:message de test"))
            self.assertEqual(len(state.get("live_outbox", [])), 1)
            with mock.patch.object(ab, "LIVE_SUJET", "test-sujet"), \
                 mock.patch.object(ab.urllib.request, "urlopen", return_value=mock.MagicMock()):
                self.assertEqual(ab.traiter_file_live(state, maintenant=100), 1)
            self.assertEqual(state["live_outbox"], [])
        finally:
            if previous is None:
                ab._ETAT_COURANT.pop("etat", None)
            else:
                ab._ETAT_COURANT["etat"] = previous

    def test_live_publier_failure_is_retried_not_dropped(self):
        previous = ab._ETAT_COURANT.get("etat")
        state = {"live_outbox": [{"key": "x", "text": "message", "tries": 0, "next_t": 0}]}
        ab._ETAT_COURANT["etat"] = state
        try:
            with mock.patch.object(ab, "LIVE_SUJET", "test-sujet"), \
                 mock.patch.object(ab.urllib.request, "urlopen", side_effect=OSError("network down")):
                self.assertEqual(ab.traiter_file_live(state, maintenant=100), 0)
            self.assertEqual(len(state["live_outbox"]), 1)
            self.assertEqual(state["live_outbox"][0]["tries"], 1)
            self.assertGreater(state["live_outbox"][0]["next_t"], 100)
        finally:
            if previous is None:
                ab._ETAT_COURANT.pop("etat", None)
            else:
                ab._ETAT_COURANT["etat"] = previous


if __name__ == "__main__":
    unittest.main()


class BandePulsion(unittest.TestCase):
    def test_pulsion_sans_info(self):
        for f in ("🎙 ÇA BOUGE !\n🟠 BTC : 65 560\n🔴 Les vendeurs accélèrent", "🎙 GROSSE MÈCHE !\n🥇 GOLD : 4 012"):
            t = ab.texte_bande_flash(f)
            self.assertTrue(t.startswith("BULLE:"))
            self.assertIn("lien en bio", t.lower())
            self.assertIsNone(re.search(r"\d{2,}|BTC|GOLD|NASDAQ|LONG|SHORT|Telegram", t))

    def test_menu_chaine(self):
        texte, kb = ab.menu_chaine({}, "BTC")
        self.assertIn("ALIGN", texte)
        urls = [b["url"] for l in json.loads(kb)["inline_keyboard"] for b in l]
        self.assertIn(ab.BOT_LIEN, urls)
        self.assertIn(ab.LIVE_LIEN, urls)
        self.assertIn(ab.LIENS_CHAINES["GOLD"], urls)
        self.assertNotIn(ab.LIENS_CHAINES["BTC"], urls)


class BandeNews(unittest.TestCase):
    def test_etapes(self):
        vus = {}
        for reste, attendu in ((15 * 60, "n15"), (10 * 60, "n10"), (5 * 60, "n5"), (-5 * 60, "nreac"), (-20 * 60, "nfin"), (40 * 60, None)):
            e, t = ab.textes_live_news("CPI (inflation)", reste)
            self.assertEqual(e, attendu)
            if t:
                self.assertIn("lien en bio", t)
                self.assertNotIn("Telegram", t)
        self.assertIn("SL et ton TP", ab.textes_live_news("CPI", 600)[1])

    def test_une_fois_par_etape(self):
        envoye = []
        etat = {}
        with mock.patch.object(ab, "calendrier", return_value=[{"t": 10_000, "titre": "NFP"}]), \
             mock.patch.object(ab, "live_publier", side_effect=lambda t: envoye.append(t) or True):
            ab.live_news(etat, 10_000 - 14 * 60)
            ab.live_news(etat, 10_000 - 13 * 60)
            ab.live_news(etat, 10_000 - 9 * 60)
        self.assertEqual(len(envoye), 2)


class MarcheFermeJamaisEnPosition(unittest.TestCase):
    def test_gold_ferme_avec_trade_perime(self):
        import datetime
        from zoneinfo import ZoneInfo
        samedi = datetime.datetime(2026, 11, 14, 12, 0, tzinfo=ZoneInfo("America/Chicago")).timestamp()
        r = {"m1": [{"c": 4000.0}]}
        for m in ("GOLD", "NASDAQ"):
            p = ab.proximite_marche(m, r, {"trade": {"d": 1}}, samedi)
            self.assertEqual(p["classe"], "ferme")
        self.assertEqual(ab.proximite_marche("BTC", r, {"trade": {"d": 1}}, samedi)["classe"], "position")


class CarteEntreeClaire(unittest.TestCase):
    def test_pas_de_jaune_et_meme_bougie_que_le_chrono(self):
        o = {"e": 100.0, "za": 99.0, "zb": 101.0, "tp1": 95.0, "src": "FVG"}
        with unittest.mock.patch.object(ab, "timeframe_attendu", return_value="5m"):
            t = ab.avant_entree("BTC", {}, {}, o, -1)
        self.assertNotIn("jaune", t.lower()); self.assertNotIn("15 min", t)
        self.assertIn("bougie 5 min CLÔTURE SOUS l'étiquette « ENTRÉE »", t)
        self.assertIn("on n'entre PAS encore", t); self.assertIn("VALIDÉ 🔴 SHORT", t)
        self.assertIn("CLOSE BELOW", ab.traduire(t))


class ZoneMangee(unittest.TestCase):
    """Même lecture que l'indicateur v87 : la partie vide de la zone = mangée par les bougies."""
    def b(self, h, l):
        return {"h": h, "l": l, "o": l, "c": h}

    def test_pourcentages(self):
        self.assertEqual(ab.zone_mangee([self.b(95, 90)], 100, 110), 0)            # pas encore touchée
        self.assertEqual(ab.zone_mangee([self.b(105, 90)], 100, 110), 50)          # la moitié du bas mangée (SHORT)
        self.assertEqual(ab.zone_mangee([self.b(120, 90)], 110, 100), 100)         # traversée (ordre des bornes indifférent)
        self.assertIsNone(ab.zone_mangee([], 100, 110))

    def test_carte_entree_affiche_le_pourcentage(self):
        o = {"e": 100.0, "za": 100.0, "zb": 110.0}
        r = {"b5": [self.b(104, 95)] * 3 + [self.b(1, 1)]}                         # la dernière bougie (en formation) est ignorée
        with unittest.mock.patch.object(ab, "timeframe_attendu", return_value="5m"):
            t = ab.avant_entree("BTC", r, {}, o, -1)
        self.assertIn("🍽 Zone mangée à 40 %", t)
        self.assertIn("Zone eaten 40 %", ab.traduire(t))


class ScalpVautLeCoup(unittest.TestCase):
    def test_regle(self):
        si = {"d": 1, "e": 100.0, "sl": 95.0, "tp": 115.0, "rr": 3.0, "voy": 3, "atr": 4.0}
        self.assertTrue(ab.scalp_vaut_le_coup(si))
        self.assertFalse(ab.scalp_vaut_le_coup(dict(si, rr=1.5)))                 # gain < 2 × risque
        self.assertFalse(ab.scalp_vaut_le_coup(dict(si, atr=10.0)))               # trop court (< 2 ATR)
        self.assertIn("le bot le prend", "\n".join(ab.texte_scalp("BTC", si, -1)))
        self.assertIn("ne le prend pas", "\n".join(ab.texte_scalp("BTC", dict(si, rr=1.5), -1)))


class LeconsIA(unittest.TestCase):
    def test_lecons_relues_et_pause_apres_2_sl(self):
        etat = {}
        pr = {"d": 1, "type": "repli"}
        self.assertFalse(ab.noter_lecon(etat, "BTC", pr, -1.0, "Entrée trop tôt, attendre la clôture"))
        self.assertTrue(ab.noter_lecon(etat, "BTC", pr, -0.5, "Zone déjà mangée à 100 %"))
        self.assertTrue(ab.en_pause(etat, "BTC")); self.assertFalse(ab.en_pause(etat, "GOLD"))
        self.assertTrue(any("trop tôt" in x for x in ab.lecons_pour("BTC")))
        ab.noter_lecon(etat, "BTC", pr, 2.0, "TP propre")
        self.assertEqual(etat["serie_sl"]["BTC"], 0)
        with unittest.mock.patch.object(ab, "_envoi_sur") as env:
            ab.auto_entree(etat, "BTC", {"d": 1, "e": 1, "sl": 0.5, "tp1": 3})   # en pause : aucun ordre
        env.assert_not_called()
        ab.LECONS[:] = []
