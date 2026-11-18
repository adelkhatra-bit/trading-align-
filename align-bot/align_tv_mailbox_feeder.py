#!/usr/bin/env python3
"""ALIGN — relais boîte aux lettres Cloudflare → bridge Python local.

La boîte aux lettres (cloud/align-tv-mailbox/worker.js) ne valide rien : elle garde
le dernier message TradingView par marché. Ce relais le transmet au bridge
align_tv_bridge.py qui tourne dans le runner (127.0.0.1:4100). La seule
validation reste donc celle de BridgeStore : un seul bridge, aucune copie.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
import urllib.request

SYMBOLS = ("BTCUSD", "XAUUSD", "NAS100")
DEFAULT_MAILBOX_URL = "https://align-tv-mailbox.adel-khatra.workers.dev"
_LABEL_LECTURE = b"align-tv-mailbox-read-v1"


def jeton_lecture(env=None):
    """Jeton de lecture de la boîte aux lettres.

    Priorité au secret ALIGN_TV_MAILBOX_TOKEN ; sinon il est DÉRIVÉ (HMAC-SHA256) du secret
    CLOUDFLARE_API_TOKEN, exactement comme le fait le workflow qui le pose dans le Worker.
    Personne n'a donc à copier ce jeton ; il n'est jamais affiché.
    """
    env = os.environ if env is None else env
    direct = str(env.get("ALIGN_TV_MAILBOX_TOKEN") or "").strip()
    if direct:
        return direct
    racine = str(env.get("CLOUDFLARE_API_TOKEN") or "").strip()
    if not racine:
        return ""
    return hmac.new(racine.encode(), _LABEL_LECTURE, hashlib.sha256).hexdigest()


def relay_once(fetch_mailbox, ingest, symbols=SYMBOLS):
    """Transmet le dernier message de chaque marché. Retourne {symbole: statut}."""
    results = {}
    for symbol in symbols:
        try:
            box = fetch_mailbox(symbol)
        except Exception as exc:  # réseau : on le signale, on ne fabrique rien
            results[symbol] = "mailbox_error:" + type(exc).__name__
            continue
        http_status = box.get("_http_status", 200) if isinstance(box, dict) else None
        if http_status != 200:
            # 401 (mauvais jeton), 5xx… : on le dit, on ne le confond pas avec « vide ».
            results[symbol] = "mailbox_http_" + str(http_status)
            continue
        payload = box.get("payload") if box.get("ok") else None
        if not isinstance(payload, dict):
            results[symbol] = "empty"
            continue
        try:
            status, body = ingest(payload)
        except Exception as exc:  # bridge local momentanément indisponible : on réessaiera au cycle suivant
            results[symbol] = "ingest_error:" + type(exc).__name__
            continue
        results[symbol] = "ok" if status == 200 else "rejected:" + str(body.get("error", status))
    return results


def relay_failed(results):
    """Vrai si un marché a échoué (réseau, HTTP, bridge, rejet). « empty » n'est pas une panne."""
    return any(not (v == "ok" or v == "empty") for v in results.values())


# Cloudflare refuse l'agent par défaut « Python-urllib » (HTTP 403) : on s'identifie clairement.
USER_AGENT = "ALIGN-relais/1.0 (+github.com/adelkhatra-bit/trading-align-)"


def _http_json(url, method="GET", data=None, headers=None, timeout=8):
    h = {"User-Agent": USER_AGENT}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read() or b"{}")


def main():
    mailbox_url = (os.environ.get("ALIGN_TV_MAILBOX_URL") or DEFAULT_MAILBOX_URL).rstrip("/")
    mailbox_token = jeton_lecture()
    if "--print-derived-token-to-github-mask" in sys.argv:
        # Utilisé par le workflow : masque la valeur dans les journaux puis l'écrit dans un fichier temporaire.
        print("::add-mask::" + mailbox_token)
        with open(os.environ["ALIGN_TOKEN_FILE"], "w", encoding="utf-8") as f:
            f.write(mailbox_token)
        return 0 if mailbox_token else 1
    local_url = os.environ.get("ALIGN_TV_LOCAL_URL", "http://127.0.0.1:4100").rstrip("/")
    local_ingest = os.environ.get("ALIGN_TV_INGEST_TOKEN", "")
    if not (mailbox_url and mailbox_token and local_ingest):
        print("ÉCHEC: ALIGN_TV_MAILBOX_URL / ALIGN_TV_MAILBOX_TOKEN / ALIGN_TV_INGEST_TOKEN manquants.")
        return 1

    def fetch(symbol):
        status, body = _http_json(mailbox_url + "/mailbox?symbol=" + symbol,
                                  headers={"Authorization": "Bearer " + mailbox_token})
        body = body if isinstance(body, dict) else {}
        body["_http_status"] = status
        return body

    def ingest(payload):
        return _http_json(local_url + "/ingest/" + local_ingest, method="POST",
                          data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})

    interval = float(os.environ.get("ALIGN_TV_RELAY_INTERVAL", "10"))
    once = "--once" in sys.argv
    while True:
        results = relay_once(fetch, ingest)
        print(json.dumps({"relay": results}), flush=True)
        if once:
            return 1 if relay_failed(results) else 0
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
