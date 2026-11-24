import json
import unittest
from unittest.mock import patch

import align_bot as ab


class TelegramCoachMenuTests(unittest.TestCase):
    def test_live_menu_separates_commentator_next_position_and_twelve_timeframes(self):
        etat = {"live_on": True, "proprio": ["101"], "auto": {"BTC": ["101"]}}
        keyboard = json.loads(ab.clavier_live(etat, "101"))
        buttons = [button for row in keyboard["inline_keyboard"] for button in row]
        callbacks = {button.get("callback_data"): button["text"] for button in buttons}

        self.assertIn("coachlive:BTC", callbacks)
        self.assertIn("auto:BTC", callbacks)
        self.assertIn("timeframes:BTC", callbacks)
        self.assertIn("autostop:BTC", callbacks)
        self.assertIn("animlive:toggle", callbacks)
        self.assertIn("Animations ON", callbacks["animlive:toggle"])
        self.assertIn("Commentaire BTC", callbacks["coachlive:BTC"])
        self.assertIn("Coach position BTC", callbacks["auto:BTC"])
        self.assertIn("12 UT BTC", callbacks["timeframes:BTC"])
        self.assertIn("Arrêter coach BTC", callbacks["autostop:BTC"])
        self.assertNotEqual(callbacks["coachlive:BTC"], callbacks["auto:BTC"])

    def test_english_live_menu_keeps_labels_in_english(self):
        etat = {"live_on": True, "proprio": ["101"], "auto": {"BTC": ["101"]}}
        keyboard = json.loads(ab.clavier_live(etat, "101", anglais=True))
        buttons = [button for row in keyboard["inline_keyboard"] for button in row]
        labels = [button["text"] for button in buttons]

        self.assertTrue(any("Commentary BTC" in label for label in labels))
        self.assertTrue(any("Next position BTC" in label for label in labels))
        self.assertTrue(any("12 timeframes BTC" in label for label in labels))
        self.assertTrue(any("Stop coach BTC" in label for label in labels))
        self.assertTrue(any("Animations ON" in label for label in labels))
        self.assertNotIn("Commentaire BTC", labels)
        self.assertNotIn("Coach position BTC", labels)

    def test_animation_remote_callback_is_owner_only_and_publishes_state(self):
        etat = {"proprio": ["101"], "live_animations": True}
        cb = {"id": "animlive-test"}
        published = []
        with patch.object(ab, "live_publier", side_effect=lambda msg: published.append(msg) or True), \
             patch.object(ab, "_envoi_sur") as send, \
             patch.object(ab, "telegram", return_value={"ok": True}):
            ab.live_callback(etat, set(), cb, "animlive", "toggle", "101")
        self.assertFalse(etat["live_animations"])
        self.assertEqual(published, ["CMD:animations:off:ALIGN"])
        self.assertIn("coupées", send.call_args.kwargs["text"])

        # A non-owner cannot publish a remote visual command.
        with patch.object(ab, "live_publier") as publish, patch.object(ab, "telegram", return_value={"ok": True}):
            ab.live_callback(etat, set(), {"id": "animlive-denied"}, "animlive", "toggle", "202")
        publish.assert_not_called()
        self.assertFalse(etat["live_animations"])

        # A failed ntfy publish must not claim that the remote screen changed.
        etat_echec = {"proprio": ["101"], "live_animations": True}
        with patch.object(ab, "live_publier", return_value=False), \
             patch.object(ab, "_envoi_sur") as send_fail, \
             patch.object(ab, "telegram", return_value={"ok": True}):
            ab.live_callback(etat_echec, set(), {"id": "animlive-fail"}, "animlive", "toggle", "101")
        self.assertTrue(etat_echec["live_animations"])
        self.assertIn("état précédent", send_fail.call_args.kwargs["text"])

    def test_next_position_button_dispatches_to_real_auto_coach_activation(self):
        etat = {}
        update = {
            "update_id": 99101,
            "callback_query": {
                "id": "auto-btc-test",
                "data": "auto:BTC",
                "message": {"chat": {"id": 101, "type": "private"}},
                "from": {"id": 101},
            },
        }
        with patch.object(ab, "autorise", return_value=True), \
             patch.object(ab, "selectionner_marches_suivi") as select_markets, \
             patch.object(ab, "inscrire_auto") as activate_coach, \
             patch.object(ab, "_envoi_sur"), \
             patch.object(ab, "telegram", return_value={"ok": True}), \
             patch.object(ab, "menu_plateforme"):
            ab.traiter(etat, set(), [update])

        select_markets.assert_called_once_with(etat, "101", ["BTC"])
        activate_coach.assert_called_once_with(etat, "101", "BTC", notifier=False)


    def test_search_positions_activates_auto_coach_not_commentator(self):
        etat = {"recherche_positions_active": []}
        with patch.object(ab, "marches_choisis", return_value=("BTC", "GOLD")), \
             patch.object(ab, "inscrire_auto") as activate, \
             patch.object(ab, "activer_coach_live") as commentary:
            marches = ab.demarrer_recherche_positions(etat, "101")

        self.assertEqual(marches, ("BTC", "GOLD"))
        self.assertEqual(activate.call_count, 2)
        activate.assert_any_call(etat, "101", "BTC", notifier=False)
        activate.assert_any_call(etat, "101", "GOLD", notifier=False)
        commentary.assert_not_called()
        self.assertIn("101", etat["recherche_positions_active"])

    def test_search_positions_repairs_empty_market_preference(self):
        etat = {"marches_par_chat": {"101": []}, "recherche_positions_active": []}
        activated = []
        with patch.object(ab, "inscrire_auto", side_effect=lambda state, cid, market, notifier=False: activated.append((cid, market))), \
             patch.object(ab, "selectionner_marches_suivi", wraps=ab.selectionner_marches_suivi) as select:
            marches = ab.demarrer_recherche_positions(etat, "101")

        self.assertEqual(marches, ("BTC", "GOLD"))
        self.assertEqual(set(activated), {("101", "BTC"), ("101", "GOLD")})
        self.assertEqual(set(etat["marches_par_chat"]["101"]), {"BTC", "GOLD"})
        select.assert_called_once_with(etat, "101", ("BTC", "GOLD"))
        self.assertIn("101", etat["recherche_positions_active"])

    def test_search_positions_does_not_bypass_new_subscriber_opt_in(self):
        for selected in ([], ["BTC"]):
            with self.subTest(selected=selected):
                etat = {
                    "coach_pending": ["101"],
                    "marches_par_chat": {"101": selected.copy()},
                    "recherche_positions_active": [],
                }
                with patch.object(ab, "inscrire_auto") as activate:
                    with patch.object(ab, "selectionner_marches_suivi") as save:
                        marches = ab.demarrer_recherche_positions(etat, "101")
                self.assertEqual(marches, ())
                activate.assert_not_called()
                save.assert_not_called()
                self.assertEqual(etat["marches_par_chat"]["101"], selected)
                self.assertEqual(etat["recherche_positions_active"], [])

    def test_searchpos_callback_does_not_activate_pending_subscriber_before_market_validation(self):
        etat = {
            "coach_pending": ["101"],
            "marches_par_chat": {"101": []},
            "recherche_positions_active": [],
        }
        update = {
            "update_id": 99103,
            "callback_query": {
                "id": "searchpos-pending-test",
                "data": "searchpos:BOTH",
                "message": {"chat": {"id": 101, "type": "private"}},
                "from": {"id": 101},
            },
        }
        with patch.object(ab, "telegram", return_value={"ok": True}) as telegram:
            with patch.object(ab, "_envoi_sur") as send:
                with patch.object(ab, "menu_marches") as markets_menu:
                    with patch.object(ab, "inscrire_auto") as activate:
                        ab.traiter(etat, set(), [update])

        self.assertEqual(etat["marches_par_chat"]["101"], [])
        self.assertEqual(etat["recherche_positions_active"], [])
        self.assertEqual(etat["coach_pending"], ["101"])
        activate.assert_not_called()
        markets_menu.assert_called_once()
        self.assertIn("valide", send.call_args.kwargs["text"].lower())
        self.assertTrue(any(call.args[0] == "answerCallbackQuery" for call in telegram.call_args_list))

    def test_autostop_callback_removes_only_selected_market_and_its_chrono(self):
        etat = {
            "auto": {"BTC": ["101", "202"], "GOLD": ["101"]},
            "recherche_positions_active": ["101"],
            "telegram_outbox": [
                {"chat_id": "101", "coach_prealert_markets": ["BTC", "GOLD"], "text": "prealert both"},
                {"chat_id": "101", "coach_prealert_markets": ["BTC"], "text": "prealert btc"},
                {"chat_id": "202", "coach_prealert_markets": ["BTC"], "text": "other chat"},
            ],
            "veille_cloture": {"BTC": {"101": {"multi": True}}, "GOLD": {"101": {"multi": True}}},
            "chrono": {"BTC": {"101": {"mid": 777}}, "GOLD": {"101": {"mid": 888}}},
            "BTC": {"trade": {"qui": {"101": {"fini": False}}}},
            "GOLD": {"trade": {"qui": {"101": {"fini": False}}}},
        }
        update = {
            "update_id": 99102,
            "callback_query": {
                "id": "autostop-btc-test",
                "data": "autostop:BTC",
                "message": {"chat": {"id": 101, "type": "private"}},
                "from": {"id": 101},
            },
        }
        with patch.object(ab, "telegram", return_value={"ok": True}) as telegram, \
             patch.object(ab, "_envoi_sur"):
            ab.traiter(etat, set(), [update])

        self.assertEqual(etat["auto"]["BTC"], ["202"])
        self.assertEqual(etat["auto"]["GOLD"], ["101"])
        self.assertNotIn("101", etat["veille_cloture"]["BTC"])
        self.assertIn("101", etat["veille_cloture"]["GOLD"])
        self.assertNotIn("101", etat["chrono"]["BTC"])
        self.assertIn("101", etat["chrono"]["GOLD"])
        self.assertNotIn("101", etat["BTC"]["trade"]["qui"])
        self.assertIn("101", etat["GOLD"]["trade"]["qui"])
        self.assertIn("101", etat["recherche_positions_active"])
        self.assertEqual(etat["telegram_outbox"][0]["coach_prealert_markets"], ["GOLD"])
        self.assertEqual(len(etat["telegram_outbox"]), 2)
        self.assertEqual(etat["telegram_outbox"][1]["chat_id"], "202")
        ab.desinscrire_auto(etat, "101", "GOLD")
        self.assertNotIn("101", etat["recherche_positions_active"])
        self.assertTrue(any(call.args[0] == "deleteMessage" and call.kwargs.get("message_id") == 777
                            for call in telegram.call_args_list))


if __name__ == "__main__":
    unittest.main()
