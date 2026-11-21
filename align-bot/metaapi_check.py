"""Vérifie que le compte FundedNext répond via MetaApi (AUCUN ordre) : solde, équité, symboles BTC / GOLD, prix."""
import os, sys, time, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auto_trade as at

TRANSIENT_HTTP = {408, 429, 500, 502, 503, 504}


def api_read_retry(api, method, path, attempts=3, sleep=time.sleep):
    """Retry les erreurs réseau/HTTP transitoires pour les appels MetaApi en lecture seule."""
    for attempt in range(attempts):
        try:
            return api(method, path)
        except urllib.error.HTTPError as exc:
            if exc.code not in TRANSIENT_HTTP or attempt + 1 >= attempts:
                raise
            print(f"METAAPI_RETRY HTTP {exc.code} tentative {attempt + 1}/{attempts}", flush=True)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            if attempt + 1 >= attempts:
                raise
            print(f"METAAPI_RETRY réseau tentative {attempt + 1}/{attempts}: {exc}", flush=True)
        sleep(min(2 ** attempt, 8))
    raise RuntimeError("MetaApi read retry exhausted")


def main():
    if not at.TOKEN or not at.COMPTES:
        print("METAAPI ECHEC : jeton ou compte manquant")
        raise SystemExit(1)
    for c in at.COMPTES:
        info = api_read_retry(at._api, "GET", f"{c}/account-information")
        print(f"METAAPI_COMPTE {c} solde={info.get('balance')} equite={info.get('equity')} levier={info.get('leverage')} plateforme={info.get('platform')}")
        etat = {}
        for m in ("BTC", "GOLD"):
            try:
                sym = at.symbole(etat, c, m)
                p = api_read_retry(at._api, "GET", f"{c}/symbols/{sym}/current-price")
                spec = api_read_retry(at._api, "GET", f"{c}/symbols/{sym}/specification")
                print(f"METAAPI_SYMBOLE {m} -> {sym} bid={p.get('bid')} ask={p.get('ask')} contrat={spec.get('contractSize')} pas={spec.get('volumeStep')}")
            except Exception as ex:
                print(f"METAAPI_SYMBOLE {m} erreur {ex}")
        print("METAAPI_POSITIONS", len(api_read_retry(at._api, "GET", f"{c}/positions") or []))
    print("METAAPI_CONNEXION OK")


if __name__ == "__main__":
    main()
