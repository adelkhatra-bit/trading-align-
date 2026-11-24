from pathlib import Path
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "align-fast-healthcheck.yml"


class AlignFastHealthcheckWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        lines = cls.source.splitlines()
        marker = "          python3 - <<'PY'"
        start = lines.index(marker) + 1
        end = lines.index("          PY", start)
        cls.verifier = textwrap.dedent("\n".join(lines[start:end]))

    def test_embedded_bridge_verifier_is_valid_python(self):
        compile(self.verifier, str(WORKFLOW) + ":bridge-verifier", "exec")

    def test_healthcheck_reuses_the_bot_bridge_route_and_full_mtf_contract(self):
        self.assertIn("align_tv_bridge.py", self.source)
        self.assertIn("align_tv_mailbox_feeder.py", self.source)
        self.assertIn("127.0.0.1:4100", self.source)
        self.assertIn("ALIGN_TV_API_URL_SECRET", self.source)
        self.assertIn("Override bridge externe détecté", self.source)
        self.assertIn("CLOUDFLARE_API_TOKEN", self.source)
        self.assertIn("from align_tv_bridge import REQUIRED_TIMEFRAMES", self.verifier)
        self.assertIn("for tf in REQUIRED_TIMEFRAMES", self.verifier)
        self.assertIn("align_bot.symboles_bridge_obligatoires(time.time())", self.verifier)
        self.assertIn("missing_or_stale", self.verifier)

    def test_healthcheck_does_not_start_telegram_polling_or_send_test_messages(self):
        self.assertNotIn('api("getUpdates")', self.source)
        self.assertNotIn('api("sendMessage")', self.source)
        self.assertIn("aucun getUpdates ni message envoyé", self.source)


if __name__ == "__main__":
    unittest.main()
