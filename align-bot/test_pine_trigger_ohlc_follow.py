import unittest
from unittest.mock import patch

import align_bot as ab


class PineTriggerOhlcFollowTests(unittest.TestCase):
    def tv(self, **overrides):
        data = {
            "price": 108.0,
            "timeframe": "M15",
            "ageMs": 1000,
            "entryTimeframe": "M5",
            "barOhlcAvailable": True,
            "activeEntryBarTime": 600_000,
            "activeEntryBarOpen": 105.0,
            "activeEntryBarHigh": 111.0,
            "activeEntryBarLow": 99.0,
            "activeEntryBarClose": 108.0,
            "entryBarTime": 300_000,
            "entryBarHigh": 105.0,
            "entryBarLow": 99.0,
        }
        data.update(overrides)
        return data

    def plan(self, **overrides):
        data = {
            "available": True,
            "confirmed": True,
            "triggered": False,
            "direction": 1,
            "strategy": "DAY",
            "entry_timeframe": "M5",
            "entry": 100.0,
            "sl": 95.0,
            "tp1": 110.0,
            "tp2": 120.0,
            "price": 101.0,
            "price_in_zone": True,
            "zone_low": 99.0,
            "zone_high": 101.0,
            "decision": 100.0,
            "entry_bar_time": 300_000,
            "entry_bar_close": 100.5,
            "active_entry_bar_time": 600_000,
            "active_entry_bar_high": 102.0,
            "active_entry_bar_low": 99.5,
            "active_bar_safe": True,
        }
        data.update(overrides)
        return data

    def test_same_trigger_candle_ignores_wicks_that_existed_before_entry(self):
        trade = {
            "tvEntryBarTime": 600_000,
            "tvEntryBarHigh": 110.0,
            "tvEntryBarLow": 100.0,
            "tvEntryTimeframe": "M5",
        }
        tv = self.tv(
            price=108.0,
            activeEntryBarHigh=110.0,
            activeEntryBarLow=100.0,
            entryBarHigh=130.0,
            entryBarLow=80.0,
        )
        self.assertEqual(ab.extremes_tradingview_depuis_entree(tv, trade), (108.0, 108.0))

    def test_same_trigger_candle_counts_only_new_extremes_after_entry(self):
        trade = {
            "tvEntryBarTime": 600_000,
            "tvEntryBarHigh": 105.0,
            "tvEntryBarLow": 100.0,
            "tvEntryTimeframe": "M5",
        }
        tv = self.tv(
            price=108.0,
            activeEntryBarHigh=112.0,
            activeEntryBarLow=98.0,
        )
        self.assertEqual(ab.extremes_tradingview_depuis_entree(tv, trade), (112.0, 98.0))

    def test_next_trigger_candle_includes_closed_entry_candle_and_current_candle(self):
        trade = {
            "tvEntryBarTime": 600_000,
            "tvEntryBarHigh": 105.0,
            "tvEntryBarLow": 100.0,
            "tvEntryTimeframe": "M5",
        }
        tv = self.tv(
            price=112.0,
            activeEntryBarTime=900_000,
            activeEntryBarHigh=115.0,
            activeEntryBarLow=101.0,
            entryBarTime=600_000,
            entryBarHigh=111.0,
            entryBarLow=97.0,
        )
        self.assertEqual(ab.extremes_tradingview_depuis_entree(tv, trade), (115.0, 97.0))

    def test_timeframe_change_or_missing_candle_gap_suspends_extreme_tracking(self):
        trade = {
            "tvEntryBarTime": 600_000,
            "tvEntryBarHigh": 105.0,
            "tvEntryBarLow": 100.0,
            "tvEntryTimeframe": "M5",
        }
        changed = self.tv(entryTimeframe="H1")
        gap = self.tv(activeEntryBarTime=1_800_000, entryBarTime=600_000)
        self.assertIsNone(ab.extremes_tradingview_depuis_entree(changed, trade))
        self.assertIsNone(ab.extremes_tradingview_depuis_entree(gap, trade))

    def test_active_price_helper_uses_canonical_m15_robot_ohlc(self):
        r = {
            "tv_indicator_mtf": {
                "available": True,
                "activeTimeframe": "M15",
                "activeTimeframeAgeMs": 1000,
                "snapshots": {
                    "M15": {
                        "fresh": True,
                        "price": 108.0,
                        "robotFresh": True,
                        "robotAgeMs": 1000,
                        "robotV12": {
                            "entryTimeframe": "M5",
                            "activeEntryBarOhlcAvailable": True,
                            "activeEntryBarTime": 600_000,
                            "activeEntryBarOpen": 105.0,
                            "activeEntryBarHigh": 111.0,
                            "activeEntryBarLow": 99.0,
                            "activeEntryBarClose": 108.0,
                            "entryBarTime": 300_000,
                            "entryBarHigh": 105.0,
                            "entryBarLow": 99.0,
                        },
                    }
                },
            }
        }
        tv = ab.prix_tradingview_actif(r)
        self.assertEqual(tv["price"], 108.0)
        self.assertTrue(tv["barOhlcAvailable"])
        self.assertEqual(tv["entryTimeframe"], "M5")
        self.assertEqual(tv["activeEntryBarHigh"], 111.0)

    def test_agent_waits_for_pine_trigger_without_requiring_local_m1(self):
        r = {
            "market": "BTC",
            "require_tv_bridge": True,
            "m1": [],
            "r5": [],
            "t": 1_700_000_000,
            "atr": 1.0,
            "annonce": False,
            "fermeture": False,
            "posD": 0.5,
            "posW": 0.5,
            "tv_indicator_mtf": {"available": True},
        }
        with (
            patch.object(ab, "mode_sans_signal", return_value=False),
            patch.object(ab, "prix_tradingview_actif", return_value=self.tv()),
            patch.object(ab, "plan_indicateur", return_value=self.plan(triggered=False)),
            patch.object(ab, "pause_entree_marche", return_value=None),
            patch.object(ab, "bouton_auto", return_value=None),
        ):
            out = ab.agent("BTC", r, {}, "")
        self.assertTrue(out)
        self.assertIn("PLAN PINE M15", out[0][0])
        self.assertIn("Aucune entrée n'est autorisée par une simple mèche", out[0][0])

    def test_agent_creates_trade_from_pine_levels_without_local_m1(self):
        r = {
            "market": "BTC",
            "require_tv_bridge": True,
            "m1": [],
            "r5": [],
            "t": 1_700_000_000,
            "atr": 1.0,
            "annonce": False,
            "fermeture": False,
            "posD": 0.5,
            "posW": 0.5,
            "tv_indicator_mtf": {"available": True},
        }
        cle = {}
        with (
            patch.object(ab, "mode_sans_signal", return_value=False),
            patch.object(ab, "prix_tradingview_actif", return_value=self.tv()),
            patch.object(ab, "plan_indicateur", return_value=self.plan(triggered=True)),
            patch.object(ab, "pause_entree_marche", return_value=None),
            patch.object(ab, "profil_trade", return_value="DAY"),
            patch.object(ab, "strategie_trade", return_value={"strat": "LOCAL"}),
            patch.object(ab, "retournement_confirme", return_value=False),
            patch.object(ab, "memoire_refuse", return_value=(False, 0, 0)),
            patch.object(ab, "validite_cloture", return_value="M5"),
            patch.object(ab, "carte_coach", return_value="CARD"),
            patch.object(ab, "boutons", return_value="BUTTONS"),
        ):
            out = ab.agent("BTC", r, cle, "")
        self.assertEqual(out, [("CARD", "BUTTONS")])
        self.assertEqual(cle["trade"]["e"], 100.0)
        self.assertEqual(cle["trade"]["sl"], 95.0)
        self.assertEqual(cle["trade"]["tp1"], 110.0)
        self.assertEqual(cle["trade"]["tvEntryBarTime"], 600_000)
        self.assertEqual(cle["trade"]["tvEntryBarHigh"], 102.0)
        self.assertEqual(cle["trade"]["tvEntryTimeframe"], "M5")

    def test_agent_uses_trigger_wicks_to_move_trade_to_tp1(self):
        r = {
            "market": "BTC",
            "require_tv_bridge": True,
            "m1": [],
            "r5": [],
            "t": 1_700_000_000,
            "annonce": False,
            "fermeture": False,
            "tv_indicator_mtf": {"available": True},
        }
        trade = {
            "e": 100.0, "sl": 95.0, "tp1": 110.0, "tp2": 120.0,
            "d": 1, "statut": "entree", "cree": 1_700_000_000,
            "tvEntryBarTime": 600_000, "tvEntryBarHigh": 105.0,
            "tvEntryBarLow": 100.0, "tvEntryTimeframe": "M5",
            "qui": {},
        }
        cle = {"trade": trade}
        tv = self.tv(price=108.0, activeEntryBarHigh=112.0, activeEntryBarLow=99.0)
        with (
            patch.object(ab, "mode_sans_signal", return_value=False),
            patch.object(ab, "prix_tradingview_actif", return_value=tv),
            patch.object(ab, "carte_suivi", return_value="SUIVI"),
        ):
            ab.agent("BTC", r, cle, "")
        self.assertEqual(trade["statut"], "tp1")
        self.assertEqual(trade["sl"], 100.0)

    def test_agent_assumes_stop_first_when_stop_and_target_are_touched_in_same_candle(self):
        r = {
            "market": "BTC",
            "require_tv_bridge": True,
            "m1": [],
            "r5": [],
            "t": 1_700_000_000,
            "annonce": False,
            "fermeture": False,
            "tv_indicator_mtf": {"available": True},
        }
        trade = {
            "e": 100.0, "sl": 95.0, "tp1": 110.0, "tp2": 120.0,
            "d": 1, "statut": "entree", "cree": 1_700_000_000,
            "tvEntryBarTime": 600_000, "tvEntryBarHigh": 105.0,
            "tvEntryBarLow": 100.0, "tvEntryTimeframe": "M5",
            "qui": {},
        }
        cle = {"trade": trade}
        tv = self.tv(price=100.0, activeEntryBarHigh=112.0, activeEntryBarLow=94.0)
        with (
            patch.object(ab, "mode_sans_signal", return_value=False),
            patch.object(ab, "prix_tradingview_actif", return_value=tv),
            patch.object(ab, "carte_suivi", return_value="SUIVI"),
        ):
            ab.agent("BTC", r, cle, "")
        self.assertNotIn("trade", cle)
        self.assertEqual(cle["fin"][1], 95.0)

    def test_live_pnl_uses_tradingview_price_without_local_m1(self):
        class Robot:
            def profit_ouvert(self, _etat, _market):
                return 10.0

        etat = {}
        cle = {"trade": {"e": 100.0, "tp1": 110.0, "d": 1}}
        r = {"require_tv_bridge": True, "m1": []}
        ab._LIVE_DERNIER["pnlBTC"] = 0
        with (
            patch.object(ab, "prix_tradingview_actif", return_value=self.tv(price=105.0)),
            patch.object(ab, "auto_trade", Robot()),
            patch.object(ab, "topstep_trade", Robot()),
            patch.object(ab, "live_publier"),
        ):
            result = ab.live_pnl(etat, "BTC", cle, r, now=10_000)
        self.assertEqual(result, 20.0)


if __name__ == "__main__":
    unittest.main()
