"""Vérifie que la clé API TopstepX répond (aucun ordre envoyé) : connexion, comptes, contrats MNQ / MGC / MBT."""
import json, os, urllib.request

BASE = "https://api.topstepx.com/api"


def appel(chemin, corps, jeton=None):
    h = {"Content-Type": "application/json", "accept": "text/plain"}
    if jeton:
        h["Authorization"] = "Bearer " + jeton
    req = urllib.request.Request(BASE + chemin, data=json.dumps(corps).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def main():
    r = appel("/Auth/loginKey", {"userName": os.environ.get("TOPSTEP_USERNAME", ""), "apiKey": os.environ.get("TOPSTEP_API_KEY", "")})
    if not r.get("success"):
        print("TOPSTEP_CONNEXION ECHEC code", r.get("errorCode"), r.get("errorMessage"))
        raise SystemExit(1)
    jeton = r["token"]
    print("TOPSTEP_CONNEXION OK")
    comptes = appel("/Account/search", {"onlyActiveAccounts": True}, jeton).get("accounts") or []
    for c in comptes:
        print(f"TOPSTEP_COMPTE id={c.get('id')} nom={c.get('name')} solde={c.get('balance')} trading={c.get('canTrade')}")
    for s in ("MNQ", "MGC", "MBT"):
        cs = appel("/Contract/search", {"live": False, "searchText": s}, jeton).get("contracts") or []
        print("TOPSTEP_CONTRAT", s, [(c.get("id"), c.get("description"), c.get("tickSize"), c.get("tickValue")) for c in cs[:3]])


if __name__ == "__main__":
    main()
