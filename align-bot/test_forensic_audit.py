import sys
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import align_bot


class ForensicAuditSnapshotTest(unittest.TestCase):
    def test_snapshot_keeps_timeframes_and_tradingview_freshness_separate(self):
        etat = {}
        cle = {"trade": {"d": 1, "e": 100.0, "sl": 98.0, "tp1": 104.0, "tp2": 106.0,
                         "cree": 1700000000, "statut": "entree", "src": "test"}}
        r = {
            "t": 1700000300, "m1": [{"c": 101.0}], "confirme": 1,
            "dirs": [1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1],
            "rsis": [55.0] * 11,
            "tv_indicator_mtf": {
                "available": True, "activeTimeframe": "H4", "activeTimeframeAgeMs": 1200,
                "receivedTimeframes": ["M5", "H1", "H4"],
                "snapshots": {"H4": {"fresh": True, "confirmed": True,
                    "robotV12": {"signal": "LONG", "entry": 100.0, "sl": 98.0, "tp": 104.0,
                                 "long_score": 8, "short_score": 2}}}
            }
        }
        align_bot.capturer_snapshot_audit(etat, "BTC", r, cle, ["LONG confirmé"])
        snap = etat["audit_mtf"]["BTC"][0]
        self.assertEqual(snap["mtf"]["4h"]["direction"], 1)
        self.assertEqual(snap["mtf"]["1h"]["direction"], 1)
        self.assertEqual(snap["tradingview"]["activeTimeframe"], "H4")
        self.assertTrue(snap["tradingview"]["snapshots"]["H4"]["fresh"])
        self.assertEqual(snap["trade"]["audit_key"], align_bot.cle_audit_trade("BTC", cle["trade"]))
        self.assertIn("LONG confirmé", snap["messages"])

    def test_snapshot_history_is_bounded(self):
        etat = {"audit_mtf": {"GOLD": [{"t": i} for i in range(601)]}}
        r = {"t": 1000, "m1": [{"c": 1.0}], "dirs": [], "rsis": []}
        align_bot.capturer_snapshot_audit(etat, "GOLD", r, {})
        self.assertEqual(len(etat["audit_mtf"]["GOLD"]), 600)
        self.assertEqual(etat["audit_mtf"]["GOLD"][-1]["t"], 1000)


    def test_gold_and_nasdaq_reversal_watch_remains_available(self):
        # M5/M15 turn bullish while H1/H4 remain bearish: observation only.
        dirs = [0] * 11
        dirs[2], dirs[4], dirs[7], dirs[9] = 1, 1, -1, -1
        b15 = [{"t": i * 900, "o": 99.0, "h": 101.0, "l": 98.0, "c": 100.0, "v": 10.0}
               for i in range(42)]
        b15[-2]["v"] = 20.0
        b1 = [{"h": 105.0, "l": 95.0} for _ in range(6)]
        b4 = [{"h": 110.0, "l": 90.0} for _ in range(6)]
        r = {"dirs": dirs, "b5": [{"h": 101.0, "l": 98.0} for _ in range(7)],
             "b15": b15, "b1h": b1, "b4h": b4, "m1": [{"c": 100.0}], "t": 999999}
        for market in ("GOLD", "NASDAQ"):
            cle = {}
            alert = align_bot.retournement_marche(market, r, cle)
            self.assertIsNotNone(alert, market)
            self.assertIn("RETOURNEMENT EN OBSERVATION", alert)
            self.assertIn("PAS DE POSITION", alert)



    def test_pre_entry_order_is_recorded_without_fake_trade_identity(self):
        etat = {}
        cle = {"ordre": {"d": -1, "e": 200.0, "sl": 204.0, "tp1": 192.0,
                         "tp2": 188.0, "src": "FVG", "za": 199.0, "zb": 201.0}}
        r = {"t": 1700000400, "m1": [{"c": 200.5}], "dirs": [], "rsis": []}
        align_bot.capturer_snapshot_audit(etat, "NASDAQ", r, cle)
        plan = etat["audit_mtf"]["NASDAQ"][0]["trade"]
        self.assertEqual(plan["plan_source"], "ordre_en_preparation")
        self.assertEqual(plan["src"], "FVG")
        self.assertNotIn("audit_key", plan)



    def test_agent_checks_reversal_while_gold_and_nasdaq_trade_is_open(self):
        alert = "↩️ RETOURNEMENT LONG ⬆️ — test"
        r = {
            "m1": [{"t": 1000, "o": 100.0, "h": 101.0, "l": 99.0, "c": 100.0}],
            "r5": [50.0, 50.0], "confirme": -1, "t": 1000,
            "posD": 0.5, "posW": 0.5, "dirs": [0] * 11,
            "atr": 1.0, "b15": [{"t": 900, "c": 100.0}],
            "b5": [{"t": 900, "o": 100.0, "h": 101.0, "l": 99.0, "c": 100.0}]
        }
        for market in ("GOLD", "NASDAQ"):
            trade = {"d": -1, "e": 100.0, "sl": 102.0, "tp1": 96.0, "tp2": 94.0,
                     "statut": "entree", "cree": 1000, "encore": 1, "be_dit": True}
            cle = {"trade": trade}
            with unittest.mock.patch.object(align_bot, "manipulation", return_value=None), \
                 unittest.mock.patch.object(align_bot, "meche_suspecte", return_value=None), \
                 unittest.mock.patch.object(align_bot, "niveaux_cles", return_value=None), \
                 unittest.mock.patch.object(align_bot, "resistance_fvg", return_value=None), \
                 unittest.mock.patch.object(align_bot, "suivre_apres_sl", return_value=None), \
                 unittest.mock.patch.object(align_bot, "radar_climax", return_value=None), \
                 unittest.mock.patch.object(align_bot, "retournement_marche", return_value=alert) as watch, \
                 unittest.mock.patch.object(align_bot, "alerte_retournement", return_value=None), \
                 unittest.mock.patch.object(align_bot, "frole_tp", return_value=None), \
                 unittest.mock.patch.object(align_bot, "retour_entree", return_value=None):
                out = align_bot.agent(market, r, cle, "")
            watch.assert_called_once_with(market, r, cle)
            self.assertTrue(any(alert in str(item) for item in out), market)



    def test_reversal_observation_is_forwarded_to_live_banner(self):
        message = "👀 RETOURNEMENT EN OBSERVATION — GOLD\\nM5 et M15 se retournent."
        with unittest.mock.patch.object(align_bot, "live_bande") as banner:
            align_bot.live_annonces({}, "GOLD", [message])
        banner.assert_called_once()
        args, kwargs = banner.call_args
        self.assertIn("petites unités se retournent", args[1])
        self.assertEqual(args[2], "retGOLD")



    def test_breakout_with_reward_risk_below_minimum_is_not_opened(self):
        r = {
            "m1": [{"t": 1000, "o": 100.0, "h": 101.0, "l": 99.0, "c": 100.0}],
            "r5": [50.0, 50.0], "confirme": 1, "t": 1000,
            "posD": 0.5, "posW": 0.5, "b5": [], "atr": 1.0,
            "dirs": [1] * 11
        }
        low_rr_plan = {"d": 1, "e": 100.0, "sl": 99.0, "tp1": 101.0, "tp2": 102.0,
                       "rr": 1.0, "t15": 900, "src": "cassure 5 min"}
        cle = {}
        with unittest.mock.patch.object(align_bot, "manipulation"), \
             unittest.mock.patch.object(align_bot, "meche_suspecte"), \
             unittest.mock.patch.object(align_bot, "niveaux_cles"), \
             unittest.mock.patch.object(align_bot, "resistance_fvg"), \
             unittest.mock.patch.object(align_bot, "suivre_apres_sl"), \
             unittest.mock.patch.object(align_bot, "radar_climax", return_value=None), \
             unittest.mock.patch.object(align_bot, "retournement_marche", return_value=None), \
             unittest.mock.patch.object(align_bot, "bloque_dw", return_value=False), \
             unittest.mock.patch.object(align_bot, "plan_cassure", return_value=low_rr_plan), \
             unittest.mock.patch.object(align_bot, "point_entree", return_value=None), \
             unittest.mock.patch.object(align_bot, "memoire_refuse") as refuse:
            out = align_bot.agent("BTC", r, cle, "")
        self.assertNotIn("trade", cle)
        refuse.assert_not_called()
        self.assertTrue(any("pas de FVG" in str(x) for x in out))



    def test_telegram_pause_copy_explains_on_demand_analysis(self):
        source = (Path(__file__).parent / "align_bot.py").read_text(encoding="utf-8")
        start = source.index("def menu_bot(etat, cid):")
        end = source.index("\ndef regler_bot(etat, cid, on):", start)
        menu = source[start:end]
        self.assertIn("Plus de nouvelles alertes automatiques", menu)
        self.assertIn("Faire une analyse", menu)
        self.assertNotIn("Tu reçois toujours les positions", menu)
        self.assertIn("Suspendre les alertes", menu)
        self.assertIn("Réactiver les alertes", menu)



    def test_new_telegram_subscriber_starts_with_no_markets_and_must_opt_in(self):
        etat = {"coach_pending": ["new-user"]}
        with unittest.mock.patch.object(align_bot, "_envoi_sur") as send:
            align_bot.menu_marches(etat, "new-user")
        self.assertEqual(align_bot.marches_choisis(etat, "new-user"), set())
        align_bot.basculer_marche(etat, "new-user", "GOLD")
        self.assertEqual(align_bot.marches_choisis(etat, "new-user"), {"GOLD"})
        send.assert_called_once()

    def test_legacy_telegram_subscriber_keeps_existing_all_markets_default(self):
        etat = {}
        self.assertEqual(align_bot.marches_choisis(etat, "legacy-user"), set(align_bot.MARCHES))

    def test_market_follow_cannot_be_confirmed_without_selection(self):
        etat = {"marches_par_chat": {"new-user": []}}
        with unittest.mock.patch.object(align_bot, "autorise", return_value=True), \
             unittest.mock.patch.object(align_bot, "_envoi_sur") as send, \
             unittest.mock.patch.object(align_bot, "selectionner_marches_suivi") as save:
            ok = align_bot.valider_et_suivre_marches(etat, "new-user", 123)
        self.assertFalse(ok)
        save.assert_not_called()
        self.assertIn("Coche au moins un marché", send.call_args.kwargs["text"])



if __name__ == "__main__":
    unittest.main()
