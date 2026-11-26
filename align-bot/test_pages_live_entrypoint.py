"""GitHub Pages root must lead to the canonical live dashboard without changing its UI."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PagesLiveEntrypointTests(unittest.TestCase):
    def test_pages_root_redirects_to_live_dashboard(self):
        page = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn('http-equiv="refresh"', page)
        self.assertIn('content="0;url=./live/"', page)
        self.assertIn('href="./live/"', page)

    def test_coach_dialogue_is_triggered_by_market_state_changes_not_random_timer_phrases(self):
        page = (ROOT / "docs" / "live" / "index.html").read_text(encoding="utf-8")
        start = page.index("function echange() {")
        end = page.index("\\nfunction charger()", start)
        exchange = page[start:end]
        self.assertIn("dernierEtatCoachParMarche", page)
        self.assertIn("var signature = [m.etat, m.biais, m.ut, m.seuil, m.profil].join", exchange)
        self.assertIn("construireCommentaireEtat(m)", exchange)
        self.assertNotIn("Math.random()", exchange)
        self.assertIn("age > 600", exchange)

    def test_coach_market_commentary_does_not_invent_prices_or_levels(self):
        page = (ROOT / "docs" / "live" / "index.html").read_text(encoding="utf-8")
        start = page.index("function construireCommentaireEtat(m) {")
        end = page.index("\\nfunction echange()", start)
        builder = page[start:end]
        self.assertIn("m.etat", builder)
        self.assertIn("m.biais", builder)
        self.assertIn("m.ut", builder)
        self.assertIn("m.seuil", builder)
        self.assertNotIn("tv_price", builder)
        self.assertNotIn("entry", builder.lower().replace("entrée", ""))

    def test_live_dashboard_target_exists(self):
        self.assertTrue((ROOT / "docs" / "live" / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
