"""Règles de consentement Telegram : aucun push privé sans opt-in explicite."""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class TelegramOptIn(unittest.TestCase):
    def test_new_chat_receives_no_private_push_by_default(self):
        state = {"marches_par_chat": {"123": "GOLD"}}
        self.assertFalse(ab.bot_on(state, "123"))
        self.assertEqual(ab.destinataires_message(state, {"123"}, "🥇 GOLD — SIGNAL LONG"), [])

    def test_auto_follow_is_explicit_and_market_scoped(self):
        state = {"marches_par_chat": {"123": "GOLD"}, "auto": {"GOLD": ["123"]}}
        self.assertTrue(ab.bot_on(state, "123"))
        self.assertEqual(ab.destinataires_message(state, {"123"}, "🥇 GOLD — SIGNAL SHORT"), ["123"])
        self.assertEqual(ab.destinataires_message(state, {"123"}, "🟠 BTC — SIGNAL LONG"), [])

    def test_coach_live_is_explicit_and_market_scoped(self):
        state = {"coach_live": {"NASDAQ": {"123": {"expire": 9999999999}}}}
        self.assertTrue(ab.notifications_actives(state, "123", "NASDAQ"))
        self.assertFalse(ab.notifications_actives(state, "123", "GOLD"))
        self.assertEqual(ab.destinataires_message(state, {"123"}, "💠 NASDAQ — COACH"), ["123"])
        self.assertEqual(ab.destinataires_message(state, {"123"}, "🥇 GOLD — COACH"), [])

    def test_global_channel_still_receives_publication_without_private_push(self):
        state = {"canal": "-100", "marches_par_chat": {"123": "GOLD"}}
        self.assertEqual(ab.destinataires_message(state, {"123"}, "🥇 GOLD — SIGNAL"), ["-100"])

    def test_accepted_open_position_keeps_its_own_sl_tp_follow_up(self):
        state = {"bot_off": ["123"], "GOLD": {"trade": {"qui": {"123": {"e": 4000, "fini": False}}}}}
        self.assertFalse(ab.bot_on(state, "123"))
        self.assertTrue(ab.notifications_actives(state, "123", "GOLD"))
        self.assertEqual(ab.destinataires_message(state, {"123"}, "🥇 GOLD — TP1 TOUCHÉ"), ["123"])
        self.assertEqual(ab.destinataires_message(state, {"123"}, "🟠 BTC — TP1 TOUCHÉ"), [])

    def test_bot_on_requires_prior_market_selection(self):
        state = {}
        with patch.object(ab, "menu_marches") as menu, patch.object(ab, "_envoi_sur"):
            ab.regler_bot(state, "123", True)
        menu.assert_called_once_with(state, "123")
        self.assertNotIn("123", state.get("notifications_on", []))
        self.assertFalse(ab.bot_on(state, "123"))

    def test_explicit_bot_on_uses_only_validated_markets(self):
        state = {"marches_par_chat": {"123": ["GOLD", "NASDAQ"]}}
        with patch.object(ab, "_envoi_sur"):
            ab.regler_bot(state, "123", True)
        self.assertTrue(ab.bot_on(state, "123"))
        self.assertEqual(ab.marches_notifications(state, "123"), {"GOLD", "NASDAQ"})
        self.assertEqual(ab.destinataires_message(state, {"123"}, "🟠 BTC — SIGNAL"), [])

    def test_bot_off_cancels_future_subscriptions(self):
        state = {"marches_par_chat": {"123": "GOLD"}, "notifications_on": ["123"],
                 "auto": {"GOLD": ["123"]}, "coach_live": {"GOLD": {"123": {"expire": 9999999999}}}}
        with patch.object(ab, "_envoi_sur"):
            ab.regler_bot(state, "123", False)
        self.assertFalse(ab.bot_on(state, "123"))
        self.assertFalse(ab.notifications_actives(state, "123", "GOLD"))
        self.assertNotIn("123", state["auto"]["GOLD"])
        self.assertNotIn("123", state["coach_live"]["GOLD"])

    def test_unsubscribed_chat_does_not_receive_candle_follow_up(self):
        state = {"veille_cloture": {"GOLD": {"123": {"tf": "15m", "dernier_t": 1, "restants": 3}}}}
        r = {"b15": [{"t": 1}, {"t": 2}], "b1h": [], "b4h": [], "b5": []}
        with patch.object(ab, "_envoi_sur") as send:
            ab.notifier_clotures(state, "GOLD", r, {})
        send.assert_not_called()
        self.assertNotIn("123", state["veille_cloture"]["GOLD"])

    def test_gold_and_nasdaq_telegram_cards_show_clear_french_entry_sl_tp1_tp2(self):
        cases = (("GOLD", -1, 4000.0, 4010.0, 3985.0, 3965.0, "SHORT"),
                 ("NASDAQ", 1, 20000.0, 19980.0, 20030.0, 20070.0, "LONG"))
        for market, direction, entry, stop, tp1, tp2, side in cases:
            trade = {"d": direction, "e": entry, "sl": stop, "tp1": tp1, "tp2": tp2, "sl_ut": "5 min"}
            r = {"m1": [{"c": entry, "h": entry + 1, "l": entry - 1}], "macro_data": {}, "niveaux": []}
            with patch.object(ab, "niveaux_rs", return_value=(None, None)), \\
                 patch.object(ab, "pips_txt", return_value="10 points"), \\
                 patch.object(ab, "coach_fvg", return_value=[]), \\
                 patch.object(ab, "dxy_court", return_value="neutre"), \\
                 patch.object(ab, "news_prochaine_courte", return_value="aucune"), \\
                 patch.object(ab, "statut_sys", return_value="SYSTÈME OK"):
                text = ab.carte_coach(market, r, {}, "signal", tr=trade, etat={})
            self.assertIn(f"{market} - {side}", text)
            for label in ("🎯 Entrée :", "🛑 SL :", "💰 TP1 :", "🏁 TP2 :", "🤖 Agent Auto-Trade"):
                self.assertIn(label, text)
            self.assertIn("ENTRER", text)

    def test_no_telegram_fibonacci_push_function_remains(self):
        self.assertFalse(hasattr(ab, "fibo_zones"))


if __name__ == "__main__":
    unittest.main()
