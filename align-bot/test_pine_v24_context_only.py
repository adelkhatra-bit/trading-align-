"""The legacy v24 chart is context-only; v25 owns execution levels and bridge output."""
from pathlib import Path
import unittest


PINE = Path(__file__).resolve().parent / "pine" / "ALIGN_MTF_PRO_v24.pine"


class PineV24ContextOnlyContract(unittest.TestCase):
    def test_v24_keeps_dashboard_context_without_publishing_a_second_execution_plan(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn("voirPlan = false", source)
        self.assertIn('ligne = "📊 CONTEXTE MTF v24 — plan Entry / SL / TP sur v25 • " + titre', source)
        self.assertIn("VISUEL COMPLÉMENTAIRE v24 : contexte et clôtures uniquement.", source)
        self.assertIn("La direction du plan, Entry, SL et TP de référence sont exclusivement ceux de ALIGN MTF PRO v25.", source)
        self.assertIn("if voirPlan and dirPlan != 0", source)
        self.assertIn("table.cell(t, 0, 2, ligne", source)

    def test_v24_does_not_emit_a_second_robot_bridge_payload(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertNotIn("bridgePayload =", source)
        self.assertNotIn("bridgeEnabled =", source)
        self.assertNotIn("alert(bridgePayload", source)


if __name__ == "__main__":
    unittest.main()
