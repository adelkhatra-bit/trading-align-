import unittest
from unittest.mock import patch

import align_bot as ab


class CoachPineSourceTests(unittest.TestCase):
    def base_market(self, market="BTC"):
        return {
            "market": market,
            "require_tv_bridge": True,
            "m1": [{"c": 999.0}],
            "dirs": [0] * 11,
            "dirs_cloturees": [1] * 11,
            "rsis": [60] * 11,
            "posD": 0.5,
            "posW": 0.5,
            "atr": 2.0,
            "b5": [{"h": 102.0, "l": 98.0, "c": 100.0}] * 12,
            "tv_indicator_mtf": {
                "available": True,
                "activeTimeframe": "M15",
                "snapshots": {
                    "M1": {"fresh": True, "direction": "BEARISH", "rsi": 48.0},
                    "M5": {"fresh": True, "direction": "BULLISH", "rsi": 62.0},
                    "M15": {"fresh": True, "price": 101.0, "direction": "BULLISH", "rsi": 61.0},
                    "H1": {"fresh": True, "direction": "BULLISH", "rsi": 64.0},
                    "H4": {"fresh": True, "direction": "BEARISH", "rsi": 38.0},
                    "D1": {"fresh": True, "direction": "NEUTRAL", "rsi": 51.0},
                },
            },
        }

    def run_data(self, market, r, cle, plan):
        self.next_review_tf = None

        def next_close(_r, tf, _now):
            self.next_review_tf = tf
            return 1_795_536_600

        with (
            patch.object(ab, "verdict", return_value=("ATTENTE", "test local")),
            patch.object(ab, "profil_strategie", return_value={"mode": "LOCAL"}),
            patch.object(ab, "plan_indicateur", return_value=plan),
            patch.object(ab, "niveau_cassure", return_value=None),
            patch.object(ab, "resume_volume", return_value={}),
            patch.object(ab, "timeframe_attendu", return_value="5m"),
            patch.object(ab, "prochaine_cloture_bougie", side_effect=next_close),
            patch.object(ab, "lecons_pour", return_value=[]),
        ):
            return ab.donnees_ia(market, r, cle)

    def test_bridge_required_never_falls_back_to_local_order_when_pine_plan_missing(self):
        r = self.base_market()
        cle = {"ordre": {"e": 999.0, "za": 998.0, "zb": 1000.0}}
        data = self.run_data("BTC", r, cle, {"available": False, "reason": "plan Pine incomplet"})

        self.assertEqual(data["prix"], 101.0)
        self.assertEqual(data["sens 1m/5m/15m/1h/4h/Daily"], [-1, 1, 1, 1, -1, 0])
        self.assertEqual(data["RSI 5m/15m/1h/4h"], [62, 61, 64, 38])
        self.assertEqual(data["lecture_multi_unites"], {"M5": 1, "M15": 1, "H1": 1, "H4": -1})
        self.assertIsNone(data["zone d'entrée"])
        self.assertEqual(data["profil_strategie"]["mode"], "ATTENTE")
        self.assertIn("plan Pine v25 indisponible", data["verdict du bot"])
        self.assertIs(data["distance_plan_entree"]["disponible"], False)
        self.assertNotIn("entree_visee", data["distance_plan_entree"])
        self.assertIs(data["estimation_approche_entree"]["disponible"], False)

    def test_bridge_required_uses_pine_price_entry_and_zone_not_local_values(self):
        r = self.base_market()
        cle = {"ordre": {"e": 999.0, "za": 998.0, "zb": 1000.0}}
        plan = {
            "available": True, "price": 101.0, "entry": 105.0, "sl": 95.0,
            "tp1": 115.0, "tp2": 120.0, "zone_low": 104.0, "zone_high": 106.0,
            "strategy": "DAY", "direction": 1, "triggered": False,
        }
        data = self.run_data("BTC", r, cle, plan)

        self.assertEqual(data["prix"], 101.0)
        self.assertEqual(data["zone d'entrée"], [104.0, 106.0])
        self.assertEqual(data["profil_strategie"]["mode"], "DAY")
        self.assertIn("Plan Pine v25 LONG", data["verdict du bot"])
        self.assertEqual(data["distance_plan_entree"]["prix_actuel"], 101.0)
        self.assertEqual(data["distance_plan_entree"]["entree_visee"], 105.0)
        self.assertEqual(data["distance_plan_entree"]["origine"], "TradingView ROBOT V12 frais")
        self.assertEqual(self.next_review_tf, "5m")
        self.assertEqual(data["estimation_approche_entree"]["source_mouvement"],
                         "bougies 5m locales du bot (proxy, distinct du snapshot TradingView)")

    def test_confirmed_pine_trigger_outside_zone_is_never_presented_as_entry_ready(self):
        r = self.base_market()
        plan = {
            "available": True, "price": 107.0, "entry": 105.0, "sl": 95.0,
            "tp1": 115.0, "tp2": None, "zone_low": 104.0, "zone_high": 106.0,
            "strategy": "DAY", "direction": 1, "triggered": True, "price_in_zone": False,
        }
        data = self.run_data("BTC", r, {}, plan)

        self.assertIn("déclencheur confirmé mais prix hors zone", data["verdict du bot"])
        self.assertIn("attendre le retour", data["verdict du bot"])

    def test_gold_does_not_publish_eta_from_non_tradingview_proxy_candles(self):
        r = self.base_market("GOLD")
        plan = {
            "available": True, "price": 101.0, "entry": 105.0, "sl": 95.0,
            "tp1": 115.0, "tp2": None, "zone_low": 104.0, "zone_high": 106.0,
            "strategy": "DAY", "direction": 1, "triggered": False,
        }
        data = self.run_data("GOLD", r, {}, plan)

        self.assertIs(data["estimation_approche_entree"]["disponible"], False)
        self.assertNotIn("minutes_indicatives", data["estimation_approche_entree"])
        self.assertIn("spot TradingView", data["estimation_approche_entree"]["raison"])


    def test_live_countdown_uses_pine_plan_and_refuses_local_order_when_plan_missing(self):
        r = self.base_market()
        r["require_tv_bridge"] = True
        cle = {"ordre": {"e": 999.0, "za": 998.0, "zb": 1000.0}}
        with patch.object(ab, "plan_indicateur", return_value={"available": False, "reason": "plan Pine absent"}), \
             patch.object(ab.time, "time", return_value=1000.0), \
             patch.object(ab, "prochaine_cloture_bougie", return_value=1300.0):
            text = ab.chrono_txt("BTC", r, cle, 900.0)

        self.assertIn("aucun plan Pine v25 frais", text)
        self.assertIn("Aucun niveau", text)
        self.assertNotIn("998", text)
        self.assertNotIn("999", text)
        self.assertIn("PROCHAINE RÉÉVALUATION", text)

    def test_live_countdown_uses_pine_entry_timeframe_and_zone_guard(self):
        r = self.base_market()
        r["require_tv_bridge"] = True
        plan = {
            "available": True, "price": 107.0, "entry": 105.0, "sl": 95.0,
            "tp1": 115.0, "tp2": 120.0, "zone_low": 104.0, "zone_high": 106.0,
            "strategy": "DAY", "direction": 1, "entry_timeframe": "M5",
            "triggered": True, "price_in_zone": False,
        }
        seen = []
        def next_close(_r, tf, _now):
            seen.append(tf)
            return 1300.0
        with patch.object(ab, "plan_indicateur", return_value=plan), \
             patch.object(ab.time, "time", return_value=1000.0), \
             patch.object(ab, "prochaine_cloture_bougie", side_effect=next_close):
            text = ab.chrono_txt("BTC", r, {}, 900.0)

        self.assertIn("prix hors zone", text)
        self.assertIn("104", text)
        self.assertIn("106", text)
        self.assertIn("Entry", text)
        self.assertEqual(seen, ["5m"])

    def test_auto_coach_activation_never_displays_local_levels_in_bridge_mode(self):
        r = self.base_market()
        r["require_tv_bridge"] = True
        state = {"BTC": {"ordre": {"e": 999.0, "za": 998.0, "zb": 1000.0, "sl": 900.0, "tp1": 1100.0, "tp2": 1200.0}}}
        with patch.dict(ab.DERNIERS, {"BTC": r}, clear=True), \
             patch.object(ab, "plan_indicateur", return_value={"available": False, "reason": "plan Pine absent"}), \
             patch.object(ab, "_envoi_sur") as send, \
             patch.object(ab, "armer_clotures_multi"), \
             patch.object(ab, "lancer_chrono"):
            ab.inscrire_auto(state, "chat-test", "BTC")

        message = send.call_args.kwargs["text"]
        self.assertIn("aucun sens Pine v25 frais", message)
        self.assertIn("Aucune zone", message)
        self.assertNotIn("999", message)
        self.assertNotIn("998", message)
        self.assertIn("douze unités", message)

    def test_auto_coach_activation_displays_only_pine_entry_levels(self):
        r = self.base_market()
        r["require_tv_bridge"] = True
        state = {"BTC": {"ordre": {"e": 999.0, "za": 998.0, "zb": 1000.0, "sl": 900.0, "tp1": 1100.0, "tp2": 1200.0}}}
        plan = {
            "available": True, "price": 101.0, "entry": 105.0, "sl": 95.0,
            "tp1": 115.0, "tp2": 120.0, "zone_low": 104.0, "zone_high": 106.0,
            "strategy": "DAY", "direction": 1, "triggered": False, "price_in_zone": False,
        }
        with patch.dict(ab.DERNIERS, {"BTC": r}, clear=True), \
             patch.object(ab, "plan_indicateur", return_value=plan), \
             patch.object(ab, "_envoi_sur") as send, \
             patch.object(ab, "armer_clotures_multi"), \
             patch.object(ab, "lancer_chrono"):
            ab.inscrire_auto(state, "chat-test", "BTC")

        message = send.call_args.kwargs["text"]
        self.assertIn("Direction Pine v25 :", message)
        self.assertIn("LONG", message)
        self.assertIn("Prix TradingView", message)
        self.assertIn("Entry", message)
        self.assertNotIn("999", message)
        self.assertNotIn("900", message)


if __name__ == "__main__":
    unittest.main()
