"""ALIGN — exécution automatique sur Topstep (API TopstepX / ProjectX), micro-contrats MNQ / MGC / MBT.

Différences voulues par Adel (15/11) avec FundedNext :
  • Topstep = futures : TOUTES les positions sont fermées 1 h AVANT la limite Topstep (15 h 10 heure de Chicago),
    annonce sur Telegram et sur le live 1 h avant puis 10 min avant, le bot s'arrête puis reprend après la réouverture
    (17 h heure de Chicago, dimanche soir pour le week-end).
  • FundedNext (MT5, auto_trade.py) peut garder les positions plus longtemps.

Sécurité (codée en dur) : 1 micro-contrat, perte max 100 $ par position, arrêt à -150 $ dans la journée,
arrêt définitif si le solde passe sous le plancher du compte + 100 $. Mode TEST par défaut (TOPSTEP_REEL=1 pour le réel).
"""
import json, os, datetime, urllib.request
from zoneinfo import ZoneInfo

BASE = "https://api.topstepx.com/api"
CHICAGO = ZoneInfo("America/Chicago")
LIMITE_TOPSTEP = datetime.time(15, 10)     # positions à plat obligatoires (heure de Chicago)
FERMETURE_ALIGN = datetime.time(14, 10)    # demande d'Adel : 1 h avant
REOUVERTURE = datetime.time(17, 0)
CONTRATS = 1
PERTE_POSITION_MAX = 100.0
PERTE_JOUR_MAX = 150.0
MARGE_PLANCHER = 100.0
SL_ELARGI = 1.25
SYMBOLES = {"NASDAQ": "MNQ", "GOLD": "MGC", "BTC": "MBT"}   # mêmes marchés que le graphique TradingView

REEL = os.environ.get("TOPSTEP_REEL", "0") == "1"
COMPTE = os.environ.get("TOPSTEP_COMPTE", "")                 # id du compte à trader (ex. 29250754)
PLANCHER = float(os.environ.get("TOPSTEP_PLANCHER", "0") or 0)  # limite de perte max du compte (MLL)


def phase(maintenant=None):
    """'ouvert' | 'annonce_1h' | 'annonce_10min' | 'fermeture' | 'ferme' (heure de Chicago)."""
    t = (maintenant or datetime.datetime.now(datetime.timezone.utc)).astimezone(CHICAGO)
    j, h = t.weekday(), t.time()
    if j == 5 or (j == 6 and h < REOUVERTURE) or (j == 4 and h >= LIMITE_TOPSTEP):
        return "ferme"
    if FERMETURE_ALIGN <= h < REOUVERTURE:
        return "fermeture" if h < LIMITE_TOPSTEP else "ferme"
    m = (datetime.datetime.combine(t.date(), FERMETURE_ALIGN) - datetime.datetime.combine(t.date(), h)).total_seconds() / 60
    if 0 < m <= 10:
        return "annonce_10min"
    if 10 < m <= 60:
        return "annonce_1h"
    return "ouvert"


MESSAGES = {
    "annonce_1h": "⏰ COMPTES TOPSTEP : le marché ferme bientôt\n🔒 Pense à fermer tes positions dans l'heure\n🤖 Le bot ALIGN coupe les siennes et s'arrête de son côté\n🔁 Il reprend après la réouverture\n🟢 Comptes FundedNext / FTMO : on peut garder",
    "annonce_10min": "🚨 COMPTES TOPSTEP : dernières 10 minutes\n🔒 Ferme tes positions maintenant\n🤖 Le bot ALIGN est à plat\n⚠️ Ceci n'est pas un conseil en investissement (DYOR)",
    "reouverture": "🔔 Marché rouvert\n🤖 Le bot ALIGN reprend les positions sur Topstep\n👀 Suis la prochaine entrée en direct",
}
BANDE = {
    "annonce_1h": "⏰ COMPTES FUTURES : LE MARCHÉ FERME DANS 1 H • LE BOT COUPE SES POSITIONS • LIEN EN BIO",
    "annonce_10min": "🚨 COMPTES FUTURES : 10 MIN AVANT LA FERMETURE • TOUT LE MONDE À PLAT • LIEN EN BIO",
    "reouverture": "🔔 LE MARCHÉ ROUVRE • LE BOT REPREND • LIEN EN BIO",
}


def annonces(etat, maintenant=None):
    """Renvoie la liste des annonces à envoyer maintenant (une seule fois par jour et par type)."""
    p = phase(maintenant)
    jour = (maintenant or datetime.datetime.now(datetime.timezone.utc)).astimezone(CHICAGO).strftime("%Y-%m-%d")
    deja = etat.setdefault("topstep_annonces", {})
    cle = p if p in ("annonce_1h", "annonce_10min") else ("reouverture" if p == "ouvert" and deja.get("ferme") else None)
    if p in ("fermeture", "ferme"):
        deja["ferme"] = True
    if not cle or deja.get(cle) == jour:
        return []
    deja[cle] = jour
    if cle == "reouverture":
        deja["ferme"] = False
    return [{"telegram": MESSAGES[cle], "bande": BANDE[cle], "type": cle}]


