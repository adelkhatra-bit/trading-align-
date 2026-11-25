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

    def test_live_dashboard_target_exists(self):
        self.assertTrue((ROOT / "docs" / "live" / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
