"""Safety regression: production worker must never send real broker orders."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
WORKFLOW = ROOT.parent / ".github" / "workflows" / "align-bot.yml"


class BrokerExecutionSafety(unittest.TestCase):
    def test_production_worker_forces_broker_execution_off(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        start = source.index("      - name: Analyse BTC + Gold + NASDAQ et envoi Telegram")
        step = source[start:]
        self.assertIn('AUTO_TRADE: "0"', step)
        self.assertIn('TOPSTEP_REEL: "0"', step)
        self.assertNotIn("AUTO_TRADE: ${{ vars.AUTO_TRADE }}", step)
        self.assertNotIn("TOPSTEP_REEL: ${{ vars.TOPSTEP_REEL }}", step)


if __name__ == "__main__":
    unittest.main()
