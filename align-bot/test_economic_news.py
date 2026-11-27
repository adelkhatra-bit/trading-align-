import datetime as dt
import os
import sys
import unittest
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import economic_news as news


class EconomicNewsNormalizationTest(unittest.TestCase):
    def setUp(self):
        self.now = int(dt.datetime(2026, 11, 27, 9, 0, tzinfo=ZoneInfo("Europe/Paris")).timestamp())

    def test_usd_low_impact_trade_and_wholesale_inventory_are_kept_for_market_watch(self):
        raw = [
            {
                "title": "Goods Trade Balance",
                "country": "USD",
                "date": "2026-11-27T08:30:00-05:00",
                "impact": "Low",
                "forecast": "-135.9B",
                "previous": "-134.9B",
            },
            {
                "title": "Prelim Wholesale Inventories m/m",
                "country": "USD",
                "date": "2026-11-27T08:30:00-05:00",
                "impact": "Low",
                "forecast": "0.5%",
                "previous": "0.6%",
            },
            {
                "title": "Minor USD housing index",
                "country": "USD",
                "date": "2026-11-27T09:00:00-05:00",
                "impact": "Low",
            },
        ]
        important, daily = news.normaliser_evenements(raw, self.now)
        titles = [event["titre"] for event in important]
        self.assertIn("Goods Trade Balance", titles)
        self.assertIn("Prelim Wholesale Inventories m/m", titles)
        self.assertNotIn("Minor USD housing index", titles)
        self.assertEqual(len(daily), 3)

    def test_event_time_is_converted_from_explicit_offset_to_paris(self):
        event = news.normaliser_evenement({
            "title": "Goods Trade Balance",
            "country": "USD",
            "date": "2026-11-27T08:30:00-05:00",
            "impact": "Low",
        }, self.now)
        self.assertEqual(event["event_at_paris"], "2026-11-27T14:30:00+01:00")
        self.assertEqual(event["currency"], "USD")
        self.assertEqual(event["importance"], "Low")
        self.assertEqual(event["official_source_name"], "U.S. Census Bureau")

    def test_naive_event_time_is_rejected_instead_of_assuming_runner_timezone(self):
        event = news.normaliser_evenement({
            "title": "CPI",
            "country": "USD",
            "date": "2026-11-27T08:30:00",
            "impact": "High",
        }, self.now)
        self.assertIsNone(event)

    def test_publication_time_is_not_confused_with_event_time(self):
        event = news.normaliser_evenement({
            "title": "CPI",
            "country": "USD",
            "date": "2026-11-27T08:30:00-05:00",
            "publishedAt": "2026-11-27T08:31:12Z",
            "impact": "High",
        }, self.now)
        self.assertNotEqual(event["published_at"], event["t"])
        self.assertIsNotNone(event["published_at_paris"])

    def test_event_identity_is_stable_across_refreshes(self):
        raw = {
            "title": "Goods Trade Balance",
            "country": "USD",
            "date": "2026-11-27T08:30:00-05:00",
            "impact": "Low",
        }
        first = news.normaliser_evenement(raw, self.now)
        second = news.normaliser_evenement(raw, self.now + 300)
        self.assertEqual(first["id"], second["id"])

    def test_refresh_interval_tightens_before_and_after_event(self):
        event = {"t": self.now + 90 * 60}
        self.assertEqual(news.intervalle_rafraichissement([event], self.now), 300)
        self.assertEqual(news.intervalle_rafraichissement([{"t": self.now + 4 * 3600}], self.now), 900)
        self.assertEqual(news.intervalle_rafraichissement([{"t": self.now + 10 * 3600}], self.now), 3600)

    def test_facts_report_does_not_claim_missing_actual_value(self):
        event = news.normaliser_evenement({
            "title": "Goods Trade Balance",
            "country": "USD",
            "date": "2026-11-27T08:30:00-05:00",
            "impact": "Low",
            "forecast": "-135.9B",
            "previous": "-134.9B",
        }, self.now)
        report = news.facts_line(event)
        self.assertIn("Valeur publiée: non reçue", report)
        self.assertIn("aucun chiffre n'est inventé", report)
        self.assertIn("U.S. Census Bureau", report)
        self.assertIn("census.gov", report)

    def test_actual_value_is_labelled_as_aggregator_data_not_official_data(self):
        event = news.normaliser_evenement({
            "title": "Core CPI m/m",
            "country": "USD",
            "date": "2026-11-27T08:30:00-05:00",
            "impact": "High",
            "actual": "0.2%",
            "forecast": "0.3%",
            "previous": "0.3%",
        }, self.now)
        report = news.facts_line(event)
        self.assertIn("Valeur reçue du calendrier agrégé: 0.2%", report)
        self.assertIn("Source de la valeur: Forex Factory", report)
        self.assertIn("U.S. Bureau of Labor Statistics", report)


if __name__ == "__main__":
    unittest.main()
