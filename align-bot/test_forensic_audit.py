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


    def test_gold_and_nasdaq_reversal_watch_remains_available(self):
        # M5/M15 turn bullish while H1/H4 remain bearish: observation only.
        dirs = [0] * 11
        dirs[2], dirs[4], dirs[7], dirs[9] = 1, 1, -1, -1
        b15 = [{"t": i * 900, "o": 99.0, "h": 101.0, "l": 98.0, "c": 100.0, "v": 10.0}
               for i in range(42)]
        b15[-2]["v"] = 20.0
        b1 = [{"h": 105.0, "l": 95.0} for _ in range(6)]
        b4 = [{"h": 110.0, "l": 90.0} for _ in range(6)]
        r = {"dirs": dirs, "b5": [{"h": 101.0, "l": 98.0} for _ in range(7)],
             "b15": b15, "b1h": b1, "b4h": b4, "m1": [{"c": 100.0}], "t": 999999}
        for market in ("GOLD", "NASDAQ"):
            cle = {}
            alert = align_bot.retournement_marche(market, r, cle)
            self.assertIsNotNone(alert, market)
            self.assertIn("RETOURNEMENT EN OBSERVATION", alert)
            self.assertIn("PAS DE POSITION", alert)



    def test_pre_entry_order_is_recorded_without_fake_trade_identity(self):
        etat = {}
        cle = {"ordre": {"d": -1, "e": 200.0, "sl": 204.0, "tp1": 192.0,
                         "tp2": 188.0, "src": "FVG", "za": 199.0, "zb": 201.0}}
        r = {"t": 1700000400, "m1": [{"c": 200.5}], "dirs": [], "rsis": []}
        align_bot.capturer_snapshot_audit(etat, "NASDAQ", r, cle)
        plan = etat["audit_mtf"]["NASDAQ"][0]["trade"]
        self.assertEqual(plan["plan_source"], "ordre_en_preparation")
        self.assertEqual(plan["src"], "FVG")
        self.assertNotIn("audit_key", plan)



if __name__ == "__main__":
    unittest.main()
