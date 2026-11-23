import json
import os
import tempfile
import unittest
from unittest.mock import patch

import align_bot as ab


OWNER_ID = 4815162342


def message_update(text="/diag", chat_id=OWNER_ID, from_id=OWNER_ID, chat_type="private", update_id=1):
    return {
        "update_id": update_id,
        "message": {
            "message_id": 10,
            "date": 1795431000,
            "chat": {"id": chat_id, "type": chat_type},
            "from": {"id": from_id, "first_name": "ALIGN"},
            "text": text,
        },
    }


class AlignTelegramDiagTests(unittest.TestCase):
    def diag_file(self, directory):
        return os.path.join(directory, "align_diag.json")

    def test_diag_renders_btc_and_gold_counters_read_only(self):
        with tempfile.TemporaryDirectory() as runner_temp:
            path = self.diag_file(runner_temp)
            diagnostic = {
                "version": 1,
                "startedAtMs": 1795430000000,
                "updatedAtMs": 1795431000000,
                "triggerStale": {
                    "BTCUSD": {
                        "count": 3,
                        "lastAtMs": 1795430990000,
                        "lastAgeMs": 720000,
                        "lastThresholdMs": 630000,
                        "lastEntryTfMs": 300000,
                    },
                    "XAUUSD": {
                        "count": 1,
                        "lastAtMs": 1795430980000,
                        "lastAgeMs": 900000,
                        "lastThresholdMs": 7230000,
                        "lastEntryTfMs": 3600000,
                    },
                },
            }
            with open(path, "w", encoding="utf-8") as stream:
                json.dump(diagnostic, stream)
            before = Path(path).read_text(encoding="utf-8")
            with patch.dict(os.environ, {"RUNNER_TEMP": runner_temp}):
                rendered = ab.texte_diag(str(OWNER_ID))
            after = Path(path).read_text(encoding="utf-8")
            self.assertIn("BTC", rendered)
            self.assertIn("GOLD", rendered)
            self.assertIn("3", rendered)
            self.assertIn("1", rendered)
            self.assertIn("720", rendered)
            self.assertIn("630", rendered)
            self.assertIn("lecture seule", rendered.lower())
            self.assertEqual(after, before)

    def test_diag_missing_file_explains_no_event_or_bridge_not_started(self):
        with tempfile.TemporaryDirectory() as runner_temp, patch.dict(os.environ, {"RUNNER_TEMP": runner_temp}):
            rendered = ab.texte_diag(str(OWNER_ID))
        self.assertIn("aucun rejet", rendered.lower())
        self.assertIn("bridge", rendered.lower())
        self.assertIn("démarré", rendered.lower())

    def test_diag_corrupt_file_returns_safe_message_without_raising(self):
        with tempfile.TemporaryDirectory() as runner_temp:
            with open(self.diag_file(runner_temp), "w", encoding="utf-8") as stream:
                stream.write("{not-json")
            with patch.dict(os.environ, {"RUNNER_TEMP": runner_temp}):
                rendered = ab.texte_diag(str(OWNER_ID))
        self.assertIn("illisible", rendered.lower())

    def test_diag_owner_private_command_runs_before_first_visit_logic(self):
        state = {"proprio": [OWNER_ID], "prospects": []}
        chats = set()
        update = message_update("/diag@align_mtf_adel_bot")
        with patch.object(ab, "texte_diag", return_value="📊 DIAGNOSTIC TEST") as diagnostic, \
             patch.object(ab, "_envoi_sur", return_value={"ok": True}) as send:
            result = ab.traiter(state, chats, [update])
        self.assertEqual(result, [])
        send.assert_called_once()
        self.assertEqual(str(send.call_args.args[0]), str(OWNER_ID))
        self.assertIn("DIAGNOSTIC TEST", send.call_args.kwargs["text"])
        diagnostic.assert_called_once_with(str(OWNER_ID))
        self.assertEqual(state["prospects"], [])
        self.assertEqual(chats, set())

    def test_diag_denies_non_owner_even_when_free_positions_are_enabled(self):
        visitor_id = OWNER_ID + 1
        state = {"proprio": [OWNER_ID], "prospects": []}
        with patch.object(ab, "POSITIONS_GRATUITES", True), \
             patch.object(ab, "_envoi_sur", return_value={"ok": True}) as send:
            ab.traiter(state, set(), [message_update("/diag", visitor_id, visitor_id)])
        send.assert_called_once()
        self.assertIn("réservée au propriétaire", send.call_args.kwargs["text"].lower())
        self.assertNotIn("TRIGGER_STALE", send.call_args.kwargs["text"])
        self.assertEqual(state["prospects"], [])

    def test_diag_rejects_private_sender_chat_id_mismatch(self):
        state = {"proprio": [OWNER_ID], "prospects": []}
        with patch.object(ab, "_envoi_sur") as send:
            ab.traiter(state, set(), [message_update("/diag", OWNER_ID, OWNER_ID + 5)])
        send.assert_not_called()
        self.assertEqual(state["prospects"], [])

    def test_diag_in_group_is_ignored_without_public_reply(self):
        state = {"proprio": [OWNER_ID], "prospects": []}
        with patch.object(ab, "_envoi_sur") as send:
            ab.traiter(state, set(), [message_update("/diag", -100123, OWNER_ID, "supergroup")])
        send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
