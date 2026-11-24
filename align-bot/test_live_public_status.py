import unittest
from unittest.mock import patch

import align_bot as ab


class LivePublicStatusTests(unittest.TestCase):
    def _pine(self, direction=1, stale=None, strategy="DAY"):
        snapshots = {}
        for tf, _ in ab.TELEGRAM_TF_VIEWS:
            snapshots[tf] = {
                "fresh": tf != stale,
                "direction": direction,
                "rsi": 55.0,
                "price": 100.0,
                "bar_time": 1_795_542_000_000,
                "robotV12": {"strategy": strategy} if tf == "M15" else {},
            }
        return {
            "available": stale is None,
            "activeTimeframe": "M15",
            "snapshots": snapshots,
        }

    def test_required_bridge_unavailable_never_publishes_local_bias_or_profile(self):
        r = {
            "require_tv_bridge": True,
            "tv_indicator_mtf": {"available": False, "snapshots": {}},
            # These legacy/local values must be ignored while Pine is mandatory.
            "dirPlan": 1, "strat": "SWING", "bull": 10, "bear": 1,
            "dirs": [1] * 11,
        }
        with patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)):
            payload = ab.construire_live({}, {"BTC": r}, now=1_795_542_100)
        market = payload["marches"][0]
        self.assertEqual(market["etat"], "perime")
        self.assertEqual(market["biais"], "indecis")
        self.assertEqual(market["ut"], 0)
        self.assertEqual(market["profil"], "aucun")

    def test_required_bridge_uses_only_twelve_fresh_pine_snapshots(self):
        bridge = self._pine(direction=1, strategy="DAY")
        # Eight bullish Pine snapshots meet the configured threshold.
        for tf, _ in ab.TELEGRAM_TF_VIEWS[8:]:
            bridge["snapshots"][tf]["direction"] = -1
        r = {
            "require_tv_bridge": True,
            "tv_indicator_mtf": bridge,
            "dirPlan": -1, "strat": "SWING", "bull": 0, "bear": 11,
            "dirs": [-1] * 11,
        }
        plan = {"available": True, "direction": 1, "strategy": "DAY"}
        with patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)), \
             patch.object(ab, "plan_indicateur", return_value=plan):
            payload = ab.construire_live({}, {"BTC": r}, now=1_795_542_100)
        market = payload["marches"][0]
        self.assertEqual(market["etat"], "preparation")
        self.assertEqual(market["biais"], "haussier")
        self.assertEqual(market["ut"], 8)
        self.assertEqual(market["seuil"], ab.MIN_ALIGN)
        self.assertEqual(market["profil"], "INTRADAY")

    def test_one_stale_required_timeframe_fails_closed_even_if_local_data_is_aligned(self):
        bridge = self._pine(direction=-1, stale="M3", strategy="SWING")
        r = {
            "require_tv_bridge": True,
            "tv_indicator_mtf": bridge,
            "dirPlan": -1, "strat": "SWING", "bull": 0, "bear": 11,
            "dirs": [-1] * 11,
        }
        with patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)):
            payload = ab.construire_live({}, {"GOLD": r}, now=1_795_542_100)
        market = payload["marches"][0]
        self.assertEqual(market["etat"], "perime")
        self.assertEqual(market["biais"], "indecis")
        self.assertEqual(market["ut"], 0)
        self.assertEqual(market["profil"], "aucun")

    def test_closed_market_remains_closed_without_fabricating_a_pine_bias(self):
        r = {
            "require_tv_bridge": True,
            "tv_indicator_mtf": {"available": False, "snapshots": {}},
            "dirPlan": 1, "strat": "SWING", "bull": 10, "bear": 0,
        }
        with patch.object(ab, "etat_marche_hb", return_value=("ferme", "session fermée")):
            payload = ab.construire_live({}, {"GOLD": r}, now=1_795_542_100)
        market = payload["marches"][0]
        self.assertEqual(market["etat"], "ferme")
        self.assertEqual(market["biais"], "indecis")
        self.assertEqual(market["ut"], 0)

    def test_non_bridge_mode_keeps_legacy_public_summary(self):
        r = {"dirPlan": 1, "strat": "SWING", "bull": 9, "bear": 2}
        summary = {"sens": -1, "n": 7, "strat": "DAY"}
        with patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)), \
             patch.object(ab, "hb_etat_surveille", return_value=summary):
            payload = ab.construire_live({}, {"BTC": r}, now=1_795_542_100)
        market = payload["marches"][0]
        self.assertEqual(market["etat"], "preparation")
        self.assertEqual(market["biais"], "baissier")
        self.assertEqual(market["ut"], 7)
        self.assertEqual(market["profil"], "INTRADAY")


if __name__ == "__main__":
    unittest.main()
