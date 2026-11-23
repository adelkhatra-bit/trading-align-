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
        self.old_live_gauge_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "live_gauge_chat_id", None)
        self.old_live_gauge_market = getattr(ab.TELEGRAM_PULL_CONTEXT, "live_gauge_market", None)
        ab.TELEGRAM_PULL_MODE = True
        ab.TOKEN = "test-token"
        ab.TELEGRAM_PULL_CONTEXT.chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.private = False
        ab.TELEGRAM_PULL_CONTEXT.coach_prealert_chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.coach_prealert_markets = frozenset()
        ab.TELEGRAM_PULL_CONTEXT.live_gauge_chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.live_gauge_market = None
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
        ab.TELEGRAM_PULL_CONTEXT.live_gauge_chat_id = self.old_live_gauge_chat
        ab.TELEGRAM_PULL_CONTEXT.live_gauge_market = self.old_live_gauge_market

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

    def test_live_gauge_scope_allows_only_its_chat_and_market(self):
        texte_btc = "🟠 BTC 65000\\n🧭 Alignement 2/3 ⏳"
        texte_gold = "🥇 GOLD 3655\\n🧭 Alignement 1/3 ⏳"

        self.assertFalse(ab._telegram_sortant_autorise(
            "sendMessage", {"chat_id": "-1001", "text": texte_btc}
        ))
        ab.TELEGRAM_PULL_CONTEXT.live_gauge_chat_id = "-1001"
        ab.TELEGRAM_PULL_CONTEXT.live_gauge_market = "BTC"
        self.assertTrue(ab._telegram_sortant_autorise(
            "sendMessage", {"chat_id": "-1001", "text": texte_btc}
        ))
        self.assertTrue(ab._telegram_sortant_autorise(
            "editMessageText", {"chat_id": "-1001", "text": texte_btc}
        ))
        self.assertFalse(ab._telegram_sortant_autorise(
            "sendMessage", {"chat_id": "-1002", "text": texte_btc}
        ))
        self.assertFalse(ab._telegram_sortant_autorise(
            "sendMessage", {"chat_id": "-1001", "text": texte_gold}
        ))
        self.assertFalse(ab._telegram_sortant_autorise(
            "sendPhoto", {"chat_id": "-1001", "caption": texte_btc}
        ))

    def test_market_gauge_sends_one_silent_persistent_message_to_configured_channel(self):
        texte = "🟠 BTC 65000\\n🧭 Alignement 2/3 ⏳"
        cle = {}
        with patch.object(ab, "jauge", return_value=texte):
            sent = self.send_via_real_telegram(
                lambda: ab.maj_jauge(self.state, "BTC", {}, cle, set(), canal="-1001")
            )

        self.assertEqual(len(sent), 1)
        url, params = sent[0]
        self.assertTrue(url.endswith("/sendMessage"))
        self.assertEqual(params["chat_id"], ["-1001"])
        self.assertEqual(params["disable_notification"], ["true"])
        self.assertEqual(cle["jauge"]["-1001"], 55)
        self.assertEqual(cle["jauge_txt"]["-1001"], texte)
        self.assertIsNone(ab.TELEGRAM_PULL_CONTEXT.live_gauge_chat_id)
        self.assertIsNone(ab.TELEGRAM_PULL_CONTEXT.live_gauge_market)

    def test_market_gauge_edits_existing_message_without_creating_a_second_one(self):
        texte = "🟠 BTC 65001\\n🧭 Alignement 3/3 ⏳"
        cle = {
            "jauge": {"-1001": 55},
            "jauge_txt": {"-1001": "ancien contenu"},
            "jauge_t": {"-1001": 1},
        }
        with patch.object(ab, "jauge", return_value=texte):
            sent = self.send_via_real_telegram(
                lambda: ab.maj_jauge(self.state, "BTC", {}, cle, set(), canal="-1001")
            )

        self.assertEqual(len(sent), 1)
        url, params = sent[0]
        self.assertTrue(url.endswith("/editMessageText"))
        self.assertEqual(params["chat_id"], ["-1001"])
        self.assertEqual(params["message_id"], ["55"])
        self.assertEqual(cle["jauge"]["-1001"], 55)
        self.assertEqual(cle["jauge_txt"]["-1001"], texte)
        self.assertIsNone(ab.TELEGRAM_PULL_CONTEXT.live_gauge_chat_id)
        self.assertIsNone(ab.TELEGRAM_PULL_CONTEXT.live_gauge_market)

    def test_blocked_or_failed_gauge_send_is_not_recorded_as_delivered(self):
        texte = "🟠 BTC 65000\\n🧭 Alignement 2/3 ⏳"
        cle = {}
        with patch.object(ab, "jauge", return_value=texte), \\
             patch.object(ab, "http_json", return_value={
                 "ok": False, "result": None, "description": "Envoi refusé"
             }):
            ab.maj_jauge(self.state, "BTC", {}, cle, set(), canal="-1001")

        self.assertNotIn("-1001", cle.get("jauge", {}))
        self.assertNotIn("-1001", cle.get("jauge_txt", {}))
        self.assertIn("-1001", cle.get("jauge_t", {}))
        self.assertIsNone(ab.TELEGRAM_PULL_CONTEXT.live_gauge_chat_id)
        self.assertIsNone(ab.TELEGRAM_PULL_CONTEXT.live_gauge_market)

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
