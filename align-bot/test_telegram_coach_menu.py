import json
import unittest
from unittest.mock import patch

import align_bot as ab


class TelegramCoachMenuTests(unittest.TestCase):
    def test_live_menu_separates_commentator_next_position_and_twelve_timeframes(self):
        etat = {"live_on": True, "proprio": ["101"]}
        keyboard = json.loads(ab.clavier_live(etat, "101"))
        buttons = [button for row in keyboard["inline_keyboard"] for button in row]
        callbacks = {button.get("callback_data"): button["text"] for button in buttons}

        self.assertIn("coachlive:BTC", callbacks)
        self.assertIn("auto:BTC", callbacks)
        self.assertIn("timeframes:BTC", callbacks)
        self.assertIn("Commentaire BTC", callbacks["coachlive:BTC"])
        self.assertIn("Coach position BTC", callbacks["auto:BTC"])
        self.assertIn("12 UT BTC", callbacks["timeframes:BTC"])
        self.assertNotEqual(callbacks["coachlive:BTC"], callbacks["auto:BTC"])

    def test_english_live_menu_keeps_labels_in_english(self):
        etat = {"live_on": True, "proprio": ["101"]}
        keyboard = json.loads(ab.clavier_live(etat, "101", anglais=True))
        buttons = [button for row in keyboard["inline_keyboard"] for button in row]
        labels = [button["text"] for button in buttons]

        self.assertIn("Commentary BTC", labels)
        self.assertIn("Next position BTC", labels)
        self.assertIn("12 timeframes BTC", labels)
        self.assertNotIn("Commentaire BTC", labels)
        self.assertNotIn("Coach position BTC", labels)

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


if __name__ == "__main__":
    unittest.main()
