import datetime
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import align_bot as ab


class EconomicCalendarFailureGuardTest(unittest.TestCase):
    def test_failed_fetch_uses_retry_backoff_without_marking_calendar_fresh(self):
        now = 1_700_000_000
        state = {}

        with mock.patch.object(ab, "http_json", side_effect=RuntimeError("offline")) as fetch:
            self.assertEqual(ab.calendrier(state, now), [])
            self.assertEqual(ab.calendrier(state, now + 30), [])

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(state["cal"]["retry_after"], now + 300)
        self.assertFalse(ab.calendrier_connu(state, now + 30))

    def test_calendar_retries_after_backoff_and_clears_error_on_success(self):
        now = 1_700_000_000
        state = {}

        with mock.patch.object(ab, "http_json", side_effect=[RuntimeError("offline"), []]) as fetch:
            ab.calendrier(state, now)
            self.assertEqual(ab.calendrier(state, now + 301), [])

        self.assertEqual(fetch.call_count, 2)
        self.assertTrue(ab.calendrier_connu(state, now + 301))
        self.assertNotIn("retry_after", state["cal"])
        self.assertNotIn("erreur", state["cal"])

    def test_unknown_calendar_warns_instead_of_claiming_no_news_or_replaying_stale_events(self):
        now = datetime.datetime(2026, 11, 26, 8, 0, tzinfo=ab.PARIS).timestamp()
        stale_event = {
            "titre": "Old FOMC announcement",
            "t": now + 300,
            "prev": "",
            "avant": "",
        }
        state = {"cal": {"t": now - 7 * 3600, "ev": [stale_event]}}

        with mock.patch.object(ab, "calendrier", return_value=[stale_event]):
            messages = ab.annonces_et_sessions(state, now, {})

        joined = "\\n".join(messages)
        self.assertIn("CALENDRIER ÉCONOMIQUE INDISPONIBLE", joined)
        self.assertNotIn("Aucune annonce majeure US aujourd'hui", joined)
        self.assertNotIn("Old FOMC announcement", joined)

    def test_fresh_empty_calendar_can_still_report_no_major_news(self):
        now = datetime.datetime(2026, 11, 26, 8, 0, tzinfo=ab.PARIS).timestamp()
        state = {"cal": {"t": now - 600, "ev": []}}

        with mock.patch.object(ab, "calendrier", return_value=[]):
            messages = ab.annonces_et_sessions(state, now, {})

        self.assertIn("📅 Aucune annonce majeure US aujourd'hui.", messages)


if __name__ == "__main__":
    unittest.main()
