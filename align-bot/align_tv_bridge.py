#!/usr/bin/env python3
"""Isolated TradingView -> ALIGN ROBOT V12 bridge (stdlib only).

The service listens on loopback port 4100 by default. Expose it only through a
separate HTTPS tunnel; do not reuse the legacy server on port 4000.
"""
from __future__ import annotations

import hmac
import json
import math
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

SOURCE = "ALIGN_MTF_PRO_V25"
ALLOWED_SYMBOLS = {"BTCUSD", "XAUUSD", "NAS100"}
ACTIVE_TIMEFRAMES = {"M1", "M5", "M15", "M30", "H1", "H2", "H4", "D1", "W1"}
REQUIRED_TIMEFRAMES = ("M5", "M15", "H1", "H4", "D1", "W1")
TIMEFRAME_MS = {
    "M1": 60_000,
    "M5": 300_000,
    "M15": 900_000,
    "M30": 1_800_000,
    "H1": 3_600_000,
    "H2": 7_200_000,
    "H4": 14_400_000,
    "D1": 86_400_000,
    "W1": 604_800_000,
}
ACTIVE_MAX_AGE_MS = 30_000
MTF_BAR_GRACE_MS = 30_000
MAX_FUTURE_SKEW_MS = 5_000
MAX_BODY_BYTES = 32_768
TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
FORBIDDEN_PORTS = {3000, 4000, 5001}


