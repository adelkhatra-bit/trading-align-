import unittest
from unittest.mock import patch

import align_bot as ab


class TelegramFollowStatusPineTests(unittest.TestCase):
    def base_market(self):
        snapshots = {}
        for tf, _label in ab.TELEGRAM_TF_VIEWS:
            snapshots[tf] = {"fresh": True, "direction": 0, "price": 100.0}
        for tf, _label in ab.TELEGRAM_TF_VIEWS[:7]:
            snapshots[tf]["direction"] = 1
        return {
            "market": "BTC",
            "require_tv_bridge": True,
            "tv_indicator_mtf": {
                "available": True,
                "activeTimeframe": "M5",
                "snapshots": snapshots,
            },
        }

    def base_plan(self, **overrides):
        plan = {
            "available": True,
            "direction": 1,
            "confirmed": False,
            "triggered": False,
            "price_in_zone": False,
            "strategy": "DAY",
            "entry_timeframe": "M5",
            "price": 100.0,
            "entry": 101.0,
            "sl": 95.0,
            "tp1": 110.0,
            "tp2": 115.0,
            "zone_low": 100.0,
            "zone_high": 102.0,
        }
        plan.update(overrides)
        return plan

    def pine_status(self, plan, now=300):
        r = self.base_market()
        with (
            patch.object(ab, "DERNIERS", {"BTC": r}),
            patch.object(ab, "plan_indicateur", return_value=plan),
            patch.object(ab, "_radar_n_ut", side_effect=lambda _r, d: 7 if d == 1 else 4),
            patch.object(ab, "hb_etat_surveille", side_effect=AssertionError("local MTF must not be used")),
        ):
            return ab._ou_en_est({}, "BTC", now=now)

    def test_unconfirmed_plan_uses_pine_12_timeframe_count_and_hides_trade_levels(self):
        text = self.pine_status(self.base_plan())

        self.assertIn("Pine v25", text)
        self.assertIn("LONG", text)
        self.assertIn("7/12", text)
        self.assertIn("8/12", text)
        self.assertIn("non confirmée", text)
        self.assertIn("UT non alignées ou périmées", text)
        self.assertIn("Aucune entrée autorisée", text)
        self.assertNotIn("Entry 101", text)
        self.assertNotIn("SL 95", text)
        self.assertNotIn("TP1 110", text)
        self.assertNotIn("6/11", text)

    def test_missing_pine_plan_reports_bridge_context_without_local_fallback(self):
        plan = {"available": False, "reason": "snapshot TradingView canonique M15 périmé"}
        text = self.pine_status(plan)

        self.assertIn("Contexte Pine v25", text)
        self.assertIn("7/12 UT haussières", text)
        self.assertIn("4/12 baissières", text)
        self.assertIn("Plan M15 indisponible", text)
        self.assertIn("Aucune entrée", text)
        self.assertNotIn("6/11", text)

    def test_confirmed_plan_shows_chart_levels_but_not_entry_authorization_before_trigger(self):
        plan = self.base_plan(confirmed=True)
        text = self.pine_status(plan)

        self.assertIn("Plan Pine v25 confirmé : LONG", text)
        self.assertIn("Entry 101", text)
        self.assertIn("SL 95", text)
        self.assertIn("TP1 110", text)
        self.assertIn("TP2 115", text)
        self.assertIn("zone d'entrée 100", text)
        self.assertIn("attente du retest", text)
        self.assertIn("Préparation uniquement", text)
        self.assertNotIn("ENTRÉE AUTORISÉE", text)

    def test_trigger_outside_zone_explicitly_says_wait_and_no_market_entry(self):
        plan = self.base_plan(confirmed=True, triggered=True, price=103.0, price_in_zone=False)
        text = self.pine_status(plan)

        self.assertIn("Déclencheur Pine M5 confirmé", text)
        self.assertIn("hors zone", text)
        self.assertIn("Attendre le retour dans la zone", text)
        self.assertIn("aucune entrée au marché", text)

    def test_trigger_inside_zone_waits_for_final_align_safety_message(self):
        plan = self.base_plan(confirmed=True, triggered=True, price=101.0, price_in_zone=True)
        text = self.pine_status(plan)

        self.assertIn("prix TradingView dans la zone", text)
        self.assertIn("Contrôles finaux ALIGN en attente", text)
        self.assertIn("message explicite ENTRÉE AUTORISÉE", text)

    def test_follow_summary_distinguishes_signal_from_user_personal_position(self):
        r = self.base_market()
        state = {
            "BTC": {
                "trade": {
                    "d": 1, "e": 101.0, "sl": 95.0, "tp1": 110.0, "tp2": 115.0,
                    "statut": "entree", "qui": {},
                }
            }
        }
        with (
            patch.object(ab, "MARCHES", ("BTC",)),
            patch.object(ab, "NOMS_MARCHES", {"BTC": "BTC"}),
            patch.object(ab, "DERNIERS", {"BTC": r}),
            patch.object(ab, "_prix_tv_actif", return_value=102.0),
            patch.object(ab, "en_position", return_value=[]),
            patch.object(ab, "marches_choisis", return_value={"BTC"}),
            patch.object(ab, "bot_on", return_value=True),
        ):
            text = ab.texte_suivi(state, "123", now=300)

        self.assertIn("signal confirmé", text)
        self.assertIn("exécution manuelle à effectuer", text)
        self.assertIn("entrée 101", text)
        self.assertIn("prix TradingView 102", text)
        self.assertNotIn("attente de confirmation Pine v25", text)
        self.assertNotIn("j'attends une entrée confirmée", text)

    def test_personal_follow_is_not_reported_as_waiting_for_a_signal(self):
        r = self.base_market()
        state = {
            "BTC": {
                "trade": {
                    "d": 1, "e": 100.0, "sl": 95.0, "tp1": 110.0, "tp2": 115.0,
                    "statut": "entree",
                    "qui": {"123": {"d": 1, "e": 101.0, "sl": 95.0, "tp1": 110.0, "fini": False}},
                }
            }
        }
        with (
            patch.object(ab, "MARCHES", ("BTC",)),
            patch.object(ab, "NOMS_MARCHES", {"BTC": "BTC"}),
            patch.object(ab, "DERNIERS", {"BTC": r}),
            patch.object(ab, "_prix_tv_actif", return_value=102.0),
            patch.object(ab, "en_position", return_value=["BTC"]),
            patch.object(ab, "marches_choisis", return_value={"BTC"}),
            patch.object(ab, "bot_on", return_value=True),
        ):
            text = ab.texte_suivi(state, "123", now=300)

        self.assertIn("ta position personnelle est suivie jusqu'à clôture", text)
        self.assertIn("entrée personnelle 101", text)
        self.assertIn("prix TradingView 102", text)
        self.assertNotIn("attente de confirmation Pine v25", text)

    def test_closed_personal_position_is_not_shown_as_waiting_or_open(self):
        state = {
            "BTC": {
                "trade": {
                    "d": 1, "e": 100.0, "sl": 95.0, "tp1": 110.0, "tp2": 115.0,
                    "statut": "tp2",
                    "qui": {"123": {"d": 1, "e": 101.0, "sl": 95.0, "tp1": 110.0, "fini": True}},
                }
            }
        }
        with (
            patch.object(ab, "MARCHES", ("BTC",)),
            patch.object(ab, "NOMS_MARCHES", {"BTC": "BTC"}),
            patch.object(ab, "en_position", return_value=[]),
            patch.object(ab, "marches_choisis", return_value={"BTC"}),
            patch.object(ab, "bot_on", return_value=True),
        ):
            text = ab.texte_suivi(state, "123", now=300)

        self.assertIn("ta position personnelle est clôturée", text)
        self.assertNotIn("j'attends une entrée confirmée", text)
        self.assertNotIn("signal confirmé", text)


if __name__ == "__main__":
    unittest.main()
