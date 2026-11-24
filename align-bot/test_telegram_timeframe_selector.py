import json
import unittest
from unittest.mock import patch

import align_bot as ab


class TelegramTimeframeSelectorTests(unittest.TestCase):
    def snapshot(self, fresh=True):
        return {
            "available": True,
            "snapshots": {
                "M3": {"fresh": fresh, "direction": "BULLISH", "rsi": 61.5,
                       "price": 98250.5, "bar_time": 1795532341000},
                "W1": {"fresh": True, "direction": "BEARISH", "rsi": 42.0,
                       "price": 98100.0, "bar_time": 1795528800000},
            },
        }

    def test_keyboard_exposes_all_twelve_bridge_timeframes(self):
        keyboard = json.loads(ab.clavier_timeframes("BTC"))["inline_keyboard"]
        callbacks = [button["callback_data"] for row in keyboard for button in row
                     if button.get("callback_data", "").startswith("tfview:")]
        expected = [f"tfview:BTC:{tf}" for tf, _ in ab.TELEGRAM_TF_VIEWS]
        self.assertEqual(callbacks, expected)
        self.assertEqual(len(callbacks), 12)
        self.assertIn("resume:BTC", [b.get("callback_data") for row in keyboard for b in row])

    def test_selected_timeframe_reads_fresh_pine_snapshot_including_weekly(self):
        text = ab.texte_unite_timeframe("GOLD", "W1", {"tv_indicator_mtf": self.snapshot()})
        self.assertIn("1 semaine", text)
        self.assertIn("TradingView", text)
        self.assertIn("BAISSIER", text)
        self.assertIn("RSI : 42.0", text)
        self.assertIn("plan Entry / SL / TP reste", text)

    def test_stale_snapshot_is_fail_closed_without_local_fallback(self):
        r = {"dirs": [1] * 11, "rsis": [70] * 11,
             "tv_indicator_mtf": {"available": True,
                                  "snapshots": {"M3": {"fresh": False, "direction": "BULLISH", "rsi": 70}}}}
        text = ab.texte_unite_timeframe("BTC", "M3", r)
        self.assertIn("périmé", text)
        self.assertNotIn("HAUSSIER", text)
        self.assertNotIn("RSI : 70", text)

    def test_unavailable_bridge_does_not_substitute_local_reading(self):
        r = {"dirs": [1] * 11, "rsis": [70] * 11,
             "tv_indicator_mtf": {"available": False}}
        text = ab.texte_unite_timeframe("BTC", "M5", r)
        self.assertIn("Bridge TradingView indisponible", text)
        self.assertNotIn("HAUSSIER", text)

    def test_english_timeframe_view_and_keyboard_do_not_mix_french_labels(self):
        text = ab.texte_unite_timeframe("BTC", "W1", {"tv_indicator_mtf": self.snapshot()}, anglais=True)
        self.assertIn("1 week", text)
        self.assertIn("BEARISH", text)
        self.assertIn("Last price", text)
        keyboard = json.loads(ab.clavier_timeframes("BTC", anglais=True))["inline_keyboard"]
        labels = [b["text"] for row in keyboard for b in row]
        self.assertIn("1 day", labels)
        self.assertIn("1 week", labels)
        self.assertIn("↩️ Back to analysis", labels)
        self.assertNotIn("1 jour", labels)
        self.assertNotIn("1 semaine", labels)

    def test_english_all_timeframes_summary_is_translated(self):
        text = ab.texte_timeframes("BTC", {"dirs": [1] * 11, "rsis": [60] * 11}, anglais=True)
        self.assertIn("ALL TIMEFRAMES", text)
        self.assertIn("BULLISH", text)
        self.assertIn("main trend", text)
        self.assertNotIn("TOUTES LES UNITÉS", text)
        self.assertNotIn("HAUSSIER", text)
    def test_tfview_callback_routes_market_and_timeframe_and_returns_selector(self):
        update = {"update_id": 99801, "callback_query": {
            "id": "tfview-btc-m3", "data": "tfview:BTC:M3",
            "message": {"chat": {"id": 101, "type": "private"}},
            "from": {"id": 101},
        }}
        r = {"tv_indicator_mtf": self.snapshot()}
        with patch.dict(ab.DERNIERS, {}, clear=True), \
             patch.object(ab, "autorise", return_value=True), \
             patch.object(ab, "analyse_marche", return_value=r), \
             patch.object(ab, "_envoi_sur") as send, \
             patch.object(ab, "telegram"):
            ab.traiter({}, set(), [update])
        self.assertIn("3 min", send.call_args.kwargs["text"])
        self.assertIn("HAUSSIER", send.call_args.kwargs["text"])
        keyboard = json.loads(send.call_args.kwargs["reply_markup"])["inline_keyboard"]
        callbacks = [b.get("callback_data") for row in keyboard for b in row]
        self.assertIn("tfview:BTC:W1", callbacks)

    def test_all_timeframes_callback_now_includes_individual_selector(self):
        update = {"update_id": 99802, "callback_query": {
            "id": "timeframes-gold", "data": "timeframes:GOLD",
            "message": {"chat": {"id": 102, "type": "private"}},
            "from": {"id": 102},
        }}
        r = {"dirs": [0] * 11, "rsis": [50] * 11, "tv_indicator_mtf": self.snapshot()}
        with patch.dict(ab.DERNIERS, {}, clear=True), \
             patch.object(ab, "autorise", return_value=True), \
             patch.object(ab, "analyse_marche", return_value=r), \
             patch.object(ab, "texte_timeframes", return_value="TOUTES LES UNITÉS"), \
             patch.object(ab, "_envoi_sur") as send, \
             patch.object(ab, "telegram"):
            ab.traiter({}, set(), [update])
        self.assertEqual(send.call_args.kwargs["text"], "TOUTES LES UNITÉS")
        keyboard = json.loads(send.call_args.kwargs["reply_markup"])["inline_keyboard"]
        callbacks = [b.get("callback_data") for row in keyboard for b in row]
        self.assertIn("tfview:GOLD:M15", callbacks)
        self.assertIn("tfview:GOLD:W1", callbacks)


if __name__ == "__main__":
    unittest.main()