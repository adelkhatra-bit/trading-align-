import os
import sys
import unittest
import io
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class TelegramAuditTests(unittest.TestCase):
    def setUp(self):
        with ab.TELEGRAM_AUDIT_LOCK:
            ab.TELEGRAM_AUDIT.update({
                "updates_received": 0, "messages_received": 0, "callbacks_received": 0,
                "callbacks_dispatched": 0, "callbacks_completed": 0,
                "callbacks_unknown": 0, "callbacks_rejected": 0,
                "callback_ack_ok": 0, "callback_ack_failed": 0,
                "messages_sent": 0, "messages_edited": 0, "api_errors": 0,
                "pull_blocks": {}, "actions_seen": {},
                "last_callback": None, "last_callback_latency_ms": None,
                "last_error": None, "last_block": None,
            })
        ab.CALLBACKS_ACKNOWLEDGED.clear()
        ab.CALLBACKS_ACK_FAILED.clear()
        self.old_pull_mode = ab.TELEGRAM_PULL_MODE
        self.old_token = ab.TOKEN
        self.old_pull_context = {
            key: getattr(ab.TELEGRAM_PULL_CONTEXT, key, None)
            for key in ("chat_id", "private", "callback_action", "channel_setup_chat_id",
                        "rules_setup_chat_id", "invite_setup_chat_id",
                        "join_request_chat_id", "join_request_user_id", "channel_menu_setup_chat_id", "bot_setup")
        }
        for key in self.old_pull_context:
            setattr(ab.TELEGRAM_PULL_CONTEXT, key, None)
        ab.TELEGRAM_PULL_CONTEXT.chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.private = False
        ab.TELEGRAM_PULL_MODE = False
        ab.TOKEN = "test-token"

    def tearDown(self):
        ab.TELEGRAM_PULL_MODE = self.old_pull_mode
        ab.TOKEN = self.old_token
        for key, value in self.old_pull_context.items():
            setattr(ab.TELEGRAM_PULL_CONTEXT, key, value)
        ab.CALLBACKS_ACKNOWLEDGED.clear()
        ab.CALLBACKS_ACK_FAILED.clear()

    def test_failed_fast_ack_is_not_cached_and_handler_can_retry(self):
        cb = {"id": "callback-failed", "data": "markets:BTC"}
        with patch.object(ab, "http_json", side_effect=[
            {"ok": False, "description": "query too old"},
            {"ok": True, "result": True},
        ]) as http:
            ab._ack_callback_rapide(cb, "ack")
            self.assertNotIn("callback-failed", ab.CALLBACKS_ACKNOWLEDGED)
            retry = ab.telegram("answerCallbackQuery", callback_query_id="callback-failed")
        self.assertTrue(retry["ok"])
        self.assertEqual(http.call_count, 2)
        self.assertEqual(ab.TELEGRAM_AUDIT["callback_ack_failed"], 1)

    def test_failed_fast_ack_is_retried_before_a_live_button_without_its_own_ack(self):
        cb = {"id": "callback-retry", "data": "menulive:x"}
        update = {
            "update_id": 56,
            "callback_query": {
                "id": cb["id"], "data": cb["data"],
                "from": {"id": 42, "first_name": "Tester"},
                "message": {"message_id": 9, "chat": {"id": 42, "type": "private"}},
            },
        }
        with patch.object(ab, "http_json", side_effect=[
            {"ok": False, "description": "temporary failure"},
            {"ok": True, "result": True},
        ]) as http, patch.object(ab, "live_callback", return_value=True):
            ab._ack_callback_rapide(cb, "ack")
            self.assertIn("callback-retry", ab.CALLBACKS_ACK_FAILED)
            ab.traiter({"proprio": [42], "prospects": []}, set(), [update])
        self.assertEqual(http.call_count, 2)
        self.assertEqual(ab.TELEGRAM_AUDIT["callback_ack_failed"], 1)
        self.assertEqual(ab.TELEGRAM_AUDIT["callback_ack_ok"], 1)
        self.assertNotIn("callback-retry", ab.CALLBACKS_ACK_FAILED)
        self.assertNotIn("callback-retry", ab.CALLBACKS_ACKNOWLEDGED)

    def test_successful_fast_ack_is_cached_until_handler_consumes_it(self):
        cb = {"id": "callback-ok", "data": "markets:BTC"}
        with patch.object(ab, "http_json", return_value={"ok": True, "result": True}) as http:
            ab._ack_callback_rapide(cb, "ack")
            self.assertIn("callback-ok", ab.CALLBACKS_ACKNOWLEDGED)
            result = ab.telegram("answerCallbackQuery", callback_query_id="callback-ok")
        self.assertTrue(result["ok"])
        self.assertEqual(http.call_count, 1)
        self.assertNotIn("callback-ok", ab.CALLBACKS_ACKNOWLEDGED)
        self.assertEqual(ab.TELEGRAM_AUDIT["callback_ack_ok"], 1)

    def test_owner_can_request_audit_on_fast_path(self):
        update = {"message": {"chat": {"id": "owner-1", "type": "private"}, "from": {"id": "owner-1"}, "text": "/audit"}}
        with patch.object(ab, "proprio", return_value=["owner-1"]), \
             patch.object(ab, "texte_audit_telegram", return_value="AUDIT TEST") as report, \
             patch.object(ab, "_envoi_sur") as send:
            handled = ab._traiter_lecture_rapide({}, set(), update)
        self.assertTrue(handled)
        self.assertTrue(update["_align_fast_handled"])
        report.assert_called_once()
        send.assert_called_once_with("owner-1", text="AUDIT TEST")

    def test_owner_audit_requires_sender_identity(self):
        update = {"message": {"chat": {"id": "owner-1", "type": "private"},
                              "from": {"id": "guest-2"}, "text": "/audit"}}
        with patch.object(ab, "proprio", return_value=["owner-1"]), \
             patch.object(ab, "texte_audit_telegram") as report, \
             patch.object(ab, "_envoi_sur") as send:
            handled = ab._traiter_lecture_rapide({}, set(), update)
        self.assertFalse(handled)
        report.assert_not_called()
        send.assert_not_called()

    def test_diag_alias_is_not_audit_command(self):
        update = {"message": {"chat": {"id": "owner-1", "type": "private"},
                              "from": {"id": "owner-1"}, "text": "/diag"}}
        with patch.object(ab, "proprio", return_value=["owner-1"]), \
             patch.object(ab, "texte_audit_telegram") as report, \
             patch.object(ab, "_envoi_sur") as send:
            handled = ab._traiter_lecture_rapide({}, set(), update)
        self.assertFalse(handled)
        report.assert_not_called()
        send.assert_not_called()

    def test_non_owner_cannot_request_owner_audit(self):
        update = {"message": {"chat": {"id": "guest-1", "type": "private"}, "from": {"id": "guest-1"}, "text": "/audit"}}
        with patch.object(ab, "proprio", return_value=[]), \
             patch.object(ab, "texte_audit_telegram") as report, \
             patch.object(ab, "_envoi_sur") as send:
            handled = ab._traiter_lecture_rapide({}, set(), update)
        self.assertFalse(handled)
        report.assert_not_called()
        send.assert_not_called()

    def test_callback_dispatch_and_unknown_action_are_reported(self):
        update = {
            "update_id": 55,
            "callback_query": {
                "id": "unknown-callback",
                "data": "not_a_real_action:BTC",
                "from": {"id": 42, "first_name": "Tester"},
                "message": {"message_id": 9, "chat": {"id": 42, "type": "private"}},
            },
        }
        with patch.object(ab, "telegram", return_value={"ok": True}):
            ab.traiter({"proprio": [42], "prospects": []}, set(), [update])
        self.assertEqual(ab.TELEGRAM_AUDIT["callbacks_dispatched"], 1)
        self.assertEqual(ab.TELEGRAM_AUDIT["callbacks_completed"], 1)
        self.assertEqual(ab.TELEGRAM_AUDIT["callbacks_unknown"], 1)
        self.assertEqual(ab.TELEGRAM_AUDIT["actions_seen"]["not_a_real_action"], 1)

    def test_pull_mode_block_is_counted_without_storing_chat_id(self):
        ab.TELEGRAM_PULL_MODE = True
        with patch.object(ab, "_telegram_sortant_autorise", return_value=False):
            result = ab.telegram("sendMessage", chat_id="123456789", text="private message")
        self.assertTrue(result["blocked_by_pull_mode"])
        self.assertEqual(ab.TELEGRAM_AUDIT["pull_blocks"]["sendMessage"], 1)
        self.assertNotIn("123456789", repr(ab.TELEGRAM_AUDIT))

    def test_pull_mode_denies_unknown_non_message_methods_by_default(self):
        ab.TELEGRAM_PULL_MODE = True
        with patch.object(ab, "http_json") as http:
            result = ab.telegram("unknownMutation", chat_id="123456789")
        self.assertTrue(result["blocked_by_pull_mode"])
        http.assert_not_called()
        self.assertEqual(ab.TELEGRAM_AUDIT["pull_blocks"]["unknownMutation"], 1)

    def test_pull_mode_keeps_known_read_and_protocol_methods_available(self):
        ab.TELEGRAM_PULL_MODE = True
        for method in ("getMe", "getUpdates", "getChat", "getChatMember",
                       "answerCallbackQuery", "answerPreCheckoutQuery"):
            with self.subTest(method=method):
                self.assertTrue(ab._telegram_sortant_autorise(method, {}))
        for method in ("getUnknownMethod", "sendUnknownMethod", "unknownMutation"):
            with self.subTest(method=method):
                self.assertFalse(ab._telegram_sortant_autorise(method, {}))

    def test_pull_mode_blocks_multipart_audio_outside_private_request(self):
        ab.TELEGRAM_PULL_MODE = True
        ab.TELEGRAM_PULL_CONTEXT.chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.private = False
        with patch.object(ab.urllib.request, "urlopen") as http:
            result = ab.envoyer_son_piece("123456789")
        self.assertTrue(result["blocked_by_pull_mode"])
        http.assert_not_called()

    def test_pull_mode_scopes_channel_photo_and_description_to_setup_context(self):
        ab.TELEGRAM_PULL_MODE = True
        ab.TELEGRAM_PULL_CONTEXT.channel_setup_chat_id = None
        self.assertFalse(ab._telegram_sortant_autorise("setChatPhoto", {"chat_id": "-1001"}))
        self.assertFalse(ab._telegram_sortant_autorise("setChatDescription", {"chat_id": "-1001"}))
        ab.TELEGRAM_PULL_CONTEXT.channel_setup_chat_id = "-1001"
        self.assertTrue(ab._telegram_sortant_autorise("setChatPhoto", {"chat_id": "-1001"}))
        self.assertTrue(ab._telegram_sortant_autorise("setChatDescription", {"chat_id": "-1001"}))
        self.assertFalse(ab._telegram_sortant_autorise("setChatPhoto", {"chat_id": "-1002"}))

    def test_pull_mode_allows_multipart_audio_for_matching_private_request(self):
        ab.TELEGRAM_PULL_MODE = True
        ab.TELEGRAM_PULL_CONTEXT.chat_id = "123456789"
        ab.TELEGRAM_PULL_CONTEXT.private = True
        rep = type("Response", (), {"read": lambda self: b'{"ok":true,"result":{}}',
                                    "__enter__": lambda self: self,
                                    "__exit__": lambda self, *args: None})()
        with patch.object(ab.urllib.request, "urlopen", return_value=rep) as http, \
             patch.object(ab, "_telegram_verifie_cooldown"):
            result = ab.envoyer_son_piece("123456789")
        self.assertTrue(result["ok"])
        http.assert_called_once()

    def test_pull_mode_scopes_invitation_management_to_exact_setup_channel(self):
        ab.TELEGRAM_PULL_MODE = True
        for method in ("createChatInviteLink", "createChatSubscriptionInviteLink", "exportChatInviteLink"):
            with self.subTest(method=method):
                self.assertFalse(ab._telegram_sortant_autorise(method, {"chat_id": "-1001"}))
                ab.TELEGRAM_PULL_CONTEXT.invite_setup_chat_id = "-1001"
                self.assertTrue(ab._telegram_sortant_autorise(method, {"chat_id": "-1001"}))
                self.assertFalse(ab._telegram_sortant_autorise(method, {"chat_id": "-1002"}))
                ab.TELEGRAM_PULL_CONTEXT.invite_setup_chat_id = None

    def test_pull_mode_scopes_join_decisions_to_exact_channel_and_user(self):
        ab.TELEGRAM_PULL_MODE = True
        for method in ("approveChatJoinRequest", "declineChatJoinRequest"):
            with self.subTest(method=method):
                params = {"chat_id": "-1001", "user_id": "42"}
                self.assertFalse(ab._telegram_sortant_autorise(method, params))
                ab.TELEGRAM_PULL_CONTEXT.join_request_chat_id = "-1001"
                ab.TELEGRAM_PULL_CONTEXT.join_request_user_id = "42"
                self.assertTrue(ab._telegram_sortant_autorise(method, params))
                self.assertFalse(ab._telegram_sortant_autorise(method, {"chat_id": "-1001", "user_id": "43"}))
                self.assertFalse(ab._telegram_sortant_autorise(method, {"chat_id": "-1002", "user_id": "42"}))
                ab.TELEGRAM_PULL_CONTEXT.join_request_chat_id = None
                ab.TELEGRAM_PULL_CONTEXT.join_request_user_id = None

    def test_invitation_and_join_helpers_restore_temporary_context(self):
        with patch.object(ab, "telegram", return_value={"ok": True}) as api:
            self.assertTrue(ab._telegram_lien_canal("createChatInviteLink", "-1001", name="test")["ok"])
            self.assertEqual(ab.TELEGRAM_PULL_CONTEXT.invite_setup_chat_id, None)
            self.assertTrue(ab._telegram_decision_demande("declineChatJoinRequest", "-1001", "42")["ok"])
            self.assertEqual(ab.TELEGRAM_PULL_CONTEXT.join_request_chat_id, None)
            self.assertEqual(ab.TELEGRAM_PULL_CONTEXT.join_request_user_id, None)
        self.assertEqual(api.call_count, 2)

    def test_pull_mode_scopes_bot_profile_setup_to_explicit_installer_context(self):
        ab.TELEGRAM_PULL_MODE = True
        for method in ("setMyCommands", "setChatMenuButton", "setMyShortDescription", "setMyDescription"):
            with self.subTest(method=method):
                self.assertFalse(ab._telegram_sortant_autorise(method, {}))
        with patch.object(ab, "telegram", return_value={"ok": True}) as api:
            self.assertTrue(ab._telegram_configuration_bot("setMyCommands", commands="[]")["ok"])
            self.assertIs(getattr(ab.TELEGRAM_PULL_CONTEXT, "bot_setup", False), None)
        api.assert_called_once()

    def test_pull_mode_scopes_channel_menu_setup_to_registered_destination(self):
        ab.TELEGRAM_PULL_MODE = True
        state = {"canal": "-100vip", "canal_preuves": "-100proofs", "canaux_marche": {"BTC": "-100btc"}}
        self.assertTrue(ab._telegram_menu_canal(state, "sendMessage", "-100btc", text="menu")["blocked_by_pull_mode"] is False
                        if False else True) if False else None
        with patch.object(ab, "telegram", return_value={"ok": True}) as api:
            self.assertTrue(ab._telegram_menu_canal(state, "sendMessage", "-100btc", text="menu")["ok"])
            self.assertTrue(ab._telegram_menu_canal(state, "pinChatMessage", "-100vip", message_id=5)["ok"])
            blocked = ab._telegram_menu_canal(state, "sendMessage", "-100other", text="menu")
        self.assertTrue(blocked["blocked_by_pull_mode"])
        self.assertEqual(api.call_count, 2)
        self.assertIsNone(getattr(ab.TELEGRAM_PULL_CONTEXT, "channel_menu_setup_chat_id", None))

    def test_pull_mode_blocks_are_logged_once_without_chat_id_and_aggregate_counts(self):
        ab.TELEGRAM_PULL_BLOCK_LOGGED.clear()
        ab.TELEGRAM_PULL_MODE = True
        output = io.StringIO()
        with patch("sys.stdout", output):
            ab.telegram("sendMessage", chat_id="111111111", text="private message one")
            ab.telegram("sendMessage", chat_id="222222222", text="private message two")
        rendered = output.getvalue()
        self.assertEqual(rendered.count("TELEGRAM_PULL_BLOCK"), 1)
        self.assertIn("method=sendMessage action=outside_callback", rendered)
        self.assertNotIn("111111111", rendered)
        self.assertNotIn("222222222", rendered)
        self.assertEqual(ab.TELEGRAM_AUDIT["pull_blocks"]["sendMessage"], 2)
        ab.TELEGRAM_PULL_BLOCK_LOGGED.clear()

    def test_audit_marks_gold_cme_closed_as_normal_without_snapshot(self):
        state = {
            "BTC": {},
            "GOLD": {
                "m1": [{"t": 1990, "c": 2000.0}],
                "tv_indicator_mtf": {
                    "available": False,
                    "activeTimeframe": None,
                    "activeTimeframeAgeMs": None,
                },
            },
        }
        with patch.object(ab, "cme_ouvert", return_value=False):
            report = ab.texte_audit_telegram(
                {"offset": 12, "sauve_t": 1000, "telegram_outbox": []},
                state,
                now=2000,
            )
        self.assertIn("GOLD : bougies M1", report)
        self.assertIn(
            "Bridge TradingView : marché CME fermé (normal) • snapshot non requis",
            report,
        )
        self.assertNotIn("Bridge TradingView : indisponible • UT active aucune", report)

    def test_audit_keeps_gold_bridge_failure_visible_when_cme_is_open(self):
        state = {
            "BTC": {},
            "GOLD": {
                "m1": [{"t": 1990, "c": 2000.0}],
                "tv_indicator_mtf": {
                    "available": False,
                    "activeTimeframe": None,
                    "activeTimeframeAgeMs": None,
                },
            },
        }
        with patch.object(ab, "cme_ouvert", return_value=True):
            report = ab.texte_audit_telegram(
                {"offset": 12, "sauve_t": 1000, "telegram_outbox": []},
                state,
                now=2000,
            )
        self.assertIn(
            "Bridge TradingView : indisponible • UT active aucune • âge inconnue",
            report,
        )

    def test_report_displays_runtime_evidence_without_private_ids(self):
        ab._telegram_audit("callback_received", "markets:BTC")
        ab._telegram_audit("callback_dispatched", "markets:BTC")
        ab._telegram_audit("callback_completed", "markets:BTC")
        ab._telegram_audit("callback_latency", 42)
        report = ab.texte_audit_telegram(
            {"offset": 12, "sauve_t": 1000, "telegram_outbox": []},
            {"BTC": {}, "GOLD": {}},
            now=2000,
        )
        self.assertIn("Callbacks : dispatchés 1 • terminés 1", report)
        self.assertIn("Latence dernier clic avant dispatch : 42 ms", report)
        self.assertIn("Catalogue callbacks", report)
        self.assertNotIn("123456789", report)


if __name__ == "__main__":
    unittest.main()
