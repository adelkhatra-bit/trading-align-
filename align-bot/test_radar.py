"""RADAR ALIGN : un seul message par personne, édité sur place ; cassures fusionnées ; news réservées au VIP."""
import os
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def props_test():
    return [
        dict(m="GOLD", prix=3995.0, atr_n=0.8, classe="proche", rang=1, d=-1, za=3990.05, zb=4012.54, dist=4.95,
             action="clôture 1h sous 4001,30", au_dessus=False),
        dict(m="BTC", prix=60000.0, atr_n=3.2, classe="en_approche", rang=2, d=-1, za=61000, zb=61500, dist=1000,
             action="x", au_dessus=True),
    ]


DERNIERS = {"GOLD": {"strat": "SWING", "bear": 11, "plan_fige": {"d": -1, "e": 4000.0, "sl": 4019.86, "tp1": 3895.54}},
            "BTC": {"bear": 7}}


class TexteRadarTest(unittest.TestCase):
    def test_vip_focus_et_niveaux(self):
        t = ab.texte_radar(props_test(), DERNIERS, vip=True, now=time.time())
        self.assertIn("🎯 FOCUS : 🥇 GOLD — prépare-toi", t.split("\n")[0])
        for morceau in ("SHORT", "SWING", "Zone d'entrée", "SL", "TP1", "J'attends", "11/11", "2️⃣ 🟠 BTC"):
            self.assertIn(morceau, t)
        self.assertNotIn("SHORT ⬇️ · pas de plan", t)          # pas de sens affiché pour un marché sans plan

    def test_gratuit_sans_niveaux(self):
        t = ab.texte_radar(props_test(), DERNIERS, vip=False, now=time.time())
        self.assertIn("🔒 Entrée, SL, TP : VIP", t)
        self.assertIn("SHORT", t)                               # le sens reste visible côté gratuit
        for interdit in ("4019", "3895", "Zone d'entrée :", "J'attends"):
            self.assertNotIn(interdit, t)

    def test_rien_de_proche(self):
        p = [dict(m="NASDAQ", prix=1.0, atr_n=99.0, classe="sans_plan", rang=5)]
        t = ab.texte_radar(p, {}, vip=True, now=time.time())
        self.assertIsNone(t)


class AlignementRequisTest(unittest.TestCase):
    def test_btc_proche_mais_pas_aligne_n_est_pas_prepare_toi(self):
        d = {"BTC": {"bull": 6}, "GOLD": {"bear": 9}}
        p = [dict(m="BTC", prix=1.0, atr_n=0.9, classe="proche", rang=1, d=1, za=1, zb=2, dist=0.5, action="x", au_dessus=True),
             dict(m="GOLD", prix=1.0, atr_n=2.8, classe="en_approche", rang=2, d=-1, za=1, zb=2, dist=3, action="y", au_dessus=False)]
        t = ab.texte_radar(p, d, vip=True, now=time.time())
        self.assertNotIn("prépare-toi", t)
        self.assertIn("BTC — proche, alignement pas encore atteint", t)
        d["BTC"]["bull"] = 8
        self.assertIn("BTC — prépare-toi", ab.texte_radar(p, d, vip=True, now=time.time()))

    def test_gold_pret_passe_devant_un_btc_non_aligne(self):
        d = {"BTC": {"bull": 6}, "GOLD": {"bear": 10}}
        p = [dict(m="BTC", prix=1.0, atr_n=0.2, classe="dans_zone", rang=0, d=1, za=1, zb=2, dist=0, action="x", au_dessus=True),
             dict(m="GOLD", prix=1.0, atr_n=1.2, classe="proche", rang=1, d=-1, za=1, zb=2, dist=1, action="y", au_dessus=False)]
        self.assertIn("🎯 FOCUS : 🥇 GOLD — prépare-toi", ab.texte_radar(p, d, vip=True, now=time.time()).split("\n")[0])


