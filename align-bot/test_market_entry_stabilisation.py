import datetime
import os
import sys
import unittest
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot


class MarketEntryStabilisationTests(unittest.TestCase):
    def bars(self, reference, ranges):
        out = []
        for i, amplitude in enumerate(ranges):
            ts = int(reference) + i * 300
            out.append({"t": ts, "o": 100.0, "h": 100.0 + amplitude, "l": 100.0,
                        "c": 100.0 + amplitude / 2, "v": 100.0})
        return out

    def stable_market(self, reference):
        before = self.bars(reference - 12 * 300, [1.0] * 12)
        after = self.bars(reference, [1.1, 1.2, 1.0])
        return {"b5": before + after, "atr5": 1.0, "atr": 1.0}

    def test_gold_reopen_has_a_minimum_wait_before_any_new_entry(self):
        now = datetime.datetime(2026, 11, 16, 17, 5, tzinfo=ZoneInfo("America/Chicago")).timestamp()
        reason = align_bot.pause_entree_marche("GOLD", {"b5": []}, {}, now)
        self.assertIn("réouverture CME", reason)
        self.assertIn("15 min", reason)

    def test_nasdaq_cash_open_has_a_minimum_wait_before_any_new_entry(self):
        now = datetime.datetime(2026, 11, 16, 9, 35, tzinfo=ZoneInfo("America/New_York")).timestamp()
        reason = align_bot.pause_entree_marche("NASDAQ", {"b5": []}, {}, now)
        self.assertIn("ouverture de New York", reason)
        self.assertIn("20 min", reason)

    def test_btc_is_not_blocked_by_gold_or_nasdaq_session_open(self):
        now = datetime.datetime(2026, 11, 16, 9, 35, tzinfo=ZoneInfo("America/New_York")).timestamp()
        self.assertIsNone(align_bot.pause_entree_marche("BTC", {"b5": []}, {}, now))

    def test_high_impact_news_blocks_entries_during_initial_reaction(self):
        event = datetime.datetime(2026, 11, 16, 10, 0, tzinfo=ZoneInfo("America/New_York")).timestamp()
        now = event + 10 * 60
        state = {"cal": {"ev": [{"t": event, "titre": "CPI"}]}}
        reason = align_bot.pause_entree_marche("BTC", {"b5": []}, state, now)
        self.assertIn("actualité économique", reason)

    def test_after_news_waits_for_three_stable_closed_m5_candles(self):
        event = datetime.datetime(2026, 11, 16, 10, 0, tzinfo=ZoneInfo("America/New_York")).timestamp()
        now = event + 25 * 60
        state = {"cal": {"ev": [{"t": event, "titre": "CPI"}]}}
        r = self.stable_market(event)
        self.assertIsNone(align_bot.pause_entree_marche("BTC", r, state, now))

    def test_after_news_volatile_m5_candles_keep_entry_blocked(self):
        event = datetime.datetime(2026, 11, 16, 10, 0, tzinfo=ZoneInfo("America/New_York")).timestamp()
        now = event + 25 * 60
        state = {"cal": {"ev": [{"t": event, "titre": "CPI"}]}}
        r = self.stable_market(event)
        r["b5"][-3:] = self.bars(event + 12 * 300, [3.0, 3.2, 3.5])
        reason = align_bot.pause_entree_marche("BTC", r, state, now)
        self.assertIn("réaction M5 encore instable", reason)

    def test_stabilisation_requires_six_pre_event_and_three_post_event_bars(self):
        event = datetime.datetime(2026, 11, 16, 10, 0, tzinfo=ZoneInfo("America/New_York")).timestamp()
        r = {"b5": self.bars(event, [1.0, 1.0, 1.0]), "atr5": 1.0}
        self.assertFalse(align_bot._stabilisation_m5_apres(r, event))


if __name__ == "__main__":
    unittest.main()
