"""Régression : « Pas aujourd'hui » coupe réellement les nouvelles alertes jusqu'à réactivation explicite."""
import datetime
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import align_bot as ab


class QuietOptOutTest(unittest.TestCase):
    def test_quiet_callback_silences_user_and_cleans_pending_subscriptions(self):
        state = {
            "auto": {"BTC": ["11", "22"], "GOLD": ["11"], "NASDAQ": ["11"]},
            "coach_pending": ["11", "22"],
            "coach_live": {
                "BTC": {"11": {"dernier_t": 1}, "22": {"dernier_t": 1}},
                "GOLD": {"11": {"dernier_t": 1}},
            },
            "recherche_positions_active": ["11", "22"],
            "BTC": {"trade": {"qui": {
                "11": {"e": 100.0, "sl": 95.0, "tp1": 110.0},
                "22": {"e": 100.0, "sl": 95.0, "tp1": 110.0},
            }}},
            "telegram_outbox": [
                {"chat_id": "11", "params": {"text": "old alert"}},
                {"chat_id": "22", "params": {"text": "other user's alert"}},
            ],
        }
        update = {
            "update_id": 901,
            "callback_query": {
                "id": "quiet-callback",
                "data": "quiet:no",
                "from": {"id": 11, "first_name": "Test"},
                "message": {"chat": {"id": 11, "type": "private"}},
            },
        }

        with patch.object(ab, "telegram", return_value={"ok": True}) as telegram:
            ab.traiter(state, {"11", "22"}, [update])

        self.assertIn("11", {str(x) for x in state["quiet"]})
        self.assertIn("11", {str(x) for x in state["bot_off"]})
        self.assertNotIn("11", [str(x) for x in state["coach_pending"]])
        self.assertTrue(all("11" not in {str(x) for x in users} for users in state["auto"].values()))
        self.assertTrue(all("11" not in {str(x) for x in users} for users in state["coach_live"].values()))
        self.assertNotIn("11", {str(x) for x in state["recherche_positions_active"]})
        self.assertNotIn("11", state["BTC"]["trade"]["qui"])
        self.assertIn("22", state["BTC"]["trade"]["qui"])
        with patch.object(ab, "noter") as notify:
            ab.cloturer_abonnes(state, "BTC", state["BTC"]["trade"], 104.0, "TP1")
        self.assertEqual([call.args[1] for call in notify.call_args_list], ["22"])
        self.assertEqual([x["chat_id"] for x in state["telegram_outbox"]], ["22"])
        self.assertFalse(ab.coach_actif(state, "11", "BTC"))
        self.assertTrue(ab.coach_actif(state, "22", "BTC"))
        telegram.assert_called_once_with("answerCallbackQuery", callback_query_id="quiet-callback", text="Bien noté")

    def test_quiet_user_receives_no_daily_checkin(self):
        now = datetime.datetime(2026, 11, 17, 9, 0, tzinfo=ab.PARIS).timestamp()
        state = {"quiet": ["11"]}
        sent = []

        with patch.object(ab, "_envoi_sur",
                          side_effect=lambda cid, **kw: sent.append(str(cid)) or {"ok": True}):
            ab.question_quotidienne(state, {"11", "22"}, now)

        self.assertEqual(sent, ["22"])

    def test_quiet_user_is_not_notified_by_persistent_live_coach(self):
        state = {"quiet": ["11"], "coach_live": {"BTC": {"11": {"dernier_t": 0}}}}
        r = {"b15": [{"t": 900}, {"t": 1800}]}

        with patch.object(ab, "_envoi_sur") as send, \
             patch.object(ab, "texte_coach_live", return_value="test alert"), \
             patch.object(ab, "markup_analyse", return_value=None):
            ab.notifier_coach_live(state, "BTC", r, {})

        send.assert_not_called()

    def test_quiet_state_alone_blocks_new_market_alerts(self):
        state = {"quiet": ["11"], "auto": {"BTC": ["11"]}}
        self.assertFalse(ab.coach_actif(state, "11", "BTC"))

    def test_explicit_coach_activation_clears_quiet_state(self):
        state = {"quiet": ["11"], "bot_off": ["11"], "auto": {}}

        with patch.object(ab, "DERNIERS", {}), patch.object(ab, "lancer_chrono"):
            ab.inscrire_auto(state, "11", "BTC", notifier=False)

        self.assertNotIn("11", {str(x) for x in state.get("quiet", [])})
        self.assertNotIn("11", {str(x) for x in state.get("bot_off", [])})
        self.assertTrue(ab.coach_actif(state, "11", "BTC"))

    def test_explicit_live_search_activation_clears_quiet_state(self):
        state = {"quiet": ["11"], "bot_off": ["11"], "coach_live": {}, "recherche_positions_active": []}

        ab.activer_coach_live(state, "11", "BTC", True)

        self.assertNotIn("11", {str(x) for x in state.get("quiet", [])})
        self.assertNotIn("11", {str(x) for x in state.get("bot_off", [])})
        self.assertIn("11", state["coach_live"]["BTC"])
        self.assertIn("11", state["recherche_positions_active"])


    def test_daily_trade_no_removes_pending_push_authorization(self):
        state = {
            "auto": {"BTC": ["11", "22"], "GOLD": ["11"]},
            "coach_pending": ["11", "22"],
            "coach_live": {"BTC": {"11": {"dernier_t": 1}, "22": {"dernier_t": 1}}},
            "recherche_positions_active": ["11", "22"],
            "telegram_outbox": [
                {"chat_id": "11", "params": {"text": "queued alert"}},
                {"chat_id": "22", "params": {"text": "other user's alert"}},
            ],
            "BTC": {"trade": {"qui": {
                "11": {"e": 100.0, "sl": 95.0, "tp1": 110.0},
                "22": {"e": 100.0, "sl": 95.0, "tp1": 110.0},
            }}},
        }
        update = {
            "update_id": 902,
            "callback_query": {
                "id": "trade-no-callback",
                "data": "trade:no",
                "from": {"id": 11, "first_name": "Test"},
                "message": {"chat": {"id": 11, "type": "private"}},
            },
        }

        with (
            patch.object(ab, "telegram", return_value={"ok": True}),
            patch.object(ab, "DERNIER_ETAT", state),
            patch.object(ab, "TELEGRAM_PULL_MODE", True),
        ):
            ab.traiter(state, {"11", "22"}, [update])
            # Simule le tour automatique suivant, sans action privée entrante.
            ab.TELEGRAM_PULL_CONTEXT.chat_id = None
            ab.TELEGRAM_PULL_CONTEXT.private = False
            self.assertFalse(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": "11", "text": "🎯 POSITION ALIGN DÉTECTÉE"}
            ))

        self.assertIn("11", {str(x) for x in state["bot_off"]})
        self.assertNotIn("11", {str(x) for x in state["recherche_positions_active"]})
        self.assertTrue(all("11" not in {str(x) for x in users} for users in state["auto"].values()))
        self.assertTrue(all("11" not in {str(x) for x in users} for users in state["coach_live"].values()))
        self.assertNotIn("11", [str(x) for x in state["coach_pending"]])
        self.assertEqual([x["chat_id"] for x in state["telegram_outbox"]], ["22"])
        self.assertNotIn("11", state["BTC"]["trade"]["qui"])
        self.assertIn("22", state["BTC"]["trade"]["qui"])
        self.assertFalse(ab.coach_actif(state, "11", "BTC"))


    def test_optout_removes_only_that_user_from_all_open_market_positions(self):
        position = {"e": 100.0, "sl": 98.0, "tp1": 104.0, "d": 1, "t": 1}
        state = {
            "BTC": {"trade": {"qui": {"11": dict(position), "22": dict(position)}}},
            "GOLD": {"trade": {"qui": {"11": dict(position), "22": dict(position)}}},
            "NASDAQ": {"trade": {"qui": {"22": dict(position)}}},
        }

        ab.retirer_suivi_positions(state, "11")

        self.assertEqual(ab.en_position(state, "11"), [])
        self.assertEqual(set(ab.en_position(state, "22")), {"BTC", "GOLD", "NASDAQ"})
        with patch.object(ab, "noter") as notify:
            for market in ("BTC", "GOLD", "NASDAQ"):
                ab.cloturer_abonnes(state, market, state[market]["trade"], 104.0, "TP1")
        self.assertEqual([call.args[1] for call in notify.call_args_list], ["22", "22", "22"])

    def test_coach_no_revokes_open_position_follow(self):
        position = {"e": 100.0, "sl": 95.0, "tp1": 110.0}
        state = {
            "coach_pending": ["11"],
            "BTC": {"trade": {"qui": {"11": dict(position), "22": dict(position)}}},
            "telegram_outbox": [{"chat_id": "11", "params": {"text": "old position update"}}],
        }
        update = {
            "update_id": 903,
            "callback_query": {
                "id": "coach-no-callback",
                "data": "coach:no",
                "from": {"id": 11, "first_name": "Test"},
                "message": {"chat": {"id": 11, "type": "private"}},
            },
        }

        with patch.object(ab, "telegram", return_value={"ok": True}):
            ab.traiter(state, {"11", "22"}, [update])

        self.assertIn("11", {str(x) for x in state["bot_off"]})
        self.assertNotIn("11", state["BTC"]["trade"]["qui"])
        self.assertIn("22", state["BTC"]["trade"]["qui"])
        self.assertEqual(state["telegram_outbox"], [])



if __name__ == "__main__":
    unittest.main()
