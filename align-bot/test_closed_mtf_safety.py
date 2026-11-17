"""Closed M5/M15/H1/H4 confirmation and feed freshness regressions."""
import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def bar(t, o=100.0, h=101.0, l=99.0, c=100.0, v=100):
    return {"t": t, "o": o, "h": h, "l": l, "c": c, "v": v}


def fresh_context(now=None):
    now = int(time.time()) if now is None else int(now)
    return {
        "m1": [bar(now - 30, c=100.0)],
        "b5": [bar(now - 600), bar(now - 300)],
        "b15": [bar(now - 1800), bar(now - 900)],
        "b1h": [bar(now - 7200), bar(now - 3600)],
        "b4h": [bar(now - 28800), bar(now - 14400)],
        "atr5": 1.0,
        "atr": 1.0,
    }


class ClosedMtfSafety(unittest.TestCase):
    def test_closed_directions_use_latest_closed_mtf_and_ignore_only_flagged_live_minute(self):
        series = {}
        for key in ab.UT:
            bars = [bar(i * 60, o=100 + i, h=101 + i, l=99 + i, c=100 + i) for i in range(60)]
            if key == "1":
                bars[-1]["forming"] = True
            elif key in {"5", "15", "30", "1h", "4h", "D"}:
                # Cette bougie est déjà clôturée par le contrat des adaptateurs de données.
                bars[-1] = bar(60 * 60, o=200, h=201, l=50, c=51)
            series[key] = bars
        dirs = ab.directions_cloturees(series)
        self.assertEqual(dirs[0], ab.etat_ut(series["1"][:-1])[0])
        for idx, key in ((2, "5"), (4, "15"), (7, "1h"), (9, "4h")):
            self.assertEqual(dirs[idx], ab.etat_ut(series[key])[0])

    def test_gold_nasdaq_require_all_four_closed_timeframes_for_long_and_short(self):
        for market in ("GOLD", "NASDAQ"):
            for direction in (1, -1):
                aligned = [direction] * 11
                self.assertEqual(ab.direction_confirmee_marche(market, aligned, direction), direction)
                for idx in (2, 4, 7, 9):
                    conflicting = aligned.copy()
                    conflicting[idx] = -direction
                    self.assertEqual(ab.direction_confirmee_marche(market, conflicting, direction), 0)

    def test_mtf_profile_uses_only_four_closed_directions_for_gold_nasdaq(self):
        for market in ("GOLD", "NASDAQ"):
            # Les lectures en formation sont toutes LONG, mais la dernière clôture M5 contredit le plan.
            forming = [1] * 11
            closed = [1] * 11
            closed[2] = -1
            profile = ab.profil_strategie({
                "market": market, "dirs": forming, "dirs_cloturees": closed
            })
            self.assertEqual(profile["mode"], "ATTENTE")
            self.assertEqual(profile["direction"], 0)
            self.assertFalse(profile["m5_aligne"])
            self.assertIn("M5", profile["contexte"])

            # Les clôtures sont toutes LONG : les bougies en formation SHORT ne doivent pas les écraser.
            profile = ab.profil_strategie({
                "market": market, "dirs": [-1] * 11, "dirs_cloturees": [1] * 11
            })
            self.assertEqual(profile["direction"], 1)
            self.assertTrue(profile["m5_aligne"])

            # Sans historique de clôtures, ne jamais retomber sur les directions en formation.
            profile = ab.profil_strategie({"market": market, "dirs": forming})
            self.assertEqual(profile["mode"], "ATTENTE")
            self.assertEqual(profile["direction"], 0)

    def test_gold_nasdaq_dashboard_uses_closed_directions_without_forming_fallback(self):
        for market in ("GOLD", "NASDAQ"):
            r = {
                "market": market,
                "dirs": [1] * 11,
                "dirs_cloturees": [0] * 11,
                "dirPlan": 0,
                "confirme": 0,
                "dirW": 0,
            }
            message = "\n".join(ab.strategie_mtf(r))
            self.assertIn("Tendance principale 4 h : 🟠➖", message)
            self.assertIn("Confirmation 1 h : 🟠➖", message)
            self.assertIn("Préparation 15 min : 🟠➖", message)
            self.assertIn("Timing 5 min : 🟠➖", message)
            self.assertIn("PROFIL RETENU : ATTENTE", message)
            self.assertIn("Stratégie : aucune", message)
            self.assertIn("aucune position avant la confluence des quatre clôtures", message)

    def test_gold_nasdaq_daily_weekly_block_cannot_be_bypassed_by_forming_trend(self):
        for market in ("GOLD", "NASDAQ"):
            r = {
                "market": market,
                "posD": 0.90,
                "posW": 0.50,
                "dirs": [1] * 11,
                "dirs_cloturees": [-1] * 11,
            }
            self.assertTrue(ab.bloque_dw(r, 1))
        # BTC conserve son comportement historique.
        btc = {
            "market": "BTC",
            "posD": 0.90,
            "posW": 0.50,
            "dirs": [1] * 11,
            "dirs_cloturees": [-1] * 11,
        }
        self.assertFalse(ab.bloque_dw(btc, 1))

    def test_mtf_confirmation_rejects_stale_m5_and_stale_m1(self):
        now = int(time.time())
        ctx = fresh_context(now)
        aligned = [1] * 11
        self.assertEqual(ab.direction_confirmee_marche("GOLD", aligned, 1, ctx), 1)
        ctx["b5"][-2]["t"] = now - 1000
        self.assertEqual(ab.direction_confirmee_marche("GOLD", aligned, 1, ctx), 0)
        ctx = fresh_context(now)
        ctx["m1"][-1]["t"] = now - 180
        self.assertEqual(ab.direction_confirmee_marche("NASDAQ", aligned, 1, ctx), 0)

    def test_mtf_confirmation_uses_tradingview_bridge_when_available(self):
        ctx = fresh_context()
        ctx["tv_indicator_mtf"] = {
            "available": True,
            "activeTimeframe": "M5",
            "snapshots": {
                "M5": {
                    "fresh": True,
                    "robotV12": {
                        "lecture_5m": "LONG",
                        "lecture_15m": "LONG",
                        "lecture_60m": "LONG",
                    },
                }
            },
        }
        self.assertEqual(ab.direction_confirmee_marche("GOLD", [1] * 11, 1, ctx), 1)
        ctx["tv_indicator_mtf"]["snapshots"]["M5"]["robotV12"]["lecture_60m"] = "SHORT"
        self.assertEqual(ab.direction_confirmee_marche("GOLD", [1] * 11, 1, ctx), 0)

    def test_gold_nasdaq_plan_direction_requires_all_four_fresh_closed_timeframes(self):
        now = int(time.time())
        ctx = fresh_context(now)
        aligned = [1] * 11
        for market in ("GOLD", "NASDAQ"):
            self.assertEqual(ab.direction_plan_autorisee(market, 1, aligned, ctx), 1)
            for idx in (2, 4, 7, 9):
                conflicting = aligned.copy()
                conflicting[idx] = -1
                self.assertEqual(ab.direction_plan_autorisee(market, 1, conflicting, ctx), 0)
            stale = fresh_context(now)
            stale["b5"][-2]["t"] = now - 1000
            self.assertEqual(ab.direction_plan_autorisee(market, 1, aligned, stale), 0)
        self.assertEqual(ab.direction_plan_autorisee("BTC", 1, [0] * 11, {}), 1)

    def test_tradingview_bridge_conflict_hides_gold_plan_and_markers(self):
        base = {
            "market": "GOLD", "dirs": [1] * 11, "dirs_cloturees": [1] * 11,
            "dirPlan": 1, "confirme": 1, "strat": "SWING",
            "zone_pine": {"za": 99.0, "zb": 101.0, "zmil": 100.0},
            "sigHaut": True, "sigBas": False, "nom": "ACHAT",
            "m1": [{"t": int(time.time()) - 10, "c": 100.0}],
        }
        bridge = {
            "available": True, "activeTimeframe": "M5",
            "snapshots": {"M5": {"fresh": True, "robotV12": {
                "lecture_5m": "SHORT", "lecture_15m": "LONG", "lecture_60m": "LONG"
            }}}
        }
        with unittest.mock.patch.object(ab, "analyser", return_value=base), \
             unittest.mock.patch.object(ab, "fetch_tv_mtf", return_value=bridge), \
             unittest.mock.patch.object(ab, "entree_sniper", return_value=None), \
             unittest.mock.patch.object(ab, "tendance_armee"), \
             unittest.mock.patch.object(ab, "annonce_proche", return_value=False), \
             unittest.mock.patch.object(ab, "news_txt", return_value=""), \
             unittest.mock.patch.object(ab, "contexte_macro", return_value=""):
            result = ab.analyse_marche({}, "XAUUSD")
        self.assertEqual(result["dirPlan"], 0)
        self.assertEqual(result["confirme"], 0)
        self.assertEqual(result["strat"], "")
        self.assertTrue(result["tv_bridge_conflict"])
        self.assertIsNone(result["zone_pine"])
        self.assertFalse(result["sigHaut"])
        self.assertFalse(result["sigBas"])

    def test_gold_nasdaq_verdict_names_m5_m15_conflict_instead_of_blame_h1(self):
        now = int(time.time())
        ctx = fresh_context(now)
        dirs = [1] * 11
        dirs[2] = -1
        r = dict(ctx, market="GOLD", dirs=dirs, dirs_cloturees=dirs.copy(), confirme=0,
                 rsis=[50.0] * 11, atr=1.0)
        titre, raison = ab.verdict(r, {})
        self.assertIn("N'ENTRE PAS", titre)
        self.assertIn("M5", raison)
        self.assertIn("M15", raison)
        self.assertNotIn("Le 1h ne confirme", raison)

    def test_strategy_blocks_gold_nasdaq_when_m5_or_m15_conflicts_but_preserves_btc(self):
        aligned = [1] * 11
        for market in ("GOLD", "NASDAQ"):
            strat, status, reason = ab.strategie_alignement(aligned, 1, 1, market)
            self.assertEqual(status, "CONFIRMÉ")
            self.assertTrue(strat)
            for idx in (2, 4):
                conflicting = aligned.copy()
                conflicting[idx] = -1
                strat, status, reason = ab.strategie_alignement(conflicting, 1, 1, market)
                self.assertEqual(strat, "")
                self.assertEqual(status, "EN ATTENTE")
                self.assertIn("M5 et M15", reason)
        btc = aligned.copy()
        btc[2] = -1
        self.assertEqual(ab.strategie_alignement(btc, 1, 1, "BTC")[1], "CONFIRMÉ")

    def test_sniper_blocks_short_term_countertrend(self):
        for market in ("GOLD", "NASDAQ"):
            for idx in (2, 4):
                dirs = [1] * 11
                dirs[idx] = -1
                proposal, reason = ab._sniper({
                    "market": market,
                    "dirPlan": 1,
                    "dirs_cloturees": dirs,
                    "dirs": dirs,
                })
                self.assertIsNone(proposal)
                self.assertIn("CONFLUENCE_M5_M15", reason)

    def test_armed_trend_is_cleared_when_m5_or_m15_turns_against_it(self):
        dirs = [1] * 11
        dirs[2] = -1
        r = {"market": "GOLD", "confirme": 0, "dirs_cloturees": dirs, "dirs": [1] * 11}
        state = {"arme": 1}
        ab.tendance_armee(r, state)
        self.assertEqual(r["confirme"], 0)
        self.assertEqual(state["arme"], 0)
        self.assertFalse(r.get("repli"))

    def test_agent_does_not_crash_or_signal_without_m1_feed(self):
        self.assertEqual(ab.agent("GOLD", {"m1": [], "r5": []}, {}, False), [])

    def test_btc_requires_fresh_tradingview_h1_when_production_bridge_is_required(self):
        ctx = fresh_context()
        ctx["require_tv_bridge"] = True
        ctx["tv_indicator_mtf"] = {
            "available": True,
            "activeTimeframe": "M5",
            "snapshots": {"M5": {"fresh": True, "robotV12": {
                "lecture_5m": "LONG", "lecture_15m": "LONG", "lecture_60m": "LONG"
            }}},
        }
        self.assertEqual(ab.direction_confirmee_marche("BTC", [1] * 11, 1, ctx), 1)
        ctx["tv_indicator_mtf"]["snapshots"]["M5"]["robotV12"]["lecture_60m"] = "SHORT"
        self.assertEqual(ab.direction_confirmee_marche("BTC", [1] * 11, 1, ctx), 0)
        ctx["tv_indicator_mtf"] = {"available": False}
        self.assertEqual(ab.direction_confirmee_marche("BTC", [1] * 11, 1, ctx), 0)

    def test_btc_keeps_historical_direction_filter(self):
        self.assertEqual(ab.direction_confirmee_marche("BTC", [0] * 11, 1), 1)

    def test_btc_signal_requires_closed_h1_h4_in_same_direction_as_setup(self):
        aligned = [1] * 11
        self.assertEqual(ab.direction_btc_confirmee(1, aligned), 1)
        conflict = aligned.copy()
        conflict[9] = -1
        self.assertEqual(ab.direction_btc_confirmee(1, conflict), 0)
        conflict = aligned.copy()
        conflict[7] = 0
        self.assertEqual(ab.direction_btc_confirmee(1, conflict), 0)

    def test_btc_live_closure_scheduler_uses_closed_h1_h4(self):
        r = {"market": "BTC", "dirs": [1] * 11, "dirs_cloturees": [1] * 11}
        r["dirs_cloturees"][9] = 0
        self.assertEqual(ab.timeframe_attendu(r, {}), "4h")

    def test_btc_armed_trend_cannot_override_closed_h1_h4_conflict(self):
        closed = [1] * 11
        closed[7] = -1
        r = {"market": "BTC", "confirme": 0, "dirPlan": 1,
             "dirs": [1] * 11, "dirs_cloturees": closed}
        state = {"arme": 1}
        ab.tendance_armee(r, state)
        self.assertEqual(r["confirme"], 0)
        self.assertEqual(state["arme"], 0)
        self.assertFalse(r.get("repli"))


    def test_gold_nasdaq_live_coach_counts_closed_directions_not_forming_ones(self):
        forming = [1] * 11
        closed = [-1] * 11
        now = int(time.time())
        r = {
            "market": "GOLD", "confirme": -1, "dirs": forming,
            "dirs_cloturees": closed, "m1": [bar(now - 10, c=100.0)],
            "sqzs": [0] * 11, "b15": [], "b5": [],
        }
        message = ab.texte_coach_live(
            "GOLD", bar(now - 900, o=101.0, h=102.0, l=99.0, c=100.0), r, {}
        )
        self.assertIn("📉 Unités : 7/7 ⬇️", message)
        self.assertIn("🔴 baisse", message)

    def test_live_ai_context_uses_four_closed_timeframes_for_gold_nasdaq(self):
        r = {
            "dirPlan": -1, "dirs": [1] * 11, "dirs_cloturees": [-1] * 11,
            "m1": [bar(int(time.time()) - 10, c=100.0)],
            "b15": [], "b15_long": [], "b1h": [], "b1h_long": [],
            "b4h": [], "b4h_long": [], "niveaux": [],
        }
        context = ab.contexte_technique_live({"GOLD": r})["marches"]["GOLD"]
        self.assertEqual(context["biais_plan"], "baissier")
        self.assertEqual(context["confirmation_m5_m15_h1_h4"], "quatre clôtures alignées à la baisse")
        self.assertEqual(context["lecture_mtf_cloturee"], {"M5": -1, "M15": -1, "H1": -1, "H4": -1})
        self.assertEqual(context["unites_haussieres_sur_11"], 0)
        self.assertEqual(context["unites_baissieres_sur_11"], 11)


    def test_gold_nasdaq_scheduler_names_m5_or_m15_when_that_is_the_blocker(self):
        dirs = [1] * 11
        r = {"market": "GOLD", "dirs_cloturees": dirs.copy(), "confirme": 0}
        r["dirs_cloturees"][2] = -1
        self.assertEqual(ab.timeframe_attendu(r, {}), "5m")
        r["dirs_cloturees"][2] = 1
        r["dirs_cloturees"][4] = -1
        self.assertEqual(ab.timeframe_attendu(r, {}), "15m")

    def test_btc_scheduler_waits_for_new_setup_not_an_unneeded_h1_close(self):
        dirs = [1] * 11
        r = {"market": "BTC", "dirs_cloturees": dirs, "confirme": 0, "dirPlan": -1}
        self.assertEqual(ab.timeframe_attendu(r, {}), "15m")

    def test_gold_nasdaq_next_closure_uses_closed_h1_h4_not_forming_candles(self):
        r = {
            "market": "GOLD",
            "dirs": [1] * 11,
            "dirs_cloturees": [1] * 11,
            "confirme": 0,
        }
        r["dirs_cloturees"][9] = 0
        self.assertEqual(ab.timeframe_attendu(r, {}), "4h")
        # BTC deliberately retains its legacy timeframe selection.
        r["market"] = "BTC"
        self.assertEqual(ab.timeframe_attendu(r, {}), "4h")


if __name__ == "__main__":
    unittest.main()