class PlanIndicateurSurTest(unittest.TestCase):
    """Cas réel GOLD 12/11 18:25 : zone 3898,43 → 3962,74 · SL 3977,68 · TP1 3888,99 · TP2 3910,44 (TP2 avant TP1)."""
    def test_zone_reduite_a_sa_partie_rentable(self):
        za, zb = ab.zone_rentable(-1, 3898.43, 3962.74, 3977.68, 3888.99)
        self.assertAlmostEqual(zb, 3962.74)
        self.assertGreater(za, 3935)                                     # plus d'entrée à 3898 (79 pts de risque pour 10 de gain)
        self.assertGreaterEqual((za - 3888.99) / (3977.68 - za), ab.GAIN_MIN - 1e-9)

    def test_zone_sans_partie_rentable(self):
        self.assertEqual(ab.zone_rentable(-1, 3898.0, 3905.0, 3977.0, 3889.0), (None, None))

    def test_tp2_avant_le_tp1_n_est_pas_affiche(self):
        self.assertFalse(ab.tp2_affichable(-1, 3888.99, 3910.44))
        self.assertTrue(ab.tp2_affichable(-1, 3888.99, 3850.0))

    def test_radar_prend_le_plan_de_l_indicateur(self):
        r = {"plan_fige": {"d": -1, "e": 3962.74, "sl": 3977.68, "tp1": 3888.99}}
        es = ab.radar_entree_sl(r, -1, 3898.43, 3962.74)
        self.assertEqual((es["e"], es["sl"], es["tp1"]), (3962.74, 3977.68, 3888.99))
        self.assertGreater(es["za"], 3935)

    def test_carte_cloture_meme_decision_chiffres_differents(self):
        a = "🥇 GOLD · 3871\n🔴 PAS D'ENTRÉE\n🟡 Zone 3898,43–3962,74 · SL 3977,68 · TP1 3888,99"
        b = "🥇 GOLD · 3873\n🔴 PAS D'ENTRÉE\n🟡 Zone 3896,53–3961,04 · SL 3975,98 · TP1 3887,18"
        self.assertEqual(ab.signature_cloture(a), ab.signature_cloture(b))



class RadarPineV25SourceTest(unittest.TestCase):
    def plan(self, confirmed=True, triggered=False, price_in_zone=True):
        return {
            "available": True, "confirmed": confirmed, "direction": 1,
            "entry": 101.0, "sl": 99.0, "tp1": 104.0, "tp2": 106.0,
            "zone_low": 100.0, "zone_high": 102.0, "decision": 101.0,
            "price": 101.25, "price_in_zone": price_in_zone, "triggered": triggered,
            "strategy": "DAY", "entry_timeframe": "M5",
        }

    def market(self):
        snapshots = {
            tf: {"fresh": True, "direction": 1, "price": 101.25}
            for tf, _ in ab.TELEGRAM_TF_VIEWS
        }
        return {
            "require_tv_bridge": True,
            "tv_indicator_mtf": {"available": True, "activeTimeframe": "M15", "snapshots": snapshots},
            "m1": [{"c": 999.0}], "atr": 1.0,
            "dirPlan": -1, "zone_pine": {"za": 200.0, "zb": 210.0, "zmil": 205.0},
            "strat": "SWING", "bull": 0, "bear": 11,
        }

    def test_proximite_uses_tv_price_and_pine_zone_not_local_fallback(self):
        r = self.market()
        with mock.patch.object(ab, "plan_indicateur", return_value=self.plan()):
            p = ab.proximite_marche("BTC", r, {}, now=1_000_000.0)
        self.assertEqual((p["prix"], p["d"], p["za"], p["zb"]), (101.25, 1, 100.0, 102.0))
        self.assertEqual(p["strategy"], "DAY")
        self.assertEqual(p["entry_timeframe"], "M5")
        self.assertTrue(p["pine_confirmed"])
        self.assertIn("5 min", p["action"])
        self.assertIn("101", p["action"])

    def test_un_plan_pine_non_confirme_ne_declenche_pas_prepare_toi(self):
        r = self.market()
        with mock.patch.object(ab, "plan_indicateur", return_value=self.plan(confirmed=False)):
            p = ab.proximite_marche("BTC", r, {}, now=1_000_000.0)
            es = ab.radar_entree_sl(r, 1, 200.0, 210.0)
        self.assertEqual((p["classe"], p["rang"]), ("sans_plan", 5))
        self.assertIsNone(es)
        self.assertFalse(ab._radar_pret({"m": "BTC", "rang": 1, "pine_confirmed": False, "d": 1}, {"BTC": r}))

    def test_radar_entree_sl_uses_exact_pine_values_and_never_calls_local_calculation(self):
        r = self.market()
        with mock.patch.object(ab, "plan_indicateur", return_value=self.plan()), \
             mock.patch.object(ab, "pine_entree", side_effect=AssertionError("local plan must not be used")):
            es = ab.radar_entree_sl(r, 1, 200.0, 210.0)
        self.assertEqual((es["e"], es["sl"], es["tp1"], es["tp2"]), (101.0, 99.0, 104.0, 106.0))
        self.assertEqual((es["za"], es["zb"], es["ut"]), (100.0, 102.0, "M5"))
        self.assertEqual(es["src"], "Pine v25 / ROBOT V12")

    def test_bridge_prepare_gate_uses_pine_confirmation_not_local_bull_bear(self):
        r = self.market()
        self.assertTrue(ab._radar_pret({"m": "BTC", "rang": 1, "pine_confirmed": True, "d": 1}, {"BTC": r}))
        self.assertFalse(ab._radar_pret({"m": "BTC", "rang": 1, "pine_confirmed": False, "d": 1}, {"BTC": {**r, "bull": 11}}))

    def test_alignment_count_comes_from_tradingview_snapshots(self):
        r = self.market()
        snapshots = r["tv_indicator_mtf"]["snapshots"]
        for i, (tf, _) in enumerate(ab.TELEGRAM_TF_VIEWS):
            snapshots[tf]["direction"] = 1 if i < 8 else -1
        self.assertEqual(ab._radar_n_ut(r, 1), 8)
        self.assertEqual(ab._radar_n_ut(r, -1), len(ab.TELEGRAM_TF_VIEWS) - 8)

    def test_vip_radar_displays_pine_entry_sl_tp1_tp2_and_strategy(self):
        r = self.market()
        p = dict(m="BTC", prix=101.25, atr_n=0.5, classe="proche", rang=1, d=1,
                 za=100.0, zb=102.0, dist=0.5, action="clôture 5 min au-dessus de 101",
                 au_dessus=False, strategy="DAY", entry_timeframe="M5", pine_confirmed=True)
        with mock.patch.object(ab, "plan_indicateur", return_value=self.plan()):
            t = ab.texte_radar([p], {"BTC": r}, vip=True, now=1_000_000.0)
        for morceau in ("Pine v25 / ROBOT V12", "INTRADAY", "TP1", "TP2", "déclencheur M5"):
            self.assertIn(morceau, t)

    def test_live_coach_names_the_real_strategy_line_without_publishing_price(self):
        p = dict(m="BTC", d=1, rang=1, pine_confirmed=True, pine_triggered=False,
                 price_in_zone=False, entry_timeframe="M5", strategy="DAY")
        messages = []
        with mock.patch.object(ab, "classer_marches", return_value=[p]), \
             mock.patch.object(ab, "live_bande", lambda etat, texte, *a, **k: messages.append(texte)):
            ab.live_prepare_toi({}, {"BTC": {"require_tv_bridge": True}}, now=1_000_000.0)
        self.assertIn("prépare-toi", messages[0])
        self.assertIn("clôture 5 min au-dessus de la ligne de décision", messages[0])
        self.assertIn("niveaux exacts en privé", messages[0])
        self.assertNotIn("101.25", messages[0])


