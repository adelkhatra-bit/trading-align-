import os
import tempfile
import unittest
from unittest.mock import patch

import align_bot as ab


class GoldClosedSessionDiagnostics(unittest.TestCase):
    NOW = 1_800_000_000

    def test_status_reports_gold_closed_even_before_first_analysis(self):
        state = {
            "ia_dernier_statut": "CONNECTED",
            "ia_dernier_fournisseur": "Groq",
            "sauve_t": self.NOW - 30,
            "cal": {"ev": [{"t": self.NOW + 3600, "titre": "Test"}]},
        }
        with patch.object(ab, "cme_ouvert", return_value=False),              patch.object(ab, "prochaine_ouverture_cme", return_value=self.NOW + 3600):
            report = ab.texte_statut(state, {}, self.NOW)

        self.assertIn("GOLD : march", report)
        self.assertIn("BTC : pas encore d'analyse", report)
        self.assertNotIn("GOLD : pas encore d'analyse", report)
        self.assertIn("1 point(s)", report)  # BTC has no first snapshot; GOLD closure is not an alert

    def test_bridge_diagnostic_does_not_query_gold_during_closed_cme_session(self):
        snapshots = {tf: {"fresh": True} for tf in ("M5", "M15", "H1", "H4", "D1", "W1")}
        btc = {
            "available": True,
            "activeTimeframe": "H4",
            "activeTimeframeAgeMs": 35000,
            "snapshots": snapshots,
        }
        with tempfile.TemporaryDirectory() as runner_temp,              patch.dict(os.environ, {"RUNNER_TEMP": runner_temp}),              patch.object(ab.time, "time", return_value=self.NOW),              patch.object(ab, "cme_ouvert", return_value=False),              patch.object(ab, "prochaine_ouverture_cme", return_value=self.NOW + 3600),              patch.object(ab, "fetch_tv_mtf", return_value=btc) as fetch:
            report = ab.texte_diag()

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(fetch.call_args.args[0], "XBTUSD")
        self.assertIn("GOLD : MARCH", report)
        self.assertIn("CME FERM", report)
        self.assertIn("BTC : BRIDGE CONNECT", report)
        self.assertNotIn("GOLD : BRIDGE INDISPONIBLE", report)
        self.assertNotIn("GOLD : BRIDGE INVALIDE", report)

    def test_bridge_diagnostic_still_checks_gold_when_cme_is_open(self):
        btc = {"available": False, "reason": "r?ponse bridge invalide", "snapshots": {}}
        gold = {"available": False, "reason": "bridge inaccessible", "snapshots": {}}
        with tempfile.TemporaryDirectory() as runner_temp,              patch.dict(os.environ, {"RUNNER_TEMP": runner_temp}),              patch.object(ab.time, "time", return_value=self.NOW),              patch.object(ab, "cme_ouvert", return_value=True),              patch.object(ab, "fetch_tv_mtf", side_effect=[btc, gold]) as fetch:
            report = ab.texte_diag()

        self.assertEqual([call.args[0] for call in fetch.call_args_list], ["XBTUSD", "XAUUSD"])
        self.assertIn("GOLD : BRIDGE INDISPONIBLE", report)


if __name__ == "__main__":
    unittest.main()
