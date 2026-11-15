"""Vérifie que le compte FundedNext répond via MetaApi (AUCUN ordre) : solde, équité, symboles BTC / GOLD / NASDAQ, prix."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import auto_trade as at


def main():
    if not at.TOKEN or not at.COMPTES:
        print("METAAPI ECHEC : jeton ou compte manquant")
        raise SystemExit(1)
    for c in at.COMPTES:
        info = at._api("GET", f"{c}/account-information")
        print(f"METAAPI_COMPTE {c} solde={info.get('balance')} equite={info.get('equity')} levier={info.get('leverage')} plateforme={info.get('platform')}")
        etat = {}
        for m in ("BTC", "GOLD", "NASDAQ"):
            try:
                sym = at.symbole(etat, c, m)
                p = at._api("GET", f"{c}/symbols/{sym}/current-price")
                spec = at._api("GET", f"{c}/symbols/{sym}/specification")
                print(f"METAAPI_SYMBOLE {m} -> {sym} bid={p.get('bid')} ask={p.get('ask')} contrat={spec.get('contractSize')} pas={spec.get('volumeStep')}")
            except Exception as ex:
                print(f"METAAPI_SYMBOLE {m} erreur {ex}")
        print("METAAPI_POSITIONS", len(at._api("GET", f"{c}/positions") or []))
    print("METAAPI_CONNEXION OK")


if __name__ == "__main__":
    main()