class RadarIaTest(unittest.TestCase):
    """L'IA rédige l'annonce « prépare-toi » (phrases variées) ; les niveaux restent ceux du bot ; jamais d'IA hors alerte."""
    def test_ia_seulement_a_l_alerte_et_texte_garde_pendant_les_editions(self):
        appels, envois = [], []
        def faux_ia(etat, consigne, data, **kw):
            appels.append(kw.get("cle_cache")); return "🔔 GOLD se réveille, prépare-toi\n🎯 Je vise 3905,80 en SHORT\n🕯 Regarde la 1h"
        def tg(methode, **kw):
            envois.append((methode, kw)); return {"ok": True, "result": {"message_id": len(envois)}}
        props = props_test()
        derniers = {**DERNIERS, "GOLD": {**DERNIERS["GOLD"], "m1": [{"c": 3995.0}]}}
        with mock.patch.object(ab, "ia", faux_ia), mock.patch.object(ab, "donnees_ia", lambda *a, **k: {}), \
             mock.patch.object(ab, "telegram", tg), mock.patch.object(ab, "_envoi_sur", lambda cid, **kw: tg("sendMessage", chat_id=cid, **kw)), \
             mock.patch.object(ab, "autorise", lambda *a: True), mock.patch.object(ab, "marches_choisis", lambda e, c: {"GOLD", "BTC"}), \
             mock.patch.object(ab, "classer_marches", lambda d, e, c, n=None: props):
            etat = {"auto": {"GOLD": ["42"]}}
            ab.radar_tick(etat, {"42"}, derniers, now=1_000_000.0)            # GOLD prêt : alerte → 1 appel IA
            self.assertEqual(len(appels), 1)
            self.assertIn("GOLD se réveille", envois[0][1]["text"])
            self.assertIn("Zone d'entrée", envois[0][1]["text"])               # les niveaux calculés restent affichés
            props[0] = dict(props[0], atr_n=0.5, dist=2.0)
            ab.radar_tick(etat, {"42"}, derniers, now=1_000_000.0 + 300)      # simple édition : aucune nouvelle IA, phrases gardées
            self.assertEqual(len(appels), 1)

    def test_ia_qui_contredit_le_sens_est_jetee(self):
        with mock.patch.object(ab, "ia", lambda *a, **k: "📈 Ça va monter, prends un LONG"), mock.patch.object(ab, "donnees_ia", lambda *a, **k: {}):
            self.assertIsNone(ab.intro_ia_radar({}, "GOLD", {}, {}, props_test()[0], None))


