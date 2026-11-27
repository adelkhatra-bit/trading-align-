import datetime as dt
import os
import sys
import unittest
from unittest import mock
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import economic_news as news
import align_bot as ab


class EconomicNewsNormalizationTest(unittest.TestCase):
    def setUp(self):
        self.now = int(dt.datetime(2026, 11, 27, 9, 0, tzinfo=ZoneInfo("Europe/Paris")).timestamp())

    def test_usd_low_impact_trade_and_wholesale_inventory_are_kept_for_market_watch(self):
        raw = [
            {"title": "Goods Trade Balance", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "Low", "forecast": "-135.9B", "previous": "-134.9B"},
            {"title": "Prelim Wholesale Inventories m/m", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "Low", "forecast": "0.5%", "previous": "0.6%"},
            {"title": "Minor USD housing index", "country": "USD", "date": "2026-11-27T09:00:00-05:00", "impact": "Low"},
        ]
        blocking, watch, daily = news.normaliser_evenements(raw, self.now)
        blocking_titles = [event["titre"] for event in blocking]
        watch_titles = [event["titre"] for event in watch]
        self.assertNotIn("Goods Trade Balance", blocking_titles)
        self.assertIn("Goods Trade Balance", watch_titles)
        self.assertIn("Prelim Wholesale Inventories m/m", watch_titles)
        self.assertNotIn("Minor USD housing index", watch_titles)
        self.assertEqual(len(daily), 3)

    def test_event_time_is_converted_from_explicit_offset_to_paris(self):
        event = news.normaliser_evenement({"title": "Goods Trade Balance", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "Low"}, self.now)
        self.assertEqual(event["event_at_paris"], "2026-11-27T14:30:00+01:00")
        self.assertEqual(event["currency"], "USD")
        self.assertEqual(event["importance"], "Low")
        self.assertEqual(event["official_source_name"], "U.S. Census Bureau")

    def test_official_reference_is_selected_by_release_type(self):
        claims = news.normaliser_evenement({"title": "Unemployment Claims", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "Low"}, self.now)
        payrolls = news.normaliser_evenement({"title": "Employment Situation", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "High"}, self.now)
        self.assertEqual(claims["official_source_name"], "U.S. Department of Labor — Weekly Unemployment Claims")
        self.assertEqual(payrolls["official_source_name"], "U.S. Bureau of Labor Statistics — Employment Situation")

    def test_naive_event_time_is_rejected_instead_of_assuming_runner_timezone(self):
        event = news.normaliser_evenement({"title": "CPI", "country": "USD", "date": "2026-11-27T08:30:00", "impact": "High"}, self.now)
        self.assertIsNone(event)

    def test_publication_time_is_not_confused_with_event_time(self):
        event = news.normaliser_evenement({"title": "CPI", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "publishedAt": "2026-11-27T08:31:12Z", "impact": "High"}, self.now)
        self.assertNotEqual(event["published_at"], event["t"])
        self.assertIsNotNone(event["published_at_paris"])

    def test_event_identity_is_stable_across_refreshes(self):
        raw = {"title": "Goods Trade Balance", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "Low"}
        first = news.normaliser_evenement(raw, self.now)
        second = news.normaliser_evenement(raw, self.now + 300)
        self.assertEqual(first["id"], second["id"])

    def test_refresh_interval_tightens_before_and_after_event(self):
        self.assertEqual(news.intervalle_rafraichissement([{"t": self.now + 90 * 60}], self.now), 300)
        self.assertEqual(news.intervalle_rafraichissement([{"t": self.now + 4 * 3600}], self.now), 900)
        self.assertEqual(news.intervalle_rafraichissement([{"t": self.now + 10 * 3600}], self.now), 3600)

    def test_facts_report_does_not_claim_missing_actual_value(self):
        event = news.normaliser_evenement({"title": "Goods Trade Balance", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "Low", "forecast": "-135.9B", "previous": "-134.9B"}, self.now)
        report = news.facts_line(event)
        self.assertIn("Valeur publiée: non reçue", report)
        self.assertIn("aucun chiffre n'est inventé", report)
        self.assertIn("U.S. Census Bureau", report)
        self.assertIn("census.gov", report)

    def test_zero_is_preserved_as_a_real_published_value(self):
        event = news.normaliser_evenement({"title": "Retail Sales", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "Low", "actual": 0, "forecast": 0, "previous": 0}, self.now)
        self.assertEqual(event["actual"], "0")
        self.assertEqual(event["forecast"], "0")
        self.assertEqual(event["previous"], "0")

    def test_actual_value_is_labelled_as_aggregator_data_not_official_data(self):
        event = news.normaliser_evenement({"title": "Core CPI m/m", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "High", "actual": "0.2%", "forecast": "0.3%", "previous": "0.3%"}, self.now)
        report = news.facts_line(event)
        self.assertIn("Valeur reçue du calendrier agrégé (non vérifiée directement auprès de l’organisme): 0.2%", report)
        self.assertIn("Source de la valeur: Forex Factory", report)
        self.assertIn("U.S. Bureau of Labor Statistics", report)


    def test_calendar_updated_at_is_not_mislabelled_as_publication_time(self):
        raw = {
            "title": "Core CPI m/m",
            "country": "USD",
            "date": "2026-11-27T08:30:00-05:00",
            "impact": "High",
            "updated_at": "2026-11-27T08:31:00-05:00",
        }
        event = news.normaliser_evenement(raw, self.now)
        self.assertIsNone(event["published_at"])
        self.assertIsNone(event["published_at_paris"])
        self.assertIsNone(event["published_at_source"])
        self.assertEqual(event["source_updated_at"], news._timestamp(raw["updated_at"]))
        self.assertIsNotNone(event["source_updated_at_paris"])


class EconomicNewsBotIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.now = int(dt.datetime(2026, 11, 27, 9, 0, tzinfo=ZoneInfo("Europe/Paris")).timestamp())
        self.schedule = [
            {"title": "Goods Trade Balance", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "Low", "forecast": "-135.9B", "previous": "-134.9B"},
            {"title": "Prelim Wholesale Inventories m/m", "country": "USD", "date": "2026-11-27T08:30:00-05:00", "impact": "Low", "forecast": "0.5%", "previous": "0.6%"},
        ]

    def _patch_market_hours(self):
        return (
            mock.patch.object(ab, "minutes_avant_fermeture_gold", return_value=100),
            mock.patch.object(ab, "horaires_gold", return_value=(self.now + 100 * 60, self.now + 200 * 60, self.now + 300 * 60)),
        )

    def test_bot_calendar_keeps_low_impact_officially_relevant_usd_events(self):
        state = {}
        with mock.patch.object(ab, "http_json", return_value=self.schedule):
            events = ab.calendrier(state, self.now)
        titles = [event["titre"] for event in events]
        watch_titles = [event["titre"] for event in state["cal"]["veille"]]
        self.assertEqual(titles, [])
        self.assertIn("Goods Trade Balance", watch_titles)
        self.assertIn("Prelim Wholesale Inventories m/m", watch_titles)
        self.assertTrue(ab.calendrier_connu(state, self.now))
        self.assertEqual(state["cal"]["source_url"], news.CALENDAR_URL)
        self.assertEqual(state["cal"]["schema"], 3)

    def test_low_impact_watch_does_not_trigger_the_automatic_entry_pause(self):
        low = news.normaliser_evenement({"title": "Goods Trade Balance", "country": "USD", "date": dt.datetime.fromtimestamp(self.now, dt.timezone.utc).isoformat(), "impact": "Low"}, self.now)
        high = news.normaliser_evenement({"title": "CPI", "country": "USD", "date": dt.datetime.fromtimestamp(self.now, dt.timezone.utc).isoformat(), "impact": "High"}, self.now)
        state_low = {"cal": {"t": self.now, "ev": [], "veille": [low]}}
        state_high = {"cal": {"t": self.now, "ev": [high], "veille": []}}
        self.assertFalse(ab.annonce_proche(state_low, self.now))
        self.assertTrue(ab.annonce_proche(state_high, self.now))

    def test_news_summary_includes_relevant_low_impact_watch_events(self):
        low = news.normaliser_evenement({
            "title": "Goods Trade Balance", "country": "USD",
            "date": dt.datetime.fromtimestamp(self.now + 60 * 60, dt.timezone.utc).isoformat(),
            "impact": "Low",
        }, self.now)
        state = {"cal": {"t": self.now, "ev": [], "veille": [low]}}
        with mock.patch.object(ab.time, "time", return_value=self.now):
            summary = ab.news_txt(state)
        self.assertIn("Goods Trade Balance", summary)
        self.assertIn("impact Low", summary)
        self.assertNotIn("Plus aucune annonce", summary)

    def test_failed_refresh_after_success_marks_calendar_unknown(self):
        state = {"cal": {"schema": 3, "t": self.now - 301, "ev": [{"t": self.now + 3600, "titre": "CPI"}], "veille": []}}
        with mock.patch.object(ab, "http_json", side_effect=RuntimeError("offline")):
            ab.calendrier(state, self.now)
        self.assertFalse(ab.calendrier_connu(state, self.now))
        self.assertEqual(state["cal"]["erreur"]["type"], "RuntimeError")

    def test_watch_tier_also_drives_five_minute_refresh_near_release(self):
        state = {"cal": {"schema": 3, "t": self.now - 301, "ev": [], "veille": [{"t": self.now + 90 * 60, "titre": "Goods Trade Balance"}]}}
        with mock.patch.object(ab, "http_json", return_value=[] ) as fetch:
            ab.calendrier(state, self.now)
        fetch.assert_called_once()
        self.assertEqual(state["cal"]["t"], self.now)

    def test_unknown_calendar_never_claims_there_are_no_announcements(self):
        hours_a, hours_b = self._patch_market_hours()
        with mock.patch.object(ab, "calendrier", return_value=[]), hours_a, hours_b:
            messages = ab.annonces_et_sessions({}, self.now, {})
        joined = "\n".join(messages)
        self.assertIn("CALENDRIER ÉCONOMIQUE INDISPONIBLE", joined)
        self.assertNotIn("Aucune annonce majeure US aujourd'hui", joined)

    def test_post_event_report_separates_published_facts_from_price_reaction(self):
        event = news.normaliser_evenement({"title": "Goods Trade Balance", "country": "USD", "date": dt.datetime.fromtimestamp(self.now - 7 * 60, dt.timezone.utc).isoformat(), "impact": "Low", "forecast": "-135.9B", "previous": "-134.9B"}, self.now)
        state = {"cal": {"t": self.now, "ev": [], "veille": [event]}}
        bars = [{"t": event["t"] + 60, "o": 100.0, "h": 102.0, "l": 99.0, "c": 101.5}]
        hours_a, hours_b = self._patch_market_hours()
        with mock.patch.object(ab, "calendrier", return_value=[]), hours_a, hours_b, mock.patch.object(ab, "ia", return_value="Mouvement observé; confirmation M15 attendue."):
            messages = ab.annonces_et_sessions(state, self.now, {"BTC": {"m1": bars}})
        report = next(message for message in messages if "COMPTE RENDU APRÈS NEWS" in message)
        self.assertIn("Valeur publiée: non reçue", report)
        self.assertIn("Réaction de prix observée (distincte des faits publiés)", report)
        self.assertIn("U.S. Census Bureau", report)
        self.assertIn("census.gov", report)

    def test_late_actual_value_generates_one_update_without_repeating_reaction_report(self):
        base = {"title": "Goods Trade Balance", "country": "USD", "date": dt.datetime.fromtimestamp(self.now - 10 * 60, dt.timezone.utc).isoformat(), "impact": "Low", "forecast": "-135.9B", "previous": "-134.9B"}
        first = news.normaliser_evenement(base, self.now)
        state = {"cal": {"t": self.now, "ev": [], "veille": [first]}}
        hours_a, hours_b = self._patch_market_hours()
        with mock.patch.object(ab, "calendrier", return_value=[]), hours_a, hours_b:
            ab.annonces_et_sessions(state, self.now, {})
        updated = news.normaliser_evenement(dict(base, actual="-137.2B"), self.now + 300)
        state["cal"]["veille"] = [updated]
        hours_a, hours_b = self._patch_market_hours()
        with mock.patch.object(ab, "calendrier", return_value=[]), hours_a, hours_b:
            messages = ab.annonces_et_sessions(state, self.now + 300, {})
        updates = [message for message in messages if "MISE À JOUR — VALEUR REÇUE" in message]
        self.assertEqual(len(updates), 1)
        self.assertIn("-137.2B", updates[0])
        hours_a, hours_b = self._patch_market_hours()
        with mock.patch.object(ab, "calendrier", return_value=[]), hours_a, hours_b:
            again = ab.annonces_et_sessions(state, self.now + 301, {})
        self.assertFalse(any("MISE À JOUR — VALEUR REÇUE" in message for message in again))


if __name__ == "__main__":
    unittest.main()
