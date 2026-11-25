import unittest
from unittest.mock import patch

import align_bot as ab


class TelegramMarketChannelCommentaryTests(unittest.TestCase):
    def test_m15_commentary_reaches_only_its_configured_channel_in_pull_mode(self):
        state = {"canaux_marche": {"BTC": "-100btc"}}
        result = {"b15": [{"t": 1000}, {"t": 2000}]}

        with patch.object(ab, "TOKEN", "test-token"), \
             patch.object(ab, "TELEGRAM_PULL_MODE", True), \
             patch.object(ab, "DERNIER_ETAT", state), \
             patch.object(ab, "http_json", return_value={"ok": True, "result": {"message_id": 42}}) as request, \
             patch.object(ab, "texte_coach_live", return_value="🎙 COACH COMMENTATEUR\nℹ️ Info, pas une entrée"), \
             patch.object(ab, "boutons_chaine_marche", return_value=None):
            ab.notifier_canal_marche(state, "BTC", result, {})

        self.assertEqual(request.call_count, 1)
        self.assertEqual(state["canal_live"]["BTC"]["dernier_t"], 2000)
        self.assertIn("-100btc", str(request.call_args))

    def test_market_commentary_permission_rejects_wrong_channel_market_and_trade_levels(self):
        state = {"canaux_marche": {"BTC": "-100btc"}}
        old_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_chat_id", None)
        old_market = getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_market", None)
        with patch.object(ab, "TELEGRAM_PULL_MODE", True), patch.object(ab, "DERNIER_ETAT", state):
            ab.TELEGRAM_PULL_CONTEXT.market_commentary_chat_id = "-100btc"
            ab.TELEGRAM_PULL_CONTEXT.market_commentary_market = "BTC"
            try:
                self.assertTrue(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "-100btc", "text": "🎙 BILAN 15 MIN — Info, pas une entrée"}
                ))
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "-100other", "text": "🎙 BILAN 15 MIN"}
                ))
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "-100btc", "text": "Entry 100 / SL 95 / TP 110"}
                ))
                ab.TELEGRAM_PULL_CONTEXT.market_commentary_market = "NASDAQ"
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "-100btc", "text": "🎙 BILAN 15 MIN"}
                ))
                ab.TELEGRAM_PULL_CONTEXT.market_commentary_market = "BTC"
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendPhoto", {"chat_id": "-100btc", "caption": "🎙 BILAN 15 MIN"}
                ))
            finally:
                ab.TELEGRAM_PULL_CONTEXT.market_commentary_chat_id = old_chat
                ab.TELEGRAM_PULL_CONTEXT.market_commentary_market = old_market

    def test_commentary_helper_restores_temporary_permission_after_send(self):
        state = {"canaux_marche": {"GOLD": "-100gold"}}
        old_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_chat_id", None)
        old_market = getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_market", None)
        with patch.object(ab, "_envoi_sur", side_effect=lambda *a, **k: (
            getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_chat_id", None),
            getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_market", None),
        )) as send:
            result = ab._telegram_envoyer_commentaire_canal(state, "GOLD", "-100gold", "Commentaire")
        self.assertEqual(result, ("-100gold", "GOLD"))
        send.assert_called_once()
        self.assertEqual(getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_chat_id", None), old_chat)
        self.assertEqual(getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_market", None), old_market)


    def test_live_coach_commentary_and_activation_are_fully_translated(self):
        candle = {"o": 100.0, "h": 102.0, "l": 99.0, "c": 101.0, "t": 2000}
        market = {
            "m1": [{"c": 101.0}],
            "b15": [candle, {"o": 100.0, "h": 102.0, "l": 99.0, "c": 101.0, "t": 2000}],
            "confirme": 1,
            "dirs": [1] * 11,
            "sqzs": [0] * 11,
        }
        with patch.object(ab, "prochaine_cloture_bougie", return_value=3000):
            french = ab.texte_coach_live("BTC", candle, market, {}, public=True)
        english = ab.traduire(french)
        for expected in (
            "LIVE COMMENTATOR", "LIVE", "15-MINUTE SUMMARY", "Information, not an entry",
            "Candle rising", "Range:", "Trend:", "Timeframes:", "Next:",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, english)
        for french_label in ("COACH COMMENTATEUR", "BILAN 15 MIN", "Bougie en hausse",
                             "Écart :", "Tendance :", "Unités :", "Prochaine :"):
            with self.subTest(french_label=french_label):
                self.assertNotIn(french_label, english)

        activation = (
            "🎙 COACH COMMENTATEUR ACTIVÉ — BTC\n"
            "🔎 Surveillance continue : je cherche une configuration d'entrée confirmée, sans inventer de signal.\n"
            "🕯 Commentaire aux clôtures 15 min utiles ; aucune Entry/SL/TP sans confirmation Pine.\n"
            "📍 Dès qu'une position est ouverte par ALIGN, je poursuis son suivi.\n"
            "⏹ Pour arrêter : le bouton sous mes messages."
        )
        translated_activation = ab.traduire(activation)
        self.assertIn("LIVE COMMENTATOR ACTIVATED", translated_activation)
        self.assertNotIn("Surveillance continue", translated_activation)
        self.assertNotIn("Commentaire aux clôtures", translated_activation)


if __name__ == "__main__":
    unittest.main()
