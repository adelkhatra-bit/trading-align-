"""Tests de classification des sessions mémoire ALIGN autour des changements DST."""
import datetime
import unittest
from zoneinfo import ZoneInfo

import align_bot


def paris_ts(value):
    local = datetime.datetime.fromisoformat(value).replace(tzinfo=ZoneInfo("Europe/Paris"))
    return local.timestamp()


class SessionProfileDSTTests(unittest.TestCase):
    def test_before_new_york_open_during_us_dst_europe_standard(self):
        self.assertEqual(align_bot.session_de(paris_ts("2026-03-10T14:15:00")), "Londres")

    def test_after_new_york_open_during_us_dst_europe_standard(self):
        self.assertEqual(align_bot.session_de(paris_ts("2026-03-10T14:45:00")), "New York")

    def test_before_new_york_open_during_europe_dst(self):
        self.assertEqual(align_bot.session_de(paris_ts("2026-03-30T15:15:00")), "Londres")

    def test_after_new_york_open_during_europe_dst(self):
        self.assertEqual(align_bot.session_de(paris_ts("2026-03-30T15:45:00")), "New York")

    def test_london_open_uses_london_local_time(self):
        self.assertEqual(align_bot.session_de(paris_ts("2026-07-15T09:30:00")), "Londres")

    def test_weekend_is_not_mislabelled_as_london_or_new_york(self):
        self.assertEqual(align_bot.session_de(paris_ts("2026-07-18T12:00:00")), "Asie")


if __name__ == "__main__":
    unittest.main()