def ticks(distance, taille_tick, valeur_tick):
    """Nombre de ticks du SL (élargi ×1,25), plafonné à 100 $ de perte pour 1 micro-contrat."""
    t = int(abs(distance) * SL_ELARGI / taille_tick)
    return max(1, min(t, int(PERTE_POSITION_MAX / valeur_tick)))


def _api(chemin, corps, jeton=None):
    h = {"Content-Type": "application/json", "accept": "text/plain"}
    if jeton:
        h["Authorization"] = "Bearer " + jeton
    req = urllib.request.Request(BASE + chemin, data=json.dumps(corps).encode(), headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def connexion():
    r = _api("/Auth/loginKey", {"userName": os.environ.get("TOPSTEP_USERNAME", ""), "apiKey": os.environ.get("TOPSTEP_API_KEY", "")})
    return r.get("token") if r.get("success") else None


def garde_fou(etat, solde):
    jour = datetime.datetime.now(CHICAGO).strftime("%Y-%m-%d")
    j = etat.setdefault("topstep_jour", {})
    if j.get("date") != jour:
        j.update(date=jour, depart=solde, coupe=False)
    if PLANCHER and solde <= PLANCHER + MARGE_PLANCHER:
        return False, "trop près de la limite du compte"
    if j.get("coupe") or solde <= j["depart"] - PERTE_JOUR_MAX:
        j["coupe"] = True
        return False, "perte du jour atteinte"
    return True, "ok"


def contrat(jeton, m):
    cs = _api("/Contract/search", {"live": False, "searchText": SYMBOLES[m]}, jeton).get("contracts") or []
    return next((c for c in cs if c.get("activeContract", True)), cs[0] if cs else None)


def executer(etat, signal, journal=print):
    """signal = {marche, sens, e, sl, tp}. Une position = 1 micro-contrat avec SL et TP posés tout de suite."""
    m = signal["marche"]
    if m not in {k for k, v in (etat.get("auto_marches") or {}).items() if v}:
        return {"ok": False, "raison": f"{m} éteint dans l'admin"}
    if phase() != "ouvert":
        return {"ok": False, "raison": "fermeture du marché proche : pas de nouvelle position"}
    if not COMPTE or not os.environ.get("TOPSTEP_API_KEY"):
        return {"ok": False, "raison": "Topstep pas encore branché"}
    jeton = connexion()
    if not jeton:
        return {"ok": False, "raison": "connexion Topstep refusée"}
    comptes = _api("/Account/search", {"onlyActiveAccounts": True}, jeton).get("accounts") or []
    acc = next((a for a in comptes if str(a.get("id")) == str(COMPTE)), None)
    if not acc or not acc.get("canTrade"):
        return {"ok": False, "raison": "compte Topstep indisponible"}
    ok, raison = garde_fou(etat, float(acc.get("balance", 0)))
    if not ok:
        return {"ok": False, "raison": raison}
    if _api("/Position/searchOpen", {"accountId": int(COMPTE)}, jeton).get("positions"):
        return {"ok": False, "raison": "une position est déjà ouverte"}
    c = contrat(jeton, m)
    if not c:
        return {"ok": False, "raison": "contrat introuvable"}
    ts, tv = float(c["tickSize"]), float(c["tickValue"])
    ordre = {"accountId": int(COMPTE), "contractId": c["id"], "type": 2, "side": 0 if signal["sens"] == "LONG" else 1,
             "size": CONTRATS, "stopLossBracket": {"ticks": ticks(signal["e"] - signal["sl"], ts, tv), "type": 4},
             "takeProfitBracket": {"ticks": max(1, int(abs(signal["tp"] - signal["e"]) / ts)), "type": 1}}
    if not REEL:
        journal(f"TOPSTEP TEST {ordre}")
        return {"ok": True, "test": True, "ordre": ordre}
    r = _api("/Order/place", ordre, jeton)
    journal(f"TOPSTEP {m} {signal['sens']} → {r}")
    return {"ok": bool(r.get("success")), "reponse": r, "ordre": ordre}


def tout_fermer(journal=print):
    """Fermeture obligatoire avant la limite Topstep : ferme chaque position ouverte du compte."""
    if not COMPTE or not os.environ.get("TOPSTEP_API_KEY"):
        return []
    jeton = connexion()
    if not jeton:
        return []
    fait = []
    for p in _api("/Position/searchOpen", {"accountId": int(COMPTE)}, jeton).get("positions") or []:
        if REEL:
            _api("/Position/closeContract", {"accountId": int(COMPTE), "contractId": p["contractId"]}, jeton)
        fait.append(p["contractId"])
    journal(f"TOPSTEP fermeture avant la limite : {fait} ({'réel' if REEL else 'test'})")
    return fait
