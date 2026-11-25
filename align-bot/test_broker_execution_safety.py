"""Safety regression: ALIGN must never send real broker orders."""
from pathlib import Path
import os
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
WORKFLOW = REPO / ".github" / "workflows" / "align-bot.yml"


class BrokerExecutionSafety(unittest.TestCase):
    def test_production_worker_forces_broker_execution_off(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        start = source.index("      - name: Analyse BTC + Gold et envoi Telegram")
        step = source[start:]
        self.assertIn('AUTO_TRADE: "0"', step)
        self.assertIn('TOPSTEP_REEL: "0"', step)
        self.assertNotIn("AUTO_TRADE: ${{ vars.AUTO_TRADE }}", step)
        self.assertNotIn("TOPSTEP_REEL: ${{ vars.TOPSTEP_REEL }}", step)

    def test_environment_switches_cannot_enable_topstep_or_metaapi_orders(self):
        script = r"""
import os, sys
os.environ["TOPSTEP_REEL"] = "1"
os.environ["AUTO_TRADE"] = "1"
sys.path.insert(0, sys.argv[1])
import topstep_trade, auto_trade
assert topstep_trade.REEL is False, "TOPSTEP_REEL must never enable live orders"
assert auto_trade.REEL is False, "AUTO_TRADE must never enable live orders"
"""
        result = subprocess.run(
            [sys.executable, "-c", script, str(REPO / "align-bot")],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            env={**os.environ, "TOPSTEP_REEL": "1", "AUTO_TRADE": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_topstep_messages_never_claim_automatic_real_position_closure(self):
        source = (REPO / "align-bot" / "topstep_trade.py").read_text(encoding="utf-8")
        self.assertIn("Ferme MANUELLEMENT tes positions", source)
        self.assertIn("aucun ordre réel n'est envoyé", source)
        self.assertNotIn("Le bot ALIGN coupe les siennes", source)
        self.assertNotIn("LE BOT COUPE SES POSITIONS", source)




if __name__ == "__main__":
    unittest.main()