def _finite_number(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _epoch_ms(value):
    number = _finite_number(value)
    if number is None or number <= 0:
        return None
    if number < 100_000_000_000:
        number *= 1000
    return int(number)


def _iso_utc(epoch_ms):
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _direction(value):
    if isinstance(value, bool):
        return None
    number = _finite_number(value)
    if number is None or number not in (-1, 0, 1):
        return None
    return int(number)


def _text(value, limit=120):
    if not isinstance(value, str):
        return ""
    return value.strip()[:limit]


def _bool(value):
    return value is True


def _safe_robot(payload, price, received_at_ms):
    """Normalize the active Pine plan. Invalid levels become WAIT, never orders."""
    signal = _text(payload.get("signal") or payload.get("verdict"), 24).upper()
    if signal not in {"LONG", "SHORT", "WAIT"}:
        signal = "WAIT"

    entry = _finite_number(payload.get("entry"))
    stop = _finite_number(payload.get("sl"))
    tp1 = _finite_number(payload.get("tp1", payload.get("tp")))
    tp2 = _finite_number(payload.get("tp2"))
    if tp2 is None:
        tp2 = tp1

    plan_valid = signal in {"LONG", "SHORT"} and None not in (entry, stop, tp1, tp2)
    if plan_valid and signal == "LONG":
        plan_valid = stop < entry < tp1 and tp2 >= tp1
    elif plan_valid and signal == "SHORT":
        plan_valid = tp1 < entry < stop and tp2 <= tp1
    # Reject implausibly distant plans without discarding the fresh market snapshot.
    if plan_valid and abs(entry - price) / price > 0.10:
        plan_valid = False

    if not plan_valid:
        signal = "WAIT"
        entry = stop = tp1 = tp2 = None

    lectures = {}
    for key in ("lecture_1m", "lecture_5m", "lecture_15m", "lecture_60m"):
        value = _text(payload.get(key), 16).upper()
        if value not in {"LONG", "SHORT", "NEUTRAL"}:
            value = ""
        lectures[key] = value

    rsi_fields = {}
    for key in ("rsi_1m", "rsi_5m", "rsi_15m", "rsi_60m"):
        value = _finite_number(payload.get(key))
        rsi_fields[key] = value if value is not None and 0 <= value <= 100 else None

    macro_bull = _finite_number(payload.get("macro_bull"))
    macro_bear = _finite_number(payload.get("macro_bear"))
    long_score = _finite_number(payload.get("long_score"))
    short_score = _finite_number(payload.get("short_score"))
    rr_ratio = _finite_number(payload.get("rrRatio"))

    robot = {
        "source": SOURCE,
        "signal": signal,
        "verdict": _text(payload.get("verdict") or signal, 120),
        "confirmed": _bool(payload.get("confirmed")) and plan_valid and not _bool(payload.get("scalp_inverse")),
        "candle_confirmed": _bool(payload.get("candle_confirmed")),
        "bar_confirmed": _bool(payload.get("bar_confirmed")),
        "scalp_inverse": _bool(payload.get("scalp_inverse")),
        "strategy": _text(payload.get("strategy"), 24),
        "entry": entry,
        "sl": stop,
        "tp": tp1,
        "tp1": tp1,
        "tp2": tp2,
        "rrRatio": rr_ratio,
        "macro_bull": int(macro_bull) if macro_bull is not None else None,
        "macro_bear": int(macro_bear) if macro_bear is not None else None,
        "long_score": long_score,
        "short_score": short_score,
        "anticipation": _text(payload.get("anticipation"), 32),
        "anticipation_force": _finite_number(payload.get("anticipation_force")),
        "zone_proche": _text(payload.get("zone_proche"), 40),
        "volume_etat": _text(payload.get("volume"), 24),
        "rsi_etat": _text(payload.get("rsi_etat"), 24),
        **lectures,
        **rsi_fields,
        "receivedAt": _iso_utc(received_at_ms),
        "ageMs": 0,
    }
    return robot


class BridgeStore:
    """Thread-safe in-memory snapshots; restarts intentionally clear stale state."""

    def __init__(self, ingest_token: str, read_token: str):
        self.ingest_token = ingest_token
        self.read_token = read_token
        self._lock = threading.RLock()
        self._symbols = {}

    def ingest(self, payload, path_token, now_ms=None):
        now_ms = int(now_ms if now_ms is not None else time.time() * 1000)
        if not hmac.compare_digest(str(path_token).encode(), self.ingest_token.encode()):
            return 401, {"ok": False, "error": "unauthorized"}
        if not isinstance(payload, dict) or payload.get("source") != SOURCE:
            return 202, {"ok": True, "ignored": True, "reason": "not_an_align_snapshot"}

        symbol = _text(payload.get("symbol"), 16).upper()
        timeframe = _text(payload.get("timeframe"), 8).upper()
        if symbol not in ALLOWED_SYMBOLS:
            return 400, {"ok": False, "error": "unsupported_symbol"}
        if timeframe not in ACTIVE_TIMEFRAMES:
            return 400, {"ok": False, "error": "unsupported_active_timeframe"}

        price = _finite_number(payload.get("price"))
        source_timestamp = _epoch_ms(payload.get("timestamp"))
        if price is None or price <= 0 or source_timestamp is None:
            return 400, {"ok": False, "error": "invalid_price_or_timestamp"}
        source_age = now_ms - source_timestamp
        if source_age < -MAX_FUTURE_SKEW_MS or source_age > ACTIVE_MAX_AGE_MS:
            return 400, {"ok": False, "error": "stale_or_future_snapshot"}

        mtf = payload.get("mtf")
        if not isinstance(mtf, dict):
            return 400, {"ok": False, "error": "missing_mtf_snapshots"}
        required = set(REQUIRED_TIMEFRAMES) | {timeframe}
        normalized_mtf = {}
        for tf in required:
            item = mtf.get(tf)
            if not isinstance(item, dict):
                return 400, {"ok": False, "error": "missing_mtf_timeframe", "timeframe": tf}
            direction = _direction(item.get("direction"))
            rsi = _finite_number(item.get("rsi"))
            bar_time = _epoch_ms(item.get("bar_time"))
            if direction is None or rsi is None or not 0 <= rsi <= 100 or bar_time is None:
                return 400, {"ok": False, "error": "invalid_mtf_snapshot", "timeframe": tf}
            bar_age = now_ms - bar_time
            if bar_age < -MAX_FUTURE_SKEW_MS:
                return 400, {"ok": False, "error": "future_mtf_bar", "timeframe": tf}
            max_bar_age = TIMEFRAME_MS[tf] + MTF_BAR_GRACE_MS
            if bar_age > max_bar_age:
                return 400, {
                    "ok": False,
                    "error": "stale_mtf_bar",
                    "timeframe": tf,
                    "ageMs": bar_age,
                    "maxAgeMs": max_bar_age,
                }
            normalized_mtf[tf] = {"direction": direction, "rsi": rsi, "barTime": bar_time}

        plan_timeframe = _text(payload.get("planTimeframe"), 8).upper()
        entry_timeframe = _text(payload.get("entryTimeframe"), 8).upper()
        strategy = _text(payload.get("strategy"), 24).upper()
        expected_entry_tf = {"SCALPING": "M1", "DAY": "M5", "SWING": "H1"}.get(strategy)
        entry_zone_low = _finite_number(payload.get("entryZoneLow"))
        entry_zone_high = _finite_number(payload.get("entryZoneHigh"))
        entry_decision = _finite_number(payload.get("entryDecision"))
        signal_direction = _direction(payload.get("signal"))
        if plan_timeframe != "M15":
            return 400, {"ok": False, "error": "unsupported_plan_timeframe"}
        if expected_entry_tf is None or entry_timeframe != expected_entry_tf:
            return 400, {"ok": False, "error": "entry_timeframe_strategy_mismatch"}
        if entry_zone_low is None or entry_zone_high is None or entry_decision is None:
            return 400, {"ok": False, "error": "missing_entry_zone"}
        if not entry_zone_low < entry_decision < entry_zone_high:
            return 400, {"ok": False, "error": "invalid_entry_zone_geometry"}
        if signal_direction not in (-1, 1):
            return 400, {"ok": False, "error": "invalid_entry_direction"}
        plan_entry = _finite_number(payload.get("entry"))
        plan_sl = _finite_number(payload.get("sl"))
        if plan_entry is None or plan_sl is None:
            return 400, {"ok": False, "error": "missing_entry_or_stop"}
        if signal_direction == 1 and not (plan_sl < plan_entry and entry_zone_low < entry_decision < entry_zone_high and plan_sl < entry_zone_low < entry_zone_high <= plan_entry):
            return 400, {"ok": False, "error": "long_entry_zone_vs_stop_mismatch"}
        if signal_direction == -1 and not (plan_entry < plan_sl and entry_zone_low < entry_decision < entry_zone_high and plan_entry <= entry_zone_low < entry_zone_high < plan_sl):
            return 400, {"ok": False, "error": "short_entry_zone_vs_stop_mismatch"}

        robot = _safe_robot(payload, price, now_ms)
        robot.update({
            "planTimeframe": plan_timeframe,
            "entryTimeframe": entry_timeframe,
            "entryZoneLow": entry_zone_low,
            "entryZoneHigh": entry_zone_high,
            "entryDecision": entry_decision,
        })
        source_iso = _iso_utc(source_timestamp)
        snapshots = {}
        for tf in REQUIRED_TIMEFRAMES:
            item = normalized_mtf[tf]
            snapshots[tf] = {
                "fresh": True,
                "updatedAt": source_timestamp,
                "timestamp": source_iso,
                "barTime": item["barTime"],
                "direction": item["direction"],
                "rsi": item["rsi"],
            }
        active_item = normalized_mtf[timeframe]
        active_snapshot = snapshots.get(timeframe, {})
        active_snapshot.update({
            "fresh": True,
            "updatedAt": source_timestamp,
            "timestamp": source_iso,
            "barTime": active_item["barTime"],
            "direction": active_item["direction"],
            "rsi": active_item["rsi"],
            "price": price,
            "confirmed": robot["confirmed"],
            "robotV12": robot,
        })
        snapshots[timeframe] = active_snapshot

        state = {
            "symbol": symbol,
            "activeTimeframe": timeframe,
            "receivedAtMs": now_ms,
            "sourceTimestamp": source_timestamp,
            "snapshots": snapshots,
        }
        with self._lock:
            self._symbols[symbol] = state
        return 200, {
            "ok": True,
            "accepted": True,
            "symbol": symbol,
            "activeTimeframe": timeframe,
            "receivedTimeframes": list(snapshots.keys()),
        }

    def read(self, symbol, now_ms=None):
        now_ms = int(now_ms if now_ms is not None else time.time() * 1000)
        symbol = _text(symbol, 16).upper()
        if symbol not in ALLOWED_SYMBOLS:
            return 400, {"ok": False, "error": "unsupported_symbol"}
        with self._lock:
            state = self._symbols.get(symbol)
            if state is None:
                return 200, {
                    "ok": False,
                    "symbol": symbol,
                    "activeTimeframe": None,
                    "activeTimeframeFresh": False,
                    "activeTimeframeAgeMs": None,
                    "receivedTimeframes": [],
                    "snapshots": {},
                }
            snapshots = {key: dict(value) for key, value in state["snapshots"].items()}
            active_tf = state["activeTimeframe"]

        active_age = now_ms - int(state["sourceTimestamp"])
        active_fresh = 0 <= active_age <= ACTIVE_MAX_AGE_MS
        for tf, snap in snapshots.items():
            # Freshness follows the TradingView candle's own open time, not
            # the receipt time of a newer payload carrying the same candle.
            age = now_ms - int(snap.get("barTime", 0))
            max_age = TIMEFRAME_MS.get(tf, 60_000) + MTF_BAR_GRACE_MS
            snap["fresh"] = -MAX_FUTURE_SKEW_MS <= age <= max_age
            snap["ageMs"] = max(0, age)
        required_fresh = all(snapshots.get(tf, {}).get("fresh") is True for tf in REQUIRED_TIMEFRAMES)
        active_snapshot_fresh = snapshots.get(active_tf, {}).get("fresh") is True
        return 200, {
            "ok": active_fresh and active_snapshot_fresh and required_fresh,
            "symbol": symbol,
            "activeTimeframe": active_tf,
            "activeTimeframeFresh": active_fresh,
            "activeTimeframeAgeMs": max(0, active_age),
            "receivedTimeframes": list(snapshots.keys()),
            "snapshots": snapshots,
        }

    def health(self, now_ms=None):
        now_ms = int(now_ms if now_ms is not None else time.time() * 1000)
        with self._lock:
            states = list(self._symbols.values())
        connected = any(0 <= now_ms - state["sourceTimestamp"] <= ACTIVE_MAX_AGE_MS for state in states)
        return {
            "ok": True,
            "service": "ALIGN TradingView ROBOT V12 bridge",
            "connected": connected,
            "symbols": len(states),
            "port": int(os.environ.get("ALIGN_TV_BRIDGE_PORT", "4100")),
        }


def make_handler(store: BridgeStore):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ALIGN-TV-Bridge/1.0"

        def _send(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            parsed = urlsplit(self.path)
            if parsed.path == "/health":
                self._send(200, store.health())
                return
            if parsed.path == "/bridge/robot-v12/mtf":
                auth = self.headers.get("Authorization", "")
                prefix = "Bearer "
                supplied = auth[len(prefix):].strip() if auth.startswith(prefix) else ""
                if not supplied or not hmac.compare_digest(supplied.encode(), store.read_token.encode()):
                    self._send(401, {"ok": False, "error": "unauthorized"})
                    return
                query = parse_qs(parsed.query)
                symbol = (query.get("symbol") or [""])[0]
                status, payload = store.read(symbol)
                self._send(status, payload)
                return
            self._send(404, {"ok": False, "error": "not_found"})

        def do_POST(self):  # noqa: N802
            parsed = urlsplit(self.path)
            parts = parsed.path.strip("/").split("/")
            if len(parts) != 2 or parts[0] != "ingest":
                self._send(404, {"ok": False, "error": "not_found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send(400, {"ok": False, "error": "invalid_content_length"})
                return
            if length <= 0 or length > MAX_BODY_BYTES:
                self._send(413, {"ok": False, "error": "invalid_body_size"})
                return
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                # Existing human-readable Pine alert() messages share the alert stream.
                # Ignore them without logging their contents; only the JSON marker is ingested.
                self._send(202, {"ok": True, "ignored": True, "reason": "non_json_alert"})
                return
            status, result = store.ingest(payload, parts[1])
            self._send(status, result)

        def log_message(self, fmt, *args):
            # Never log request paths: /ingest/<token> contains the private ingress token.
            method = getattr(self, "command", "?")
            sys.stderr.write(f"ALIGN_TV_BRIDGE request method={method} status={getattr(self, '_last_response_code', 'handled')}\n")

        def send_response(self, code, message=None):
            self._last_response_code = code
            return super().send_response(code, message)

    return Handler


def main():
    ingest_token = os.environ.get("ALIGN_TV_INGEST_TOKEN", "").strip()
    read_token = os.environ.get("ALIGN_TV_READ_TOKEN", "").strip()
    if (
        not TOKEN_PATTERN.fullmatch(ingest_token)
        or not TOKEN_PATTERN.fullmatch(read_token)
        or hmac.compare_digest(ingest_token.encode(), read_token.encode())
    ):
        print("ALIGN_TV_BRIDGE_ERROR: configure two different random tokens (32-128 URL-safe characters).", file=sys.stderr)
        return 2
    host = "127.0.0.1"
    port = int(os.environ.get("ALIGN_TV_BRIDGE_PORT", "4100"))
    if port in FORBIDDEN_PORTS or not 1 <= port <= 65535:
        print("ALIGN_TV_BRIDGE_ERROR: port is reserved or invalid; use the dedicated ALIGN bridge port (default 4100).", file=sys.stderr)
        return 2
    store = BridgeStore(ingest_token, read_token)
    server = ThreadingHTTPServer((host, port), make_handler(store))
    print(f"ALIGN_TV_BRIDGE_READY host={host} port={port} secrets_configured=true", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
