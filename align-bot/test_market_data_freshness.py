"""Freshness guards for Yahoo delayed futures and cached Nasdaq quotes."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def snapshot(now, source, age5=120, age15=300, age1h=300, age4h=300):
    return {
        "t": now,
        "m1": [{"t": now, "c": 100.0}],
        "b5": [{"t": now - 300 - age5, "volume_source": source}],
        "b15": [{"t": now - 900 - age15, "volume_source": source}],
        "b1h": [{"t": now - 3600 - age1h, "volume_source": source}],
        "b4h": [{"t": now - 14400 - age4h, "volume_source": source}],
    }


class MarketDataFreshness(unittest.TestCase):
    def test_nasdaq_yahoo_m5_delayed_ten_minutes_blocks_new_positions(self):
        now = 100000.0
        r = snapshot(now, "CME NQ=F Yahoo proxy", age5=600)
        self.assertFalse(ab.donnees_mtf_fraiches("NASDAQ", r, now_ts=now))

    def test_nasdaq_fresh_closed_mtf_bars_are_accepted(self):
        now = 100000.0
        r = snapshot(now, "CME NQ=F Yahoo proxy", age5=240, age15=600, age1h=600, age4h=600)
        self.assertTrue(ab.donnees_mtf_fraiches("NASDAQ", r, now_ts=now))

    def test_gold_comex_fallback_is_blocked_when_m5_is_delayed(self):
        now = 100000.0
        r = snapshot(now, "COMEX GC=F Yahoo proxy", age5=600)
        self.assertFalse(ab.donnees_mtf_fraiches("GOLD", r, now_ts=now))

    def test_gold_kraken_paxg_feed_is_checked_by_candle_age(self):
        now = 100000.0
        fresh = snapshot(now, "Kraken PAXGUSD", age5=240)
        stale = snapshot(now, "Kraken PAXGUSD", age5=600)
        self.assertTrue(ab.donnees_mtf_fraiches("GOLD", fresh, now_ts=now))
        self.assertFalse(ab.donnees_mtf_fraiches("GOLD", stale, now_ts=now))

    def test_btc_legacy_data_policy_is_unchanged(self):
        self.assertTrue(ab.donnees_mtf_fraiches("BTC", {}, now_ts=100000.0))

    def test_sniper_refuses_stale_nasdaq_candles(self):
        now = 100000.0
        r = snapshot(now, "CME NQ=F Yahoo proxy", age5=600)
        r.update({"market": "NASDAQ", "dirPlan": 1})
        self.assertEqual(ab._sniper(r), (None, "DONNEES_MTF_PERIMEES"))

    def test_agent_ne_cree_aucune_position_sur_bougies_yahoo_retardees(self):
        now = 100000.0
        r = snapshot(now, "CME NQ=F Yahoo proxy", age5=600)
        r.update({
            "r5": [50.0, 50.0], "posD": 0.5, "posW": 0.5,
            "confirme": 1, "dirs": [1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1],
            "fermeture": False,
        })
        with (
            mock.patch.object(ab, "manipulation"),
            mock.patch.object(ab, "meche_suspecte"),
            mock.patch.object(ab, "niveaux_cles"),
            mock.patch.object(ab, "resistance_fvg"),
            mock.patch.object(ab, "suivre_apres_sl"),
            mock.patch.object(ab, "reprise_entree", return_value=None),
            mock.patch.object(ab, "entree_retest", return_value=None),
            mock.patch.object(ab, "radar_climax", return_value=None),
            mock.patch.object(ab, "retournement_marche", return_value=None),
            mock.patch.object(ab, "plan_cassure") as cassure,
            mock.patch.object(ab, "point_entree") as fvg,
        ):
            out = ab.agent("NASDAQ", r, {}, "")
        cassure.assert_not_called()
        fvg.assert_not_called()
        self.assertTrue(any("trop anciennes ou retardées" in x for x in out))

    def test_nasdaq_does_not_reuse_a_quote_cached_for_over_thirty_seconds(self):
        now = 100000.0
        with (
            mock.patch.dict(ab._CACHE, {"nq_live": (now - 60, 20123.0)}),
            mock.patch.object(ab, "http_json", side_effect=RuntimeError("scanner down")),
            mock.patch.object(ab.time, "time", return_value=now),
        ):
            self.assertIsNone(ab.nasdaq_direct())


if __name__ == "__main__":
    unittest.main()
