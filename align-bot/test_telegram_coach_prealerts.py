import os
import sys
import urllib.parse
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class TelegramCoachPrealertPullGate(unittest.TestCase):
    def setUp(self):
        self.old_mode = ab.TELEGRAM_PULL_MODE
        self.old_state = ab.DERNIER_ETAT
        self.old_token = ab.TOKEN
        self.old_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "chat_id", None)
        self.old_private = getattr(ab.TELEGRAM_PULL_CONTEXT, "private", False)
        self.old_prealert_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_prealert_chat_id", None)
        self.old_prealert_markets = getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_prealert_markets", None)
        ab.TELEGRAM_PULL_MODE = True
        ab.TOKEN = "test-token"
        ab.TELEGRAM_PULL_CONTEXT.chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.private = False
        ab.TELEGRAM_PULL_CONTEXT.coach_prealert_chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.coach_prealert_markets = frozenset()
        self.state = {
            "canal": "-1001",
            "canaux_marche": {"BTC": "-1002", "GOLD": "-1003"},
            "auto": {"BTC": ["42"], "GOLD": []},
            "bot_off": [],
            "quiet": [],
            "marches_par_chat": {"42": ["BTC"]},
        }
        ab.DERNIER_ETAT = self.state

    def tearDown(self):
        ab.TELEGRAM_PULL_MODE = self.old_mode
        ab.DERNIER_ETAT = self.old_state
        ab.TOKEN = self.old_token
        ab.TELEGRAM_PULL_CONTEXT.chat_id = self.old_chat
        ab.TELEGRAM_PULL_CONTEXT.private = self.old_private
        ab.TELEGRAM_PULL_CONTEXT.coach_prealert_chat_id = self.old_prealert_chat
        ab.TELEGRAM_PULL_CONTEXT.coach_prealert_markets = self.old_prealert_markets

    def send_via_real_telegram(self, callback):
        sent = []

        def fake_http(url, data=None, **kwargs):
            sent.append((url, urllib.parse.parse_qs(data.decode("utf-8"))))
            return {"ok": True, "result": {"message_id": 55, "chat": {"id": 42}}}

        with patch.object(ab, "http_json", side_effect=fake_http):
            callback()
        return sent

    def test_opted_in_btc_coach_receives_safe_private_prealert_only(self):
        sent = self.send_via_real_telegram(
            lambda: ab.diffuser_alerte(
                self.state, {"42"},
                ["📊 BTC : alignement en progression, configuration proche."],
                ["📊 BTC: alignment improving, setup getting closer."],
            )
        )
        self.assertEqual(len(sent), 1, "one selected private coach; channels must not receive a pre-alert")
        url, params = sent[0]
        self.assertTrue(url.endswith("/sendMessage"))
        self.assertEqual(params["chat_id"], ["42"])
        self.assertIn("BTC", params["text"][0])
        self.assertFalse(any(k in params["text"][0].lower() for k in ("entry:", "sl:", "tp1:")))
        self.assertIsNone(ab.TELEGRAM_PULL_CONTEXT.coach_prealert_chat_id)
        self.assertFalse(ab.TELEGRAM_PULL_CONTEXT.coach_prealert_markets)

    def test_diffuser_messages_uses_the_same_private_coach_scope(self):
        sent = self.send_via_real_telegram(
            lambda: ab.diffuser_messages(
                self.state, {"42"},
                [("BTC", "📊 BTC : marché en préparation, signal à confirmer.")],
            )
        )
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][1]["chat_id"], ["42"])

    def test_diffuser_evenements_uses_the_same_private_coach_scope(self):
        sent = self.send_via_real_telegram(
            lambda: ab.diffuser_evenements(
                self.state, {"42"},
                [({"BTC"}, ["📊 BTC : configuration en approche."],
                  ["📊 BTC: setup approaching."])],
            )
        )
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][1]["chat_id"], ["42"])

    def test_prealert_scope_is_restored_even_when_send_raises(self):
        with patch.object(ab, "_envoi_sur", side_effect=RuntimeError("simulated send failure")):
            with self.assertRaises(RuntimeError):
                ab._telegram_envoyer_coach_prealerte(
                    self.state, "42", "📊 BTC : configuration à surveiller", {"BTC"}
                )
        self.assertIsNone(ab.TELEGRAM_PULL_CONTEXT.coach_prealert_chat_id)
        self.assertEqual(ab.TELEGRAM_PULL_CONTEXT.coach_prealert_markets, frozenset())

    def test_market_scope_denies_gold_only_subscriber_from_btc_prealert(self):
        self.state["auto"] = {"BTC": [], "GOLD": ["42"]}
        self.state["marches_par_chat"] = {"42": ["GOLD"]}
        sent = self.send_via_real_telegram(
            lambda: ab.diffuser_alerte(
                self.state, {"42"}, ["📊 BTC : marché à surveiller"], ["📊 BTC: watch market"]
            )
        )
        self.assertEqual(sent, [])

    def test_quiet_or_bot_off_coach_does_not_receive_prealert(self):
        for state_key in ("quiet", "bot_off"):
            with self.subTest(state_key=state_key):
                self.state[state_key] = ["42"]
                sent = self.send_via_real_telegram(
                    lambda: ab.diffuser_alerte(
                        self.state, {"42"}, ["📊 BTC : configuration à surveiller"],
                        ["📊 BTC: setup to watch"],
                    )
                )
                self.assertEqual(sent, [])
                self.state[state_key] = []

    def test_unsubscribed_private_chat_does_not_receive_prealert(self):
        self.state["auto"]["BTC"] = []
        sent = self.send_via_real_telegram(
            lambda: ab.diffuser_alerte(
                self.state, {"42"}, ["📊 BTC : configuration à surveiller"],
                ["📊 BTC: setup to watch"],
            )
        )
        self.assertEqual(sent, [])

    def test_unconfirmed_message_with_entry_sl_or_tp_levels_is_never_prealert(self):
        texte = "📊 BTC : configuration en cours\nEntrée : 65000\nSL : 64500\nTP1 : 66000"
        sent = self.send_via_real_telegram(
            lambda: ab.diffuser_alerte(self.state, {"42"}, texte.split("\n"), texte.split("\n"))
        )
        self.assertEqual(sent, [])

    def test_channel_prealerts_and_edit_operations_remain_blocked(self):
        self.assertFalse(ab._telegram_sortant_autorise(
            "sendMessage", {"chat_id": "-1002", "text": "📊 BTC : configuration proche"}
        ))
        ab.TELEGRAM_PULL_CONTEXT.coach_prealert_chat_id = "42"
        ab.TELEGRAM_PULL_CONTEXT.coach_prealert_markets = frozenset({"BTC"})
        self.assertFalse(ab._telegram_sortant_autorise(
            "editMessageText", {"chat_id": "42", "text": "📊 BTC : configuration proche"}
        ))
        self.assertFalse(ab._telegram_sortant_autorise(
            "sendMessage", {"chat_id": "43", "text": "📊 BTC : configuration proche"}
        ))


if __name__ == "__main__":
    unittest.main()