class RadarTickTest(unittest.TestCase):
    def setUp(self):
        self.appels = []
        self.mid = 100

        def tg(methode, **kw):
            self.appels.append((methode, kw))
            self.mid += 1
            return {"ok": True, "result": {"message_id": self.mid}}
        self.p = [mock.patch.object(ab, "telegram", tg),
                  mock.patch.object(ab, "_envoi_sur", lambda cid, **kw: tg("sendMessage", chat_id=cid, **kw)),
                  mock.patch.object(ab, "autorise", lambda *a: True),
                  mock.patch.object(ab, "marches_choisis", lambda e, c: {"GOLD", "BTC", "NASDAQ"}),
                  mock.patch.object(ab, "classer_marches", lambda d, e, c, n=None: self.props)]
        for x in self.p:
            x.start()

    def tearDown(self):
        for x in self.p:
            x.stop()

    def test_un_seul_message_puis_edition(self):
        etat = {"auto": {"GOLD": ["42"]}}
        self.props = props_test()
        self.props[0] = dict(self.props[0], rang=2, classe="en_approche", atr_n=2.5)
        t0 = 1_000_000.0
        ab.radar_tick(etat, {"42"}, DERNIERS, now=t0)
        self.assertEqual([a[0] for a in self.appels], ["sendMessage"])
        self.assertEqual(self.appels[0][1].get("disable_notification"), "true")   # radar normal : sans son
        # même fond, 3 min plus tard : aucune action (pas de doublon, pas d'édition inutile)
        ab.radar_tick(etat, {"42"}, DERNIERS, now=t0 + 180)
        self.assertEqual(len(self.appels), 1)
        # le prix entre dans la zone d'un marché déjà en tête → nouveau message AVEC son, ancien supprimé
        self.props[0] = dict(self.props[0], rang=0, classe="dans_zone", atr_n=0.0, dist=0.0)
        ab.radar_tick(etat, {"42"}, DERNIERS, now=t0 + 400)
        methodes = [a[0] for a in self.appels]
        self.assertEqual(methodes[-2:], ["sendMessage", "deleteMessage"])
        self.assertNotIn("disable_notification", self.appels[-2][1])
        self.assertIn("prépare-toi", self.appels[-2][1]["text"])
        # oscillation : retour « en approche » puis de nouveau « dans la zone » 2 min après → pas de 2e alerte sonore
        self.props[0] = dict(self.props[0], rang=2, classe="en_approche", atr_n=2.0)
        ab.radar_tick(etat, {"42"}, DERNIERS, now=t0 + 530)
        self.props[0] = dict(self.props[0], rang=0, classe="dans_zone", atr_n=0.0)
        n = len(self.appels)
        ab.radar_tick(etat, {"42"}, DERNIERS, now=t0 + 660)
        self.assertFalse(any(a[0] == "sendMessage" for a in self.appels[n:]))
        self.assertTrue(all(a[0] == "editMessageText" for a in self.appels[n:]))

    def test_jamais_la_chaine(self):
        self.props = props_test()
        ab.radar_tick({"canal": "-100"}, {"-100"}, DERNIERS, now=1.0)
        self.assertEqual(self.appels, [])


class CassureFusionneeTest(unittest.TestCase):
    def test_hier_et_semaine_au_meme_niveau(self):
        b15 = [{"t": 0, "o": 3990, "h": 3992, "l": 3985, "c": 3990}, {"t": 900, "o": 3984, "h": 3985, "l": 3970, "c": 3975}]
        r = {"m1": [{"c": 3975}], "atr": 5.0, "b15": b15,
             "niv_cles": [(3981.18, "plus bas d'hier"), (3981.18, "plus bas de la semaine dernière"), (4050.0, "plus haut d'hier")]}
        out = []
        ab.niveaux_cles(out, "GOLD", r, {})
        cassures = [x for x in out if x.startswith("💥 CASSURE")]
        self.assertEqual(len(cassures), 1)
        self.assertIn("plus bas d'hier et de la semaine dernière", cassures[0])
        out2 = []
        ab.niveaux_cles(out2, "GOLD", r, {"nivc": {}})
        self.assertEqual(len([x for x in out2 if x.startswith("💥")]), 1)


