"""Hard guard: production ALIGN market providers, analysis and chart links accept BTC + GOLD only."""
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import align_bot as ab


class ActiveMarketsBTCGoldOnly(unittest.TestCase):
    def test_registry_and_price_references_contain_only_active_markets(self):
        self.assertEqual(ab.MARCHES, {"BTC": "XBTUSD", "GOLD": "XAUUSD"})
        self.assertEqual(ab.MARCHES_HISTORIQUES, ("BTC", "GOLD"))
        self.assertEqual(set(ab.TV_ETALON), {"XBTUSD", "XAUUSD"})
        self.assertEqual(set(ab.ICONE), {"BTC", "GOLD"})
        self.assertEqual(set(ab.PIP), {"BTC", "GOLD"})

    def test_legacy_nasdaq_pair_is_rejected_before_any_price_provider(self):
        with mock.patch.object(ab, "kraken") as kraken, mock.patch.object(ab, "paxg_or") as gold:
            for pair in ("NAS100", "NASDAQ", "NQ=F"):
                with self.subTest(pair=pair):
                    with self.assertRaises(ValueError):
                        ab.bougies(pair, 5)
            kraken.assert_not_called()
            gold.assert_not_called()

    def test_removed_nasdaq_provider_functions_are_not_available(self):
        self.assertFalse(hasattr(ab, "yahoo_nasdaq"))
        self.assertFalse(hasattr(ab, "nasdaq_direct"))

    def test_chart_link_does_not_redirect_unknown_market_to_gold(self):
        self.assertIn("KRAKEN%3AXBTUSD", ab.url_tradingview("BTC", "5"))
        self.assertIn("FOREXCOM%3AXAUUSD", ab.url_tradingview("GOLD", "5"))
        with self.assertRaises(ValueError):
            ab.url_tradingview("NASDAQ", "5")

    def test_retired_market_is_still_explicitly_refused_not_remapped(self):
        for request in ("NASDAQ", "NAS100", "NQ"):
            with self.subTest(request=request):
                self.assertTrue(ab.marche_retiree_demande(request))
                self.assertIsNone(ab.marche_demande(request))

    def test_retired_market_labels_are_not_in_active_telegram_menus(self):
        self.assertNotIn("💠 Analyse Nasdaq", ab.TRAD)
        self.assertFalse(any("nasdaq" in row[1].lower() or "nasdaq" in row[2].lower()
                             for row in ab.SESSIONS))

    def test_nasdaq_only_legacy_alert_is_not_routed_to_telegram_channel(self):
        message = ab.Msg("NASDAQ : ancienne alerte")
        message.marches = frozenset({"NASDAQ"})
        self.assertEqual(ab.destinataires_message({"canal": "-100123"}, ["12345"], message), [])
        self.assertEqual(ab.destinataires_message({"canal": "-100123"}, ["12345"],
                                                  "NASDAQ : ancienne alerte"), [])


    def test_pinned_rules_text_lists_only_btc_and_gold(self):
        self.assertIn("BTC (BTCUSD)", ab.REGLES)
        self.assertIn("GOLD (XAUUSD)", ab.REGLES)
        self.assertNotRegex(ab.REGLES, r"\b(?:NASDAQ|NAS100|NQ)\b")

    def test_pull_mode_allows_only_exact_rules_to_configured_channel(self):
        cid = "-100123"
        with mock.patch.object(ab, "TELEGRAM_PULL_MODE", True), \
             mock.patch.object(ab, "DERNIER_ETAT", {"canal": cid}), \
             mock.patch.object(ab.TELEGRAM_PULL_CONTEXT, "chat_id", None, create=True), \
             mock.patch.object(ab.TELEGRAM_PULL_CONTEXT, "private", False, create=True):
            self.assertTrue(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": cid, "text": ab.REGLES}
            ))
            self.assertFalse(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": cid, "text": "Message spontané non autorisé"}
            ))
            self.assertFalse(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": "-100999", "text": ab.REGLES}
            ))

    def test_pull_mode_allows_exact_rules_to_registered_market_channels_only(self):
        state = {"canal": "-100vip", "canaux_marche": {"BTC": "-100btc", "GOLD": "-100gold"}}
        with mock.patch.object(ab, "TELEGRAM_PULL_MODE", True), \
             mock.patch.object(ab, "DERNIER_ETAT", state), \
             mock.patch.object(ab.TELEGRAM_PULL_CONTEXT, "chat_id", None, create=True), \
             mock.patch.object(ab.TELEGRAM_PULL_CONTEXT, "private", False, create=True):
            for cid in ("-100vip", "-100btc", "-100gold"):
                with self.subTest(chat=cid):
                    self.assertTrue(ab._telegram_sortant_autorise(
                        "sendMessage", {"chat_id": cid, "text": ab.REGLES}
                    ))
            self.assertFalse(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": "-100random", "text": ab.REGLES}
            ))
            self.assertFalse(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": "-100btc", "text": "Message spontané"}
            ))

    def test_rules_destinations_include_vip_and_market_channels_not_private_chats(self):
        state = {
            "canal": "-100vip",
            "canaux_marche": {"BTC": "-100btc", "GOLD": "-100gold"},
            "prospects": ["555"],
        }
        with mock.patch.object(ab, "REGLES_PRIVEES_SPONTANEES", False):
            self.assertEqual(
                set(ab.destinations_regles(state, ["123", "456"])),
                {"-100vip", "-100btc", "-100gold"},
            )
        with mock.patch.object(ab, "REGLES_PRIVEES_SPONTANEES", True):
            self.assertEqual(
                set(ab.destinations_regles(state, ["123"])),
                {"-100vip", "-100btc", "-100gold", "123", "555"},
            )

    def test_stale_rules_migrate_in_pull_mode_even_if_v6_memory_says_done(self):
        cid = "-100123"
        old_text = ("📌 RÈGLES — ALIGN Signaux\n"
                    "📡 Marchés : BTC (BTCUSD) • GOLD (XAUUSD) • NASDAQ (NAS100)")
        state = {"canal": cid, "epingles_v6": [cid]}
        responses = [
            {"ok": True, "result": {"pinned_message": {"message_id": 19, "text": old_text}}},
            {"ok": True, "result": True},
            {"ok": True, "result": {"message_id": 20}},
            {"ok": True, "result": True},
        ]
        with mock.patch.object(ab, "TOKEN", "test-token"), \
             mock.patch.object(ab, "TELEGRAM_PULL_MODE", True), \
             mock.patch.object(ab, "DERNIER_ETAT", state), \
             mock.patch.object(ab, "http_json", side_effect=responses) as request, \
             mock.patch.object(ab.TELEGRAM_PULL_CONTEXT, "chat_id", None, create=True), \
             mock.patch.object(ab.TELEGRAM_PULL_CONTEXT, "private", False, create=True):
            ab.epingler(state, cid)
        methods = [call.args[0].rsplit("/", 1)[-1] for call in request.call_args_list]
        self.assertEqual(methods, ["getChat", "unpinChatMessage", "sendMessage", "pinChatMessage"])
        self.assertEqual(state["epingles_v7"], [cid])
        self.assertEqual(request.call_count, 4)

    def test_stale_nasdaq_pinned_rules_are_unpinned_and_replaced_once(self):
        cid = "-100123"
        old_text = ("📌 RÈGLES — ALIGN Signaux\n"
                    "📡 Marchés : BTC (BTCUSD) • GOLD (XAUUSD) • NASDAQ (NAS100)")
        state = {"epingles_v5": [cid]}  # l'ancienne mémoire ne doit pas bloquer la migration v7
        with mock.patch.object(ab, "telegram", side_effect=[
            {"ok": True, "result": {"pinned_message": {"message_id": 19, "text": old_text}}},
            {"ok": True, "result": True},
            {"ok": True, "result": {"message_id": 20}},
            {"ok": True, "result": True},
        ]) as telegram:
            ab.epingler(state, cid)
        self.assertEqual([c.args[0] for c in telegram.call_args_list],
                         ["getChat", "unpinChatMessage", "sendMessage", "pinChatMessage"])
        self.assertEqual(state["epingles_v7"], [cid])
        self.assertNotIn(cid, state.get("epingles_v7_pending", {}))
        sent = telegram.call_args_list[2].kwargs["text"]
        self.assertEqual(sent, ab.REGLES)
        self.assertNotIn("NASDAQ", sent)

    def test_pin_diagnostic_identifies_configured_chat_title_without_chat_id(self):
        state = {}
        with mock.patch.object(ab, "telegram", side_effect=[
            {"ok": True, "result": {"title": "ALIGN Gratuit", "pinned_message": {}}},
            {"ok": True, "result": {"message_id": 21}},
            {"ok": True, "result": True},
        ]), mock.patch("builtins.print") as log:
            ab.epingler(state, "-100123")
        output = " ".join(str(call.args[0]) for call in log.call_args_list)
        self.assertIn("chat_title='ALIGN Gratuit'", output)
        self.assertNotIn("-100123", output)

    def test_current_btc_gold_pinned_rules_are_not_duplicated(self):
        cid = "-100123"
        state = {"epingles_v5": [cid]}
        with mock.patch.object(ab, "telegram", return_value={
            "ok": True, "result": {"pinned_message": {"message_id": 20, "text": ab.REGLES}}
        }) as telegram:
            ab.epingler(state, cid)
        self.assertEqual(telegram.call_count, 1)
        self.assertEqual(telegram.call_args.args[0], "getChat")
        self.assertEqual(state["epingles_v7"], [cid])

    def test_failed_unpin_does_not_send_a_duplicate_rules_message(self):
        cid = "-100123"
        old_text = ("📌 RÈGLES — ALIGN Signaux\n"
                    "📡 Marchés : BTC (BTCUSD) • GOLD (XAUUSD) • NASDAQ (NAS100)")
        with mock.patch.object(ab, "telegram", side_effect=[
            {"ok": True, "result": {"pinned_message": {"message_id": 19, "text": old_text}}},
            {"ok": False, "description": "not enough rights"},
        ]) as telegram:
            ab.epingler({}, cid)
        self.assertEqual(telegram.call_count, 2)
        self.assertEqual(telegram.call_args_list[1].args[0], "unpinChatMessage")

    def test_pending_rules_message_is_pinned_without_resending(self):
        cid = "-100123"
        state = {"epingles_v7_pending": {cid: 20}}
        with mock.patch.object(ab, "telegram", return_value={"ok": True, "result": True}) as telegram:
            ab.epingler(state, cid)
        self.assertEqual(telegram.call_count, 1)
        self.assertEqual(telegram.call_args.args[0], "pinChatMessage")
        self.assertEqual(state["epingles_v7"], [cid])
        self.assertNotIn(cid, state["epingles_v7_pending"])


if __name__ == "__main__":
    unittest.main()
