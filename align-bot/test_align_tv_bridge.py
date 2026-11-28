import json
import io
import os
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import align_tv_bridge as bridge
from align_tv_bridge import (
    ACTIVE_MAX_AGE_MS,
    ENTRY_BAR_GRACE_MS,
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
REAL_TV_PAYLOAD_BTC_SWING_20261118 = r'''{"source":"ALIGN_MTF_PRO_V25","symbol":"BTCUSD","tickerid":"CRYPTO:BTCUSD","timeframe":"M15","planTimeframe":"M15","entryTimeframe":"H1","entryZoneLow":63277.56,"entryZoneHigh":63803.65,"entryDecision":63540.60,"entryBarTime":1795021200000,"entryBarOpen":63066.10,"entryBarHigh":63067.01,"entryBarLow":62233.39,"entryBarClose":62690.24,"price":63436.08,"timestamp":1795023311064,"candle_time":1795023000000,"confirmed":true,"candle_confirmed":false,"bar_confirmed":false,"signal":"SHORT","verdict":"INTÉRESSANT : attendre les conditions finales","entry":63462.39,"sl":63917.40,"tp1":62779.89,"tp2":61869.88,"rrRatio":1.50,"macro_bull":1,"macro_bear":6,"long_score":0,"short_score":82,"scalp_inverse":false,"strategy":"SWING","anticipation":"AUCUNE","zone_proche":"PLAN","volume":"OK","rsi_etat":"NORMAL","rsi_1m":73.36,"rsi_5m":62.47,"rsi_15m":49.42,"rsi_60m":40.97,"lecture_1m":"LONG","lecture_5m":"NEUTRAL","lecture_15m":"SHORT","lecture_60m":"SHORT","mtf":{"M1":{"direction":1,"rsi":73.36,"bar_time":1795023300000},"M5":{"direction":0,"rsi":62.47,"bar_time":1795023300000},"M15":{"direction":0,"rsi":49.42,"bar_time":1795023000000},"M30":{"direction":-1,"rsi":42.50,"bar_time":1795023000000},"H1":{"direction":-1,"rsi":40.97,"bar_time":1795021200000},"H2":{"direction":-1,"rsi":40.36,"bar_time":1795021200000},"H4":{"direction":-1,"rsi":36.65,"bar_time":1795021200000},"D1":{"direction":-1,"rsi":22.27,"bar_time":1794960000000},"W1":{"direction":-1,"rsi":37.09,"bar_time":1794787200000}}}'''


def valid_payload(now_ms=BASE_MS, symbol="BTCUSD", timeframe="M1"):
    frames = ("M1", "M3", "M5", "M10", "M15", "M30", "M45", "H1", "H2", "H4", "D1", "W1")
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

    def test_pine_bridge_uses_closed_candle_clock_for_bar_timestamps(self):
        pine_path = Path(__file__).resolve().parent / "pine" / "ALIGN_MTF_PRO_v25.pine"
        pine = pine_path.read_text(encoding="utf-8")
        expected = {
            "bridgeTimeM1": '"1"',
            "bridgeTimeM3": '"3"',
            "bridgeTimeM5": '"5"',
            "bridgeTimeM10": '"10"',
            "bridgeTimeM15": '"15"',
            "bridgeTimeM30": '"30"',
            "bridgeTimeM45": '"45"',
            "bridgeTimeH1": '"60"',
            "bridgeTimeH2": '"120"',
            "bridgeTimeH4": '"240"',
            "bridgeTimeD1": '"D"',
            "bridgeTimeW1": '"W"',
        }
        for variable, interval in expected.items():
            with self.subTest(timeframe=variable):
                self.assertIn(variable + '] = f_etat_mtf(' + interval + ')', pine)
        self.assertIn("EtatMtfSnapshot etatRequested = request.security(syminfo.tickerid, tf, f_etat(), lookahead=barmerge.lookahead_off)", pine)
        self.assertIn("request.security(syminfo.tickerid, tf, f_etat(), lookahead=barmerge.lookahead_off)", pine)
        self.assertIn('EtatMtfSnapshot.new(d, sqz ? 1 : 0, rsiValue, time_close, d[1], sqz[1] ? 1 : 0, rsiValue[1], time_close[1], time_close <= timenow)', pine)
        self.assertIn('type EtatMtfSnapshot', pine)
        self.assertNotIn('f_dir_confirme()', pine)

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

    def test_bridge_marks_canonical_plan_unready_until_m15_chart_reports(self):
        status, _ = self.store.ingest(valid_payload(timeframe="M1"), INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, before = self.store.read("BTCUSD", BASE_MS + 1_000)
        self.assertTrue(before["ok"])  # MTF transport is alive
        self.assertFalse(before["canonicalPlanFresh"])  # but no authoritative M15 plan yet

        status, _ = self.store.ingest(valid_payload(timeframe="M15"), INGEST, BASE_MS + 2_000)
        self.assertEqual(status, 200)
        _, after = self.store.read("BTCUSD", BASE_MS + 3_000)
        self.assertTrue(after["canonicalPlanFresh"])
        self.assertTrue(after["snapshots"]["M15"]["robotFresh"])

    def test_frequent_m1_alerts_cannot_keep_an_old_m15_plan_fresh(self):
        status, _ = self.store.ingest(valid_payload(now_ms=BASE_MS, timeframe="M15"), INGEST, BASE_MS)
        self.assertEqual(status, 200)
        status, _ = self.store.ingest(valid_payload(now_ms=BASE_MS + 100_000, timeframe="M1"),
                                      INGEST, BASE_MS + 100_000)
        self.assertEqual(status, 200)

        _, data = self.store.read("BTCUSD", BASE_MS + 101_000)
        self.assertTrue(data["activeTimeframeFresh"])
        self.assertEqual(data["activeTimeframe"], "M1")
        self.assertFalse(data["snapshots"]["M15"]["robotFresh"])
        self.assertFalse(data["canonicalPlanFresh"])

    def test_m15_plan_is_preserved_when_other_chart_timeframes_send_opposite_signals(self):
        # The bridge receives every chart's alert stream. A later M1 payload must
        # not erase or replace the canonical M15 ROBOT V12 decision.
        m15 = valid_payload(now_ms=BASE_MS + 15_000, timeframe="M15")
        status, result = self.store.ingest(m15, INGEST, BASE_MS + 15_000)
        self.assertEqual(status, 200, result)

        m1 = valid_payload(now_ms=BASE_MS + 20_000, timeframe="M1")
        m1.update({
            "signal": "SHORT", "entry": 100.0, "sl": 105.0,
            "tp1": 90.0, "tp2": 85.0, "short_score": 86, "long_score": 0,
            "entryZoneLow": 99.0, "entryZoneHigh": 101.0, "entryDecision": 100.0,
            "entryBarOpen": 100.5, "entryBarHigh": 101.0,
            "entryBarLow": 99.0, "entryBarClose": 99.5,
        })
        status, result = self.store.ingest(m1, INGEST, BASE_MS + 20_000)
        self.assertEqual(status, 200, result)

        # A delayed M15 alert older than the accepted M15 plan must not roll it back.
        delayed_m15 = valid_payload(now_ms=BASE_MS + 10_000, timeframe="M15")
        delayed_m15.update({
            "signal": "SHORT", "entry": 100.0, "sl": 105.0,
            "tp1": 90.0, "tp2": 85.0, "short_score": 86, "long_score": 0,
            "entryZoneLow": 99.0, "entryZoneHigh": 101.0, "entryDecision": 100.0,
            "entryBarOpen": 100.5, "entryBarHigh": 101.0,
            "entryBarLow": 99.0, "entryBarClose": 99.5,
        })
        status, result = self.store.ingest(delayed_m15, INGEST, BASE_MS + 20_000)
        self.assertEqual(status, 200, result)

        _, data = self.store.read("BTCUSD", BASE_MS + 21_000)
        self.assertTrue(data["ok"])
        self.assertEqual(data["activeTimeframe"], "M1")
        self.assertTrue(data["canonicalPlanFresh"])
        self.assertEqual(data["snapshots"]["M15"]["robotV12"]["signal"], "LONG")
        self.assertEqual(data["snapshots"]["M15"]["robotV12"]["entry"], 100.0)
        self.assertEqual(data["snapshots"]["M1"]["robotV12"]["signal"], "SHORT")
        self.assertEqual(data["snapshots"]["M15"]["robotUpdatedAt"], BASE_MS + 15_000)
        self.assertTrue(data["snapshots"]["M15"]["robotFresh"])

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
        self.assertEqual(self.store.read("BTCUSD", BASE_MS)[1]["snapshots"], {})
        payload = valid_payload(symbol="XAUUSD")
        status, result = self.store.ingest(payload, INGEST, BASE_MS)  # tickerid BTCUSDT
        self.assertEqual(result["error"], "symbol_tickerid_mismatch")
        self.assertEqual(self.store.read("BTCUSD", BASE_MS)[1]["snapshots"], {})
        self.assertEqual(self.store.read("XAUUSD", BASE_MS)[1]["snapshots"], {})

    def test_rejects_cross_market_payloads_for_btc_and_gold(self):
        # Le marché déclaré doit correspondre au ticker réel : aucune contamination croisée.
        for symbol, tickerid in (("BTCUSD", "FOREXCOM:XAUUSD"), ("XAUUSD", "BINANCE:BTCUSDT")):
            payload = valid_payload(symbol=symbol)
            payload["tickerid"] = tickerid
            status, result = self.store.ingest(payload, INGEST, BASE_MS)
            self.assertEqual(status, 400, (symbol, tickerid, result))
            self.assertEqual(result["error"], "symbol_tickerid_mismatch")
            self.assertEqual(self.store.read("BTCUSD", BASE_MS)[1]["snapshots"], {})
            self.assertEqual(self.store.read("XAUUSD", BASE_MS)[1]["snapshots"], {})

    def test_accepts_real_tradingview_tickers(self):
        for symbol, tickerid in (("BTCUSD", "CRYPTO:BTCUSD"), ("BTCUSD", "BINANCE:BTCUSDT"),
                                 ("XAUUSD", "FOREXCOM:XAUUSD"), ("XAUUSD", "OANDA:XAUUSD"),
                                 ):
            self.assertTrue(bridge.tickerid_matches_symbol(symbol, tickerid), tickerid)
        self.assertFalse(bridge.tickerid_matches_symbol("BTCUSD", ""))
        self.assertFalse(bridge.tickerid_matches_symbol("XAUUSD", "BINANCE:BTCUSDT"))

    def test_legacy_real_tradingview_swing_payload_missing_new_mtf_is_rejected(self):
        # Payload réel du 18/11 : il précède M3/M10/M45 et ne doit pas être accepté
        # comme snapshot complet après l'extension du contrat MTF.
        p = json.loads(REAL_TV_PAYLOAD_BTC_SWING_20261118)
        status, result = self.store.ingest(p, INGEST, p["timestamp"] + 5000)
        self.assertEqual(status, 400, result)
        self.assertEqual(result["error"], "missing_mtf_timeframe")
        self.assertEqual(result["timeframe"], "M3")
        self.assertEqual(self.store.read("BTCUSD", p["timestamp"] + 8000)[1]["snapshots"], {})

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

    def test_stale_entry_trigger_keeps_fresh_mtf_but_downgrades_plan_to_wait(self):
        payload = valid_payload()
        payload["entryBarTime"] = BASE_MS - 300_000 - 60_000  # DAY → M5
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200, result)
        self.assertTrue(result["accepted"])
        self.assertEqual(
            result["diagnosticRejection"]["error"],
            "stale_or_future_entry_trigger_candle",
        )

        status, data = self.store.read("BTCUSD", BASE_MS + 1_000)
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertTrue(data["activeTimeframeFresh"])
        self.assertEqual(
            data["lastRejection"]["error"],
            "stale_or_future_entry_trigger_candle",
        )
        robot = data["snapshots"]["M1"]["robotV12"]
        self.assertEqual(robot["signal"], "WAIT")
        self.assertFalse(robot["confirmed"])
        self.assertFalse(robot["entryTriggered"])
        for field in ("entry", "sl", "tp", "tp1", "tp2", "entryZoneLow",
                      "entryZoneHigh", "entryDecision", "entryBarTime"):
            self.assertIsNone(robot[field], field)

    def test_missing_entry_trigger_candle_downgrades_to_wait_and_keeps_fresh_mtf(self):
        fields = ("entryBarTime", "entryBarOpen", "entryBarHigh", "entryBarLow", "entryBarClose")
        for missing_field in fields:
            with self.subTest(missing_field=missing_field):
                payload = valid_payload()
                payload[missing_field] = None
                status, result = self.store.ingest(payload, INGEST, BASE_MS)
                self.assertEqual(status, 200, result)
                self.assertTrue(result["accepted"])
                self.assertEqual(
                    result["diagnosticRejection"]["error"],
                    "missing_entry_trigger_candle",
                )

                status, data = self.store.read("BTCUSD", BASE_MS + 1_000)
                self.assertEqual(status, 200)
                self.assertTrue(data["ok"])
                self.assertTrue(data["activeTimeframeFresh"])
                self.assertEqual(
                    data["lastRejection"]["error"],
                    "missing_entry_trigger_candle",
                )
                robot = data["snapshots"]["M1"]["robotV12"]
                self.assertEqual(robot["signal"], "WAIT")
                self.assertFalse(robot["confirmed"])
                self.assertFalse(robot["entryTriggered"])
                for field in ("entry", "sl", "tp", "tp1", "tp2", "entryZoneLow",
                              "entryZoneHigh", "entryDecision", "entryBarTime"):
                    self.assertIsNone(robot[field], field)

    def test_stale_entry_trigger_rejection_emits_diagnostic_line(self):
        payload = valid_payload()
        payload["entryBarTime"] = BASE_MS - TIMEFRAME_MS["M5"] - ENTRY_BAR_GRACE_MS - 1
        output = io.StringIO()
        with redirect_stdout(output):
            status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200, result)
        self.assertEqual(
            result["diagnosticRejection"]["error"],
            "stale_or_future_entry_trigger_candle",
        )
        log_line = output.getvalue().strip()
        self.assertIn("TRIGGER_STALE symbol=BTCUSD entry_tf_ms=300000", log_line)
        self.assertNotIn("BTC_TRIGGER_STALE", log_line)
        self.assertIn(f"entry_bar_time_ms={payload['entryBarTime']}", log_line)
        self.assertIn(f"now_ms={BASE_MS}", log_line)
        self.assertIn(f"age_ms={BASE_MS - payload['entryBarTime']}", log_line)
        self.assertIn(f"threshold_ms={TIMEFRAME_MS['M5'] + ENTRY_BAR_GRACE_MS}", log_line)
        self.assertIn("received_ms=absent", log_line)


    def test_rejects_unsupported_symbol(self):
        status, result = self.store.ingest(valid_payload(symbol="EURUSD"), INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "unsupported_symbol")

    def test_rejects_unsupported_active_timeframe(self):
        status, result = self.store.ingest(valid_payload(timeframe="M2"), INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "unsupported_active_timeframe")

    def test_accepts_new_indicator_timeframes_m3_m10_m45(self):
        for tf in ("M3", "M10", "M45"):
            with self.subTest(timeframe=tf):
                status, result = self.store.ingest(valid_payload(timeframe=tf), INGEST, BASE_MS)
                self.assertEqual(status, 200, result)
                self.assertTrue(result["accepted"])

    def test_rejects_missing_required_timeframe_instead_of_fabricating_it(self):
        payload = valid_payload()
        del payload["mtf"]["W1"]
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 400)
        self.assertEqual(result["error"], "missing_mtf_timeframe")
        self.assertEqual(result["timeframe"], "W1")

    def test_rejects_stale_source_timestamp(self):
        payload = valid_payload(now_ms=BASE_MS - ACTIVE_MAX_AGE_MS - 1_000)
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

    def test_plan_without_aligned_strategy_becomes_wait_and_keeps_mtf(self):
        # Cas réel BTC du 19/11 : signal LONG, aucune stratégie alignée, entryTimeframe UNSUPPORTED.
        payload = valid_payload()
        payload["strategy"] = ""
        payload["entryTimeframe"] = "UNSUPPORTED"
        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200, result)
        status, data = self.store.read("BTCUSD", BASE_MS)
        robot = data["snapshots"]["M1"]["robotV12"]
        self.assertTrue(data["ok"])
        self.assertEqual(robot["signal"], "WAIT")
        self.assertIsNone(robot["entry"])
        self.assertFalse(robot["confirmed"])

    def test_last_rejection_is_exposed_for_diagnosis_and_cleared_by_a_valid_snapshot(self):
        # Le journal du bot doit pouvoir dire POURQUOI un marché est indisponible (jamais de secret).
        refuse = valid_payload()
        refuse["timestamp"] = BASE_MS - 120_000  # trop vieux : stale_or_future_snapshot
        status, body = self.store.ingest(refuse, INGEST, BASE_MS)
        self.assertEqual(status, 400, body)
        _, data = self.store.read("BTCUSD", BASE_MS + 4_000)
        self.assertFalse(data["ok"])
        self.assertEqual(data["lastRejection"], {"error": body["error"], "ageMs": 4_000})
        self.assertNotIn(INGEST, json.dumps(data))
        self.assertNotIn(READ, json.dumps(data))
        status, _ = self.store.ingest(valid_payload(), INGEST, BASE_MS + 5_000)
        self.assertEqual(status, 200)
        _, data = self.store.read("BTCUSD", BASE_MS + 5_000)
        self.assertIsNone(data["lastRejection"])

    def test_wrong_ingest_token_never_records_a_rejection(self):
        status, _ = self.store.ingest(valid_payload(), "mauvais-jeton", BASE_MS)
        self.assertEqual(status, 401)
        _, data = self.store.read("BTCUSD", BASE_MS)
        self.assertIsNone(data["lastRejection"])

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

    def test_active_snapshot_stays_fresh_between_two_tradingview_alerts(self):
        # Cas réel du 19/11 : TradingView n'alerte qu'une fois par minute, le relais relit toutes les 10 s.
        # UT active M5 comme en production (alertes posées sur le graphique 5 min).
        status, body = self.store.ingest(valid_payload(timeframe="M5"), INGEST, BASE_MS + 70_000)
        self.assertEqual(status, 200, body)  # même message relayé 70 s après l'alerte : accepté
        _, data = self.store.read("BTCUSD", BASE_MS + 70_000)
        self.assertTrue(data["activeTimeframeFresh"])

    def test_active_snapshot_expires_after_ninety_seconds(self):
        self.store.ingest(valid_payload(), INGEST, BASE_MS)
        _, data = self.store.read("BTCUSD", BASE_MS + 91_000)
        self.assertFalse(data["ok"])
        self.assertFalse(data["activeTimeframeFresh"])

    def test_closed_m5_m15_bars_allow_webhook_delivery_delay_but_not_old_data(self):
        # TradingView sends the last CLOSED lower-timeframe bar on a higher chart.
        # The webhook may arrive up to 60 s later and the mailbox relay polls every 10 s.
        payload = valid_payload()
        for tf in ("M5", "M15"):
            payload["mtf"][tf]["bar_time"] = BASE_MS - TIMEFRAME_MS[tf] - 80_000

        status, result = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200, result)
        self.assertTrue(result["accepted"])

        _, fresh = self.store.read("BTCUSD", BASE_MS)
        self.assertTrue(fresh["snapshots"]["M5"]["fresh"])
        self.assertTrue(fresh["snapshots"]["M15"]["fresh"])
        self.assertTrue(fresh["ok"])

        # Once the same closed bars exceed the 90 s delivery window, they are stale.
        _, expired = self.store.read("BTCUSD", BASE_MS + 11_000)
        self.assertFalse(expired["snapshots"]["M5"]["fresh"])
        self.assertFalse(expired["snapshots"]["M15"]["fresh"])
        self.assertFalse(expired["ok"])

    def test_stale_mtf_bars_are_preserved_but_block_bridge_signals(self):
        for tf in ("M5", "H1", "D1", "W1"):
            with self.subTest(timeframe=tf):
                payload = valid_payload()
                payload["mtf"][tf]["bar_time"] = (
                    BASE_MS - TIMEFRAME_MS[tf] - MTF_BAR_GRACE_MS - 1
                )
                status, result = self.store.ingest(payload, INGEST, BASE_MS)
                self.assertEqual(status, 200, result)
                self.assertTrue(result["accepted"])
                _, data = self.store.read("BTCUSD", BASE_MS)
                self.assertFalse(data["ok"])
                self.assertFalse(data["snapshots"][tf]["fresh"])
                self.assertEqual(data["snapshots"][tf]["barTime"], payload["mtf"][tf]["bar_time"])

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
        payload["price"] = 100.25
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

    def test_ingest_does_not_trigger_after_live_price_has_left_long_entry_zone(self):
        payload = valid_payload()
        payload["price"] = 102.0
        status, _ = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, data = self.store.read("BTCUSD", BASE_MS)
        robot = data["snapshots"]["M1"]["robotV12"]
        self.assertFalse(robot["entryTriggered"])
        self.assertEqual(robot["signal"], "LONG")

    def test_ingest_does_not_trigger_if_live_price_returns_below_long_decision(self):
        payload = valid_payload()
        payload["price"] = 99.5
        status, _ = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, data = self.store.read("BTCUSD", BASE_MS)
        self.assertFalse(data["snapshots"]["M1"]["robotV12"]["entryTriggered"])

    def test_ingest_does_not_trigger_after_live_price_has_left_short_entry_zone(self):
        payload = valid_payload()
        payload.update({
            "signal": "SHORT", "entry": 100.0, "sl": 105.0,
            "tp1": 90.0, "tp2": 85.0, "long_score": 0, "short_score": 85,
            "entryZoneLow": 99.0, "entryZoneHigh": 101.0, "entryDecision": 100.0,
            "entryBarOpen": 100.5, "entryBarHigh": 101.0,
            "entryBarLow": 99.0, "entryBarClose": 99.5,
            "price": 98.0,
        })
        status, _ = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, data = self.store.read("BTCUSD", BASE_MS)
        self.assertFalse(data["snapshots"]["M1"]["robotV12"]["entryTriggered"])

    def test_ingest_triggers_short_only_while_live_price_is_in_correct_half_of_zone(self):
        payload = valid_payload()
        payload.update({
            "signal": "SHORT", "entry": 100.0, "sl": 105.0,
            "tp1": 90.0, "tp2": 85.0, "long_score": 0, "short_score": 85,
            "entryZoneLow": 99.0, "entryZoneHigh": 101.0, "entryDecision": 100.0,
            "entryBarOpen": 100.5, "entryBarHigh": 101.0,
            "entryBarLow": 99.0, "entryBarClose": 99.5,
            "price": 99.75,
        })
        status, _ = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, data = self.store.read("BTCUSD", BASE_MS)
        self.assertTrue(data["snapshots"]["M1"]["robotV12"]["entryTriggered"])

    def test_ingest_triggers_only_while_live_price_remains_in_correct_half_of_zone(self):
        payload = valid_payload()
        payload["price"] = 100.25
        status, _ = self.store.ingest(payload, INGEST, BASE_MS)
        self.assertEqual(status, 200)
        _, data = self.store.read("BTCUSD", BASE_MS)
        self.assertTrue(data["snapshots"]["M1"]["robotV12"]["entryTriggered"])

    def test_stale_trigger_counters_are_written_per_market_to_runner_temp(self):
        self.assertTrue(
            hasattr(bridge, "DIAG_TRIGGER_COUNT"),
            "bridge must expose per-market stale trigger counters",
        )
        self.assertTrue(
            hasattr(bridge, "DIAG_TRIGGER_LAST"),
            "bridge must expose per-market last stale trigger details",
        )
        previous_counts = dict(bridge.DIAG_TRIGGER_COUNT)
        previous_last = dict(getattr(bridge, "DIAG_TRIGGER_LAST", {}))
        previous_started = getattr(bridge, "DIAG_STARTED_AT_MS", None)
        old_runner_temp = os.environ.get("RUNNER_TEMP")
        try:
            with tempfile.TemporaryDirectory() as runner_temp:
                os.environ["RUNNER_TEMP"] = runner_temp
                bridge.DIAG_TRIGGER_COUNT.clear()
                bridge.DIAG_TRIGGER_COUNT.update({"BTCUSD": 0, "XAUUSD": 0})
                bridge.DIAG_TRIGGER_LAST.clear()

                btc = valid_payload(symbol="BTCUSD")
                btc["tickerid"] = "BINANCE:BTCUSDT"
                btc["entryBarTime"] = BASE_MS - TIMEFRAME_MS["M5"] - ENTRY_BAR_GRACE_MS - 1
                status, result = self.store.ingest(btc, INGEST, BASE_MS)
                self.assertEqual(status, 200, result)

                gold = valid_payload(symbol="XAUUSD")
                gold["tickerid"] = "FOREXCOM:XAUUSD"
                gold["entryBarTime"] = BASE_MS - TIMEFRAME_MS["M5"] - ENTRY_BAR_GRACE_MS - 2
                status, result = self.store.ingest(gold, INGEST, BASE_MS + 1_000)
                self.assertEqual(status, 200, result)

                diagnostic_path = os.path.join(runner_temp, "align_diag.json")
                with open(diagnostic_path, encoding="utf-8") as stream:
                    diagnostic = json.load(stream)

                self.assertEqual(diagnostic["version"], 1)
                self.assertEqual(diagnostic["triggerStale"]["BTCUSD"]["count"], 1)
                self.assertEqual(diagnostic["triggerStale"]["XAUUSD"]["count"], 1)
                self.assertEqual(
                    diagnostic["triggerStale"]["BTCUSD"]["lastAgeMs"],
                    BASE_MS - btc["entryBarTime"],
                )
                self.assertEqual(
                    diagnostic["triggerStale"]["XAUUSD"]["lastAgeMs"],
                    BASE_MS + 1_000 - gold["entryBarTime"],
                )
                self.assertEqual(
                    diagnostic["triggerStale"]["BTCUSD"]["lastThresholdMs"],
                    TIMEFRAME_MS["M5"] + ENTRY_BAR_GRACE_MS,
                )

                # Un snapshot frais suivant ne réinitialise pas les compteurs du run.
                fresh_btc = valid_payload()
                status, result = self.store.ingest(fresh_btc, INGEST, BASE_MS + 2_000)
                self.assertEqual(status, 200, result)
                with open(diagnostic_path, encoding="utf-8") as stream:
                    after_fresh = json.load(stream)
                self.assertEqual(after_fresh["triggerStale"]["BTCUSD"]["count"], 1)
                self.assertEqual(after_fresh["triggerStale"]["XAUUSD"]["count"], 1)

                rendered = json.dumps(diagnostic)
                self.assertNotIn(INGEST, rendered)
                self.assertNotIn(READ, rendered)
        finally:
            bridge.DIAG_TRIGGER_COUNT.clear()
            bridge.DIAG_TRIGGER_COUNT.update(previous_counts)
            bridge.DIAG_TRIGGER_LAST.clear()
            bridge.DIAG_TRIGGER_LAST.update(previous_last)
            if old_runner_temp is None:
                os.environ.pop("RUNNER_TEMP", None)
            else:
                os.environ["RUNNER_TEMP"] = old_runner_temp
            if previous_started is not None:
                bridge.DIAG_STARTED_AT_MS = previous_started

    def test_stale_or_future_entry_trigger_downgrades_plan_and_keeps_fresh_mtf(self):
        for time_value in (BASE_MS - TIMEFRAME_MS["M5"] - MTF_BAR_GRACE_MS - 1,
                           BASE_MS + MAX_FUTURE_SKEW_MS + 1):
            with self.subTest(entryBarTime=time_value):
                payload = valid_payload()
                payload["entryBarTime"] = time_value
                status, result = self.store.ingest(payload, INGEST, BASE_MS)
                self.assertEqual(status, 200, result)
                self.assertTrue(result["accepted"])
                self.assertEqual(
                    result["diagnosticRejection"]["error"],
                    "stale_or_future_entry_trigger_candle",
                )
                status, data = self.store.read("BTCUSD", BASE_MS + 1_000)
                self.assertEqual(status, 200)
                self.assertTrue(data["ok"])
                self.assertEqual(
                    data["lastRejection"]["error"],
                    "stale_or_future_entry_trigger_candle",
                )
                robot = data["snapshots"]["M1"]["robotV12"]
                self.assertEqual(robot["signal"], "WAIT")
                self.assertFalse(robot["confirmed"])
                self.assertFalse(robot["entryTriggered"])
                self.assertIsNone(robot["entry"])
                self.assertIsNone(robot["sl"])
                self.assertIsNone(robot["tp1"])
                self.assertIsNone(robot["entryBarTime"])

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
