import sys
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import align_bot


class BreakEvenStopLevelReportingTest(unittest.TestCase):
    def test_subscriber_coach_message_reports_the_actual_be_stop(self):
        now = time.time()
        position = {
            "e": 100.0,
            "sl": 95.0,
            "sl_conseil": 95.0,
            "tp1": 110.0,
        }
        trade = {"d": 1, "tp1": 110.0, "qui": {"test-user": position}}
        market_data = {
            "atr": 2.0,
            "m1": [{"t": now, "o": 107.0, "h": 108.0, "l": 106.0, "c": 107.0}],
            "b15": [{"t": now - 900, "c": 103.0}],
            "niveaux": [],
        }
        messages = []

        with mock.patch.object(
            align_bot,
            "_telegram_envoyer_commentaire_coach_prive",
            side_effect=lambda *args, **kwargs: messages.append(args[3]),
        ):
            align_bot.gerer_stop({}, "BTC", market_data, trade, "test-user")

        expected_stop = align_bot.px(position["sl_conseil"])
        expected_entry = align_bot.px(position["e"])
        self.assertAlmostEqual(position["sl_conseil"], 100.1)
        self.assertEqual(len(messages), 1)
        self.assertIn(f"Nouveau SL : {expected_stop}", messages[0])
        self.assertIn(f"entrée {expected_entry}", messages[0])
        self.assertNotIn(f"BE ≈ {expected_entry}", messages[0])

    def test_global_trade_be_message_reports_the_actual_be_stop(self):
        now = int(time.time())
        trade = {
            "d": 1,
            "e": 100.0,
            "sl": 95.0,
            "tp1": 110.0,
            "tp2": 115.0,
            "statut": "entree",
            "cree": now - 900,
            "encore": 0,
            "be_dit": False,
        }
        state = {"trade": trade}
        market_data = {
            "m1": [{"t": now, "o": 107.0, "h": 108.0, "l": 106.0, "c": 107.0}],
            "r5": [50.0, 50.0],
            "confirme": 1,
            "t": now,
            "posD": 0.5,
            "posW": 0.5,
            "dirs": [1] * 11,
            "atr": 2.0,
            "b15": [{"t": now - 900, "c": 103.0}],
            "require_tv_bridge": False,
        }

        with mock.patch.object(align_bot, "mode_sans_signal", return_value=False), \
             mock.patch.object(align_bot, "manipulation", return_value=None), \
             mock.patch.object(align_bot, "meche_suspecte", return_value=None), \
             mock.patch.object(align_bot, "niveaux_cles", return_value=None), \
             mock.patch.object(align_bot, "resistance_fvg", return_value=None), \
             mock.patch.object(align_bot, "suivre_apres_sl", return_value=None), \
             mock.patch.object(align_bot, "radar_climax", return_value=None), \
             mock.patch.object(align_bot, "retournement_marche", return_value=None), \
             mock.patch.object(align_bot, "alerte_retournement", return_value=None), \
             mock.patch.object(align_bot, "frole_tp", return_value=None), \
             mock.patch.object(align_bot, "retour_entree", return_value=None), \
             mock.patch.object(align_bot, "approche_tp", return_value=None), \
             mock.patch.object(
                 align_bot,
                 "carte_suivi",
                 side_effect=lambda market, title, lines, *args, **kwargs: "\n".join([title] + lines),
             ):
            messages = align_bot.agent("BTC", market_data, state, "")

        expected_stop = align_bot.px(trade["sl"])
        expected_entry = align_bot.px(trade["e"])
        text = "\n".join(str(message) for message in messages)
        self.assertAlmostEqual(trade["sl"], 100.1)
        self.assertIn(f"SL sécurisé : {expected_stop}", text)
        self.assertIn(f"entrée {expected_entry}", text)
        self.assertNotIn(f"SL → BE : {expected_entry}", text)


if __name__ == "__main__":
    unittest.main()
