import json
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import align_tv_bridge as bridge
from align_tv_bridge import (
    ACTIVE_MAX_AGE_MS,
    MAX_FUTURE_SKEW_MS,
    MTF_BAR_GRACE_MS,
    TIMEFRAME_MS,
    BridgeStore,
    REQUIRED_TIMEFRAMES,
    make_handler,
)


INGEST = "a" * 64
READ = "b" * 64
BASE_MS = 1_800_000_000_000
# Copié tel quel du journal des alertes TradingView (indicateur bridge, BTCUSD M15, 18/11/2026).
REAL_TV_PAYLOAD_BTC_SWING_20261118 = r'''{"source":"ALIGN_MTF_PRO_V25","symbol":"BTCUSD","tickerid":"CRYPTO:BTCUSD","timeframe":"M15","planTimeframe":"M15","entryTimeframe":"H1","entryZoneLow":63277.56,"entryZoneHigh":63803.65,"entryDecision":63540.60,"entryBarTime":1795017600000,"entryBarOpen":63066.10,"entryBarHigh":63067.01,"entryBarLow":62233.39,"entryBarClose":62690.24,"price":63436.08,"timestamp":1795023311064,"candle_time":1795023000000,"confirmed":true,"candle_confirmed":false,"bar_confirmed":false,"signal":"SHORT","verdict":"INTÉRESSANT : attendre les conditions finales","entry":63462.39,"sl":63917.40,"tp1":62779.89,"tp2":61869.88,"rrRatio":1.50,"macro_bull":1,"macro_bear":6,"long_score":0,"short_score":82,"scalp_inverse":false,"strategy":"SWING","anticipation":"AUCUNE","zone_proche":"PLAN","volume":"OK","rsi_etat":"NORMAL","rsi_1m":73.36,"rsi_5m":62.47,"rsi_15m":49.42,"rsi_60m":40.97,"lecture_1m":"LONG","lecture_5m":"NEUTRAL","lecture_15m":"SHORT","lecture_60m":"SHORT","mtf":{"M1":{"direction":1,"rsi":73.36,"bar_time":1795023300000},"M5":{"direction":0,"rsi":62.47,"bar_time":1795023300000},"M15":{"direction":0,"rsi":49.42,"bar_time":1795023000000},"M30":{"direction":-1,"rsi":42.50,"bar_time":1795023000000},"H1":{"direction":-1,"rsi":40.97,"bar_time":1795021200000},"H2":{"direction":-1,"rsi":40.36,"bar_time":1795017600000},"H4":{"direction":-1,"rsi":36.65,"bar_time":1795017600000},"D1":{"direction":-1,"rsi":22.27,"bar_time":1794960000000},"W1":{"direction":-1,"rsi":37.09,"bar_time":1794787200000}}}'''


def valid_payload(now_ms=BASE_MS, symbol="BTCUSD", timeframe="M1"):
    frames = ("M1", "M5", "M15", "M30", "H1", "H2", "H4", "D1", "W1")
    mtf = {
        tf: {"direction": 1, "rsi": 58.5, "bar_time": now_ms - 60_000}
        for tf in frames
    }
    return {
        "source": "ALIGN_MTF_PRO_V25",
        "symbol": symbol,
        "tickerid": "BINANCE:BTCUSDT",
        "timeframe": timeframe,
        "price": 100.0,
        "timestamp": now_ms,
        "candle_time": now_ms - 60_000,
        "confirmed": True,
        "candle_confirmed": True,
        "bar_confirmed": True,
        "signal": "LONG",
        "verdict": "ENTRÉE POSSIBLE",
        "entry": 100.0,
        "sl": 95.0,
        "tp1": 110.0,
        "tp2": 115.0,
        "rrRatio": 2.0,
        "macro_bull": 8,
        "macro_bear": 2,
        "long_score": 85,
        "short_score": 0,
        "scalp_inverse": False,
        "strategy": "DAY",
        "planTimeframe": "M15",
        "entryTimeframe": "M5",
        "entryZoneLow": 99.0,
        "entryZoneHigh": 101.0,
        "entryDecision": 100.0,
        "entryBarTime": now_ms - 300_000,
        "entryBarOpen": 99.5,
        "entryBarHigh": 101.0,
        "entryBarLow": 99.0,
        "entryBarClose": 100.5,
        "anticipation": "AUCUNE",
        "zone_proche": "FVG",
        "volume": "OK",
        "rsi_etat": "NORMAL",
        "rsi_1m": 56,
        "rsi_5m": 58,
        "rsi_15m": 60,
        "rsi_60m": 62,
        "lecture_1m": "LONG",
        "lecture_5m": "LONG",
        "lecture_15m": "LONG",
        "lecture_60m": "LONG",
        "mtf": mtf,
    }


class BridgeStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = BridgeStore(INGEST, READ)

    def test_accepts_snapshot_and_exposes_workflow_contract(self):
        status, result = self.store.ingest(valid_payload(), INGEST, BASE_MS)
        self.assertEqual(status, 200)
        self.assertTrue(result["accepted"])

        status, data = self.store.read("BTCUSD", BASE_MS + 1_000)
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["activeTimeframe"], "M1")
        self.assertTrue(data["activeTimeframeFresh"])
        self.assertEqual(data["snapshots"]["M1"]["price"], 100.0)
        self.assertEqual(data["snapshots"]["M1"]["robotV12"]["tp1"], 110.0)
        self.assertEqual(data["snapshots"]["M1"]["robotV12"]["tp2"], 115.0)
        for tf in REQUIRED_TIMEFRAMES:
            self.assertTrue(data["snapshots"][tf]["fresh"], tf)

    def test_rejects_wrong_ingest_token(self):
        status, result = self.store.ingest(valid_payload(), "c" * 64, BASE_MS)
        self.assertEqual(status, 401)
        self.assertEqual(result["error"], "unauthorized")

    def test_rejects_market_mixed_with_chart(self):
        # 18/11 : alerte posée sur NAS100 avec « Marché ALIGN » = BTCUSD.
        payload = valid_payload()
        payload["tickerid"] = "FX:NAS100"
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "symbol_tickerid_mismatch")
        payload = valid_payload(symbol="XAUUSD")
        status, result = self.store.ingest(payload, INGEST, BASE_MS)  # tickerid BTCUSDT
        self.assertEqual(result["error"], "symbol_tickerid_mismatch")
        self.assertEqual(self.store.read("BTCUSD", BASE_MS)[1]["snapshots"], {})

    def test_accepts_real_tradingview_tickers(self):
        for symbol, tickerid in (("BTCUSD", "CRYPTO:BTCUSD"), ("BTCUSD", "BINANCE:BTCUSDT"),
                                 ("XAUUSD", "FOREXCOM:XAUUSD"), ("XAUUSD", "OANDA:XAUUSD"),
                                 ("NAS100", "FX:NAS100"), ("NAS100", "CAPITALCOM:US100")):
            self.assertTrue(bridge.tickerid_matches_symbol(symbol, tickerid), tickerid)
        self.assertFalse(bridge.tickerid_matches_symbol("BTCUSD", ""))
        self.assertFalse(bridge.tickerid_matches_symbol("NAS100", "FOREXCOM:XAUUSD"))

    def test_real_tradingview_swing_payload_18_11_accepted(self):
        # Payload RÉEL du journal TradingView (BTC SWING, 18/11) refusé à tort deux fois :
        # bord de zone arrondi à 25 % du risque, bougie H1 clôturée âgée de 1 h 35.
        p = json.loads(REAL_TV_PAYLOAD_BTC_SWING_20261118)
        status, result = self.store.ingest(p, INGEST, p["timestamp"] + 5000)
        self.assertEqual((status, result.get("ok")), (200, True), result)
        lu = self.store.read("BTCUSD", p["timestamp"] + 8000)[1]
        self.assertTrue(lu["ok"])
        self.assertEqual(lu["snapshots"]["M15"]["robotV12"]["signal"], "SHORT")

    def test_wait_without_plan_keeps_real_mtf_reading(self):
        payload = valid_payload()
        payload.update({"signal": "WAIT", "strategy": "", "entryTimeframe": "UNSUPPORTED",
                        "entry": None, "sl": None, "tp1": None, "tp2": None,
                        "entryZoneLow": None, "entryZoneHigh": None, "entryDecision": None})
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200, result)
        robot = self.store.read("BTCUSD", BASE_MS)[1]["snapshots"]["M1"]["robotV12"]
        self.assertEqual(robot["signal"], "WAIT")
        self.assertIsNone(robot["entry"])
        self.assertFalse(robot["entryTriggered"])

    def test_entry_candle_older_than_two_timeframes_rejected(self):
        payload = valid_payload()
        payload["entryBarTime"] = BASE_MS - 2 * 300_000 - 60_000  # DAY → M5
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(result["error"], "stale_or_future_entry_trigger_candle")

    def test_rejects_unsupported_symbol(self):
        status, result = self.store.ingest(valid_payload(symbol="EURUSD"), INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "unsupported_symbol")

    def test_rejects_unsupported_active_timeframe(self):
        status, result = self.store.ingest(valid_payload(timeframe="M3"), INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "unsupported_active_timeframe")

    def test_rejects_missing_required_timeframe_instead_of_fabricating_it(self):
        payload = valid_payload()
        del payload["mtf"]["W1"]
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "missing_mtf_timeframe")
        self.assertEqual(result["timeframe"], "W1")

    def test_rejects_stale_source_timestamp(self):
        payload = valid_payload(now_ms=BASE_MS - 31_000)
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "stale_or_future_snapshot")

    def test_invalid_plan_becomes_wait_but_keeps_fresh_market_data(self):
        payload = valid_payload()
        payload["tp1"] = 98.0  # LONG target is on the wrong side of entry.
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        status, data = self.store.read("BTCUSD", BASE_MS)
        robot = data["snapshots"]["M1"]["robotV12"]
        self.assertTrue(data["ok"])
        self.assertEqual(robot["signal"], "WAIT")
        self.assertIsNone(robot["entry"])
        self.assertFalse(robot["confirmed"])

    def test_inverse_scalp_is_never_marked_confirmed(self):
        payload = valid_payload()
        payload["scalp_inverse"] = True
        status, _ = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, data = self.store.read("BTCUSD", BASE_MS)
        self.assertFalse(data["snapshots"]["M1"]["robotV12"]["confirmed"])

    def test_active_snapshot_age_uses_tradingview_source_timestamp(self):
        self.store.ingest(valid_payload(), INGEST, BASE_MS + 25_000)
        _, data = self.store.read("BTCUSD", BASE_MS + 26_000)
        self.assertEqual(data["activeTimeframeAgeMs"], 26_000)
        self.assertTrue(data["activeTimeframeFresh"])

    def test_active_snapshot_expires_after_thirty_seconds(self):
        self.store.ingest(valid_payload(), INGEST, BASE_MS)
        _, data = self.store.read("BTCUSD", BASE_MS + 31_000)
        self.assertFalse(data["ok"])
        self.assertFalse(data["activeTimeframeFresh"])

    def test_rejects_stale_m5_h1_d1_and_w1_bars_even_in_a_recent_payload(self):
        for tf in ("M5", "H1", "D1", "W1"):
            with self.subTest(timeframe=tf):
                payload = valid_payload()
                payload["mtf"][tf]["bar_time"] = (
                    BASE_MS - TIMEFRAME_MS[tf] - MTF_BAR_GRACE_MS - 1
                )
                status, result = self.store.ingest(payload, INGEST, BASE_MS)
                self.assertEqual(status, 400)
                self.assertEqual(result["error"], "stale_mtf_bar")
                self.assertEqual(result["timeframe"], tf)

    def test_accepts_h1_bar_near_its_expected_close(self):
        payload = valid_payload()
        payload["mtf"]["H1"]["bar_time"] = BASE_MS - TIMEFRAME_MS["H1"] + 1
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        self.assertTrue(result["accepted"])

    def test_rejects_future_mtf_bar_beyond_clock_tolerance(self):
        payload = valid_payload()
        payload["mtf"]["D1"]["bar_time"] = BASE_MS + MAX_FUTURE_SKEW_MS + 1
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "future_mtf_bar")
        self.assertEqual(result["timeframe"], "D1")

    def test_repeated_recent_alerts_do_not_refresh_an_old_h1_candle(self):
        first = valid_payload(now_ms=BASE_MS)
        original_h1_bar = first["mtf"]["H1"]["bar_time"]
        status, _ = self.store.ingest(first, INGEST, BASE_MS)
        self.assertEqual(status, 200)

        repeated = valid_payload(now_ms=BASE_MS + 20_000)
        repeated["mtf"]["H1"]["bar_time"] = original_h1_bar
        status, _ = self.store.ingest(repeated, INGEST, BASE_MS + 20_000)
        self.assertEqual(status, 200)

        _, data = self.store.read(
            "BTCUSD",
            BASE_MS + TIMEFRAME_MS["H1"] + MTF_BAR_GRACE_MS + 1,
        )
        self.assertFalse(data["snapshots"]["H1"]["fresh"])
        self.assertGreater(
            data["snapshots"]["H1"]["ageMs"],
            TIMEFRAME_MS["H1"] + MTF_BAR_GRACE_MS,
        )

    def test_snapshot_freshness_expires_from_bar_time_even_if_receipt_was_recent(self):
        payload = valid_payload()
        status, _ = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, data = self.store.read(
            "BTCUSD",
            BASE_MS + TIMEFRAME_MS["M5"] + MTF_BAR_GRACE_MS + 1,
        )
        self.assertFalse(data["snapshots"]["M5"]["fresh"])

    def test_ingest_rejects_plan_timeframe_other_than_m15(self):
        payload = valid_payload()
        payload["planTimeframe"] = "H4"
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "unsupported_plan_timeframe")

    def test_ingest_rejects_strategy_trigger_timeframe_mismatch(self):
        payload = valid_payload()
        payload["entryTimeframe"] = "H1"
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "entry_timeframe_strategy_mismatch")

    def test_ingest_rejects_invalid_entry_zone_geometry(self):
        payload = valid_payload()
        payload["entryDecision"] = payload["entryZoneHigh"]
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "invalid_entry_zone_geometry")

    def test_ingest_persists_plan_reference_zone_and_trigger_timeframe(self):
        status, _ = self.store.ingest(valid_payload(), INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, data = self.store.read("BTCUSD", BASE_MS)
        robot = data["snapshots"]["M1"]["robotV12"]
        self.assertEqual(robot["planTimeframe"], "M15")
        self.assertEqual(robot["entryTimeframe"], "M5")
        self.assertEqual((robot["entryZoneLow"], robot["entryDecision"], robot["entryZoneHigh"]),
                         (99.0, 100.0, 101.0))

    def test_ingest_sets_entry_trigger_only_after_closed_retest_and_decision(self):
        payload = valid_payload()
        status, _ = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, data = self.store.read("BTCUSD", BASE_MS)
        robot = data["snapshots"]["M1"]["robotV12"]
        self.assertTrue(robot["entryTriggered"])
        self.assertEqual(robot["entryBarTime"], BASE_MS - 300_000)

    def test_ingest_does_not_trigger_without_retesting_zone(self):
        payload = valid_payload()
        payload["entryBarLow"] = 102.0
        payload["entryBarHigh"] = 103.0
        payload["entryBarOpen"] = 102.0
        payload["entryBarClose"] = 102.5
        status, _ = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, data = self.store.read("BTCUSD", BASE_MS)
        self.assertFalse(data["snapshots"]["M1"]["robotV12"]["entryTriggered"])

    def test_ingest_does_not_trigger_without_close_beyond_decision_line(self):
        payload = valid_payload()
        payload["entryBarClose"] = 99.5
        status, _ = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, data = self.store.read("BTCUSD", BASE_MS)
        self.assertFalse(data["snapshots"]["M1"]["robotV12"]["entryTriggered"])

    def test_ingest_rejects_stale_or_future_entry_trigger_candle(self):
        for time_value in (BASE_MS - 2 * TIMEFRAME_MS["M5"] - MTF_BAR_GRACE_MS - 1,
                           BASE_MS + MAX_FUTURE_SKEW_MS + 1):
            with self.subTest(entryBarTime=time_value):
                payload = valid_payload()
                payload["entryBarTime"] = time_value
                status, result = self.store.ingest(payload, INGEST, BASE_MS)
                self.assertEqual(status, 400)
                self.assertEqual(result["error"], "stale_or_future_entry_trigger_candle")

    def test_read_response_never_contains_either_token(self):
        self.store.ingest(valid_payload(), INGEST, BASE_MS)
        _, data = self.store.read("BTCUSD", BASE_MS)
        rendered = str(data)
        self.assertNotIn(INGEST, rendered)
        self.assertNotIn(READ, rendered)

    def test_http_ingest_and_authenticated_read_endpoints(self):
        store = BridgeStore(INGEST, READ)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            now_ms = int(time.time() * 1000)
            body = json.dumps(valid_payload(now_ms=now_ms)).encode("utf-8")
            req = Request(base + "/ingest/" + INGEST, data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertTrue(json.loads(response.read())["accepted"])

            req = Request(base + "/bridge/robot-v12/mtf?symbol=BTCUSD", headers={"Authorization": "Bearer " + READ})
            with urlopen(req, timeout=3) as response:
                data = json.loads(response.read())
                self.assertTrue(data["ok"])
                self.assertEqual(data["activeTimeframe"], "M1")

            req = Request(base + "/bridge/robot-v12/mtf?symbol=BTCUSD")
            with self.assertRaises(HTTPError) as error:
                urlopen(req, timeout=3)
            self.assertEqual(error.exception.code, 401)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_http_ignores_existing_plain_text_pine_alerts(self):
        store = BridgeStore(INGEST, READ)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(store))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            req = Request(
                f"http://127.0.0.1:{server.server_port}/ingest/{INGEST}",
                data=b"BTCUSD ACHAT FORT | existing human alert",
                headers={"Content-Type": "text/plain"},
                method="POST",
            )
            with urlopen(req, timeout=3) as response:
                self.assertEqual(response.status, 202)
                self.assertTrue(json.loads(response.read())["ignored"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
