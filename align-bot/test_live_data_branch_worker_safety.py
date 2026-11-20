"""Safety guard for the publication-branch copy of the ALIGN worker workflow."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / ".github" / "workflows" / "align-bot.yml").read_text(encoding="utf-8")


class LiveDataWorkerSafetyTests(unittest.TestCase):
    def test_worker_job_is_restricted_to_main_ref(self):
        worker = WORKFLOW.split("\n  signaux:", 1)[1].split("\n    runs-on:", 1)[0]
        self.assertIn("github.ref == 'refs/heads/main'", worker)

    def test_publication_branch_dispatch_cannot_cancel_a_production_worker(self):
        self.assertIn("cancel-in-progress: false", WORKFLOW)


if __name__ == "__main__":
    unittest.main()
