#!/usr/bin/env python3
"""ALIGN — relais boîte aux lettres Cloudflare → bridge Python local.

La boîte aux lettres (cloud/align-tv-mailbox/worker.js) ne valide rien : elle garde
le dernier message TradingView par marché. Ce relais le transmet au bridge
align_tv_bridge.py qui tourne dans le runner (127.0.0.1:4100). La seule
validation reste donc celle de BridgeStore : un seul bridge, aucune copie.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

SYMBOLS = ("BTCUSD", "XAUUSD", "NAS100")


def relay_once(fetch_mailbox, ingest, symbols=SYMBOLS):
    """Transmet le dernier message de chaque marché. Retourne {symbole: statut}."""
    results = {}
    for symbol in symbols:
        try:
            box = fetch_mailbox(symbol)
        except Exception as exc:  # réseau : on le signale, on ne fabrique rien
            results[symbol] = "mailbox_error:" + type(exc).__name__
            continue
        payload = box.get("payload") if isinstance(box, dict) and box.get("ok") else None
        if not isinstance(payload, dict):
            results[symbol] = "empty"
            continue
        status, body = ingest(payload)
        results[symbol] = "ok" if status == 200 else "rejected:" + str(body.get("error", status))
    return results


def _http_json(url, method="GET", data=None, headers=None, timeout=8):
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


def main():
    mailbox_url = os.environ.get("ALIGN_TV_MAILBOX_URL", "").rstrip("/")
    mailbox_token = os.environ.get("ALIGN_TV_MAILBOX_TOKEN", "")
    local_url = os.environ.get("ALIGN_TV_LOCAL_URL", "http://127.0.0.1:4100").rstrip("/")
    local_ingest = os.environ.get("ALIGN_TV_INGEST_TOKEN", "")
    if not (mailbox_url and mailbox_token and local_ingest):
        print("ÉCHEC: ALIGN_TV_MAILBOX_URL / ALIGN_TV_MAILBOX_TOKEN / ALIGN_TV_INGEST_TOKEN manquants.")
        return 1

    def fetch(symbol):
        _, body = _http_json(mailbox_url + "/mailbox?symbol=" + symbol,
                             headers={"Authorization": "Bearer " + mailbox_token})
        return body

    def ingest(payload):
        return _http_json(local_url + "/ingest/" + local_ingest, method="POST",
                          data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})

    interval = float(os.environ.get("ALIGN_TV_RELAY_INTERVAL", "10"))
    once = "--once" in sys.argv
    while True:
        print(json.dumps({"relay": relay_once(fetch, ingest)}), flush=True)
        if once:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