class NewsVipTest(unittest.TestCase):
    def test_news_absentes_du_gratuit(self):
        with mock.patch.object(ab, "news_du_jour", lambda e, *a, **k: ["📰 NEWS USA DU JOUR", "x"]), \
             mock.patch.object(ab, "DERNIER_ETAT", {"cal": {}}), \
             mock.patch.object(ab, "verdict", lambda r, c: ("⛔ NON", "raison")), \
             mock.patch.object(ab, "alignement", lambda r: (0, 0)), \
             mock.patch.object(ab, "voyants_unites", lambda r: []), \
             mock.patch.object(ab, "objectifs_marche", lambda r, d: []), \
             mock.patch.object(ab, "zone_retournement_visee", lambda r, c: []), \
             mock.patch.object(ab, "direction_attente", lambda r: "AUCUNE"):
            r = {"m1": [{"c": 1.0}]}
            self.assertIn("NEWS USA DU JOUR", ab.texte_apercu("GOLD", r, {}, vip=True))
            self.assertNotIn("NEWS USA DU JOUR", ab.texte_apercu("GOLD", r, {}, vip=False))


class DureeHumaineTest(unittest.TestCase):
    def test_pas_confondu_avec_une_heure(self):
        self.assertEqual(ab.duree_humaine(570), "9 min 30 s")
        self.assertEqual(ab.duree_humaine(3900), "1 h 05")


if __name__ == "__main__":
    unittest.main()


class TestSensEnTete(unittest.TestCase):
    def test_sens_premiere_ligne_et_repli(self):
        t = ab.texte_radar(props_test(), DERNIERS, vip=True, now=time.time())
        l0 = t.split("\n")[0]
        self.assertTrue(l0.startswith("🔴 SHORT") or l0.startswith("🟢 LONG"), l0)
        self.assertIn("seulement au", t) if "DANS la zone" not in t else None

    def test_ligne_vers_zone(self):
        self.assertIn("remonte", ab.ligne_vers_zone(-1))
        self.assertIn("redescend", ab.ligne_vers_zone(1))
        self.assertIn("rejection", ab.ligne_vers_zone(-1, True))
        self.assertEqual(ab.traduire(ab.ligne_vers_zone(-1)), ab.ligne_vers_zone(-1, True))

class VerdictRobustnessTest(unittest.TestCase):
    def test_partial_market_context_waits_for_closed_mtf_data(self):
        self.assertIn("attente de donn\u00e9es MTF cl\u00f4tur\u00e9es", ab.prochaine({}, {}))

    def test_gold_without_confirmed_direction_waits_safely(self):
        r = {"market": "GOLD", "m1": [{"c": 100.0}]}
        with mock.patch.object(ab, "prochaine", return_value="\u23f3 En attente de confirmation"):
            title, reason = ab.verdict(r, {})
        self.assertIn("N'ENTRE PAS", title)
        self.assertIn("En attente de confirmation", reason)

    def test_ai_radar_skips_incomplete_market_summary_without_m1_price(self):
        self.assertIsNone(ab.intro_ia_radar({}, "GOLD", {}, {}, props_test()[0], None))

    def test_ai_radar_data_accepts_missing_confirmed_direction(self):
        r = {"m1": [{"c": 100.0}], "dirs": [0] * 11, "rsis": [50] * 11}
        with mock.patch.object(ab, "verdict", return_value=("N'ENTRE PAS", "En attente")), \
             mock.patch.object(ab, "profil_strategie", return_value=""), \
             mock.patch.object(ab, "plan_indicateur", return_value={"available": False}), \
             mock.patch.object(ab, "resume_volume", return_value={}), \
             mock.patch.object(ab, "timeframe_attendu", return_value="M5"), \
             mock.patch.object(ab, "prochaine_cloture_bougie", return_value=time.time() + 60), \
             mock.patch.object(ab, "lecons_pour", return_value=[]):
            data = ab.donnees_ia("GOLD", r, {})
        self.assertIsNone(data["niveau de cassure 5 min"])
