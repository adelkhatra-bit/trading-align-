import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import align_bot


class ForensicAuditSnapshotTest(unittest.TestCase):
    def test_snapshot_keeps_timeframes_and_tradingview_freshness_separate(self):
        etat = {}
        cle = {"trade": {"d": 1, "e": 100.0, "sl": 98.0, "tp1": 104.0, "tp2": 106.0,
                         "cree": 1700000000, "statut": "entree", "src": "test"}}
        r = {
            "t": 1700000300, "m1": [{"c": 101.0}], "confirme": 1,
            "dirs": [1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1],
            "rsis": [55.0] * 11,
            "tv_indicator_mtf": {
                "available": True, "activeTimeframe": "H4", "activeTimeframeAgeMs": 1200,
                "receivedTimeframes": ["M5", "H1", "H4"],
                "snapshots": {"H4": {"fresh": True, "confirmed": True,
                    "robotV12": {"signal": "LONG", "entry": 100.0, "sl": 98.0, "tp": 104.0,
                                 "long_score": 8, "short_score": 2}}}
            }
        }
        align_bot.capturer_snapshot_audit(etat, "BTC", r, cle, ["LONG confirmé"])
        snap = etat["audit_mtf"]["BTC"][0]
        self.assertEqual(snap["mtf"]["4h"]["direction"], 1)
        self.assertEqual(snap["mtf"]["1h"]["direction"], 1)
        self.assertEqual(snap["tradingview"]["activeTimeframe"], "H4")
        self.assertTrue(snap["tradingview"]["snapshots"]["H4"]["fresh"])
        self.assertEqual(snap["trade"]["audit_key"], align_bot.cle_audit_trade("BTC", cle["trade"]))
        self.assertIn("LONG confirmé", snap["messages"])

    def test_snapshot_history_is_bounded(self):
        etat = {"audit_mtf": {"GOLD": [{"t": i} for i in range(601)]}}
        r = {"t": 1000, "m1": [{"c": 1.0}], "dirs": [], "rsis": []}
        align_bot.capturer_snapshot_audit(etat, "GOLD", r, {})
        self.assertEqual(len(etat["audit_mtf"]["GOLD"]), 600)
        self.assertEqual(etat["audit_mtf"]["GOLD"][-1]["t"], 1000)


if __name__ == "__main__":
    unittest.main()
