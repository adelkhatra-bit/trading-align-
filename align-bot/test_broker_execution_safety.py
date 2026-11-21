"""Safety regression: ALIGN must never send real broker orders."""
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
WORKFLOW = REPO / ".github" / "workflows" / "align-bot.yml"
SERVER = REPO / "server.js"
BROKER_ADAPTER = REPO / "trading" / "broker-adapter.js"
ENV_EXAMPLE = REPO / ".env.example"
STARTUP_FILES = (
    REPO / "START.bat",
    REPO / "START_COMPLETE.bat",
    REPO / "QUICK_START.bat",
)


class BrokerExecutionSafety(unittest.TestCase):
    def test_production_worker_forces_broker_execution_off(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        start = source.index("      - name: Analyse BTC + Gold et envoi Telegram")
        step = source[start:]
        self.assertIn('AUTO_TRADE: "0"', step)
        self.assertIn('TOPSTEP_REEL: "0"', step)
        self.assertNotIn("AUTO_TRADE: ${{ vars.AUTO_TRADE }}", step)
        self.assertNotIn("TOPSTEP_REEL: ${{ vars.TOPSTEP_REEL }}", step)

    def test_node_server_defaults_to_safe_paper_mode_and_rejects_live_toggle(self):
        source = SERVER.read_text(encoding="utf-8")
        self.assertIn("process.env.BROKER_MODE = 'paper';", source)
        self.assertIn("process.env.SAFE_MODE = '1';", source)
        self.assertIn("if (m !== 'paper')", source)
        self.assertIn("LIVE_BROKER_EXECUTION_DISABLED", source)
        self.assertIn("liveExecutionEnabled: false", source)

    def test_broker_adapter_rejects_live_environment_without_network_call(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js doit être disponible sur le runner ALIGN")
        script = r"""
let fetchCalled = false;
global.fetch = () => {
  fetchCalled = true;
  return Promise.reject(new Error('unexpected live broker request'));
};
process.env.BROKER_MODE = 'live';
const adapter = require(process.argv[1]);
adapter.placeOrder({symbol: 'BTCUSD', direction: 'BUY', quantity: 1})
  .then(() => {
    console.error('A live environment unexpectedly produced an order');
    process.exit(2);
  })
  .catch((error) => {
    if (!/live broker execution is disabled/i.test(error.message)) {
      console.error(error.message);
      process.exit(3);
    }
    if (fetchCalled) {
      console.error('The adapter attempted a network broker call');
      process.exit(4);
    }
    process.exit(0);
  });
"""
        result = subprocess.run(
            [node, "-e", script, str(BROKER_ADAPTER)],
            cwd=str(REPO),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_all_standard_windows_launchers_force_paper_and_safe_mode(self):
        for path in STARTUP_FILES:
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertIn("BROKER_MODE=paper", source)
                self.assertIn("SAFE_MODE=1", source)
                self.assertNotIn("BROKER_MODE=live", source)
                self.assertNotIn("SAFE_MODE=0", source)

    def test_env_example_is_paper_only(self):
        source = ENV_EXAMPLE.read_text(encoding="utf-8")
        self.assertIn("SAFE_MODE=1", source)
        self.assertIn("BROKER_MODE=paper", source)
        self.assertNotIn("BROKER_MODE=live", source)
        self.assertNotIn("BROKER_API_KEY=", source)
        self.assertNotIn("BROKER_API_SECRET=", source)


if __name__ == "__main__":
    unittest.main()
