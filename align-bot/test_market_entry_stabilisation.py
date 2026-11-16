import datetime
import os
import sys
import unittest
import unittest.mock
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
        after = self.bars(reference, [1.1, 1.2, 1.0, 1.1, 1.0])
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
        r["b5"][-3:] = self.bars(event + 2 * 300, [3.0, 3.2, 3.5])
        reason = align_bot.pause_entree_marche("BTC", r, state, now)
        self.assertIn("réaction M5 encore instable", reason)

    def test_stabilisation_requires_six_pre_event_and_three_post_event_bars(self):
        event = datetime.datetime(2026, 11, 16, 10, 0, tzinfo=ZoneInfo("America/New_York")).timestamp()
        r = {"b5": self.bars(event, [1.0, 1.0, 1.0]), "atr5": 1.0}
        self.assertFalse(align_bot._stabilisation_m5_apres(r, event, event + 25 * 60))


    def test_agent_cancels_pending_entry_during_news_blackout(self):
        event = datetime.datetime(2026, 11, 16, 10, 0, tzinfo=ZoneInfo("America/New_York")).timestamp()
        now = event + 10 * 60
        state = {"cal": {"ev": [{"t": event, "titre": "CPI"}]}}
        r = {"m1": [{"t": now, "o": 100.0, "h": 101.0, "l": 99.0, "c": 100.0}],
             "r5": [50.0, 50.0], "confirme": 1, "t": now, "posD": 0.5, "posW": 0.5}
        cle = {"prep": True, "ordre": {"e": 100.0, "sl": 99.0}}
        patches = [
            unittest.mock.patch.dict(align_bot._ETAT_COURANT, {"etat": state}, clear=False),
            unittest.mock.patch.object(align_bot.time, "time", return_value=now),
            unittest.mock.patch.object(align_bot, "manipulation"),
            unittest.mock.patch.object(align_bot, "meche_suspecte"),
            unittest.mock.patch.object(align_bot, "niveaux_cles"),
            unittest.mock.patch.object(align_bot, "resistance_fvg"),
            unittest.mock.patch.object(align_bot, "suivre_apres_sl"),
            unittest.mock.patch.object(align_bot, "reprise_entree", return_value=None),
            unittest.mock.patch.object(align_bot, "entree_retest", return_value=None),
            unittest.mock.patch.object(align_bot, "radar_climax", return_value=None),
            unittest.mock.patch.object(align_bot, "retournement_marche", return_value=None),
        ]
        for p in patches:
            p.start()
        try:
            out = align_bot.agent("BTC", r, cle, "")
        finally:
            for p in reversed(patches):
                p.stop()
        self.assertNotIn("trade", cle)
        self.assertFalse(cle.get("prep"))
        self.assertNotIn("ordre", cle)
        self.assertTrue(any("ENTRÉES EN PAUSE" in str(x) for x in out))



if __name__ == "__main__":
    unittest.main()
