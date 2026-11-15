"""ALIGN — exécution automatique sur Topstep (API TopstepX / ProjectX), micro-contrats MNQ / MGC / MBT.

Différences voulues par Adel (15/11) avec FundedNext :
  • Topstep = futures : TOUTES les positions sont fermées 1 h AVANT la limite Topstep (15 h 10 heure de Chicago),
    annonce sur Telegram et sur le live 1 h avant puis 10 min avant, le bot s'arrête puis reprend après la réouverture
    (17 h heure de Chicago, dimanche soir pour le week-end).
  • FundedNext (MT5, auto_trade.py) peut garder les positions plus longtemps.

Sécurité (codée en dur) : 1 micro-contrat, perte max 75 $ par position, arrêt à -150 $ dans la journée,
arrêt définitif si le solde passe sous le plancher du compte + 100 $. Mode TEST par défaut (TOPSTEP_REEL=1 pour le réel).
"""
import json, os, time, datetime, urllib.request
from zoneinfo import ZoneInfo

BASE = "https://api.topstepx.com/api"
CHICAGO = ZoneInfo("America/Chicago")
LIMITE_TOPSTEP = datetime.time(15, 10)     # positions à plat obligatoires (heure de Chicago)
FERMETURE_ALIGN = datetime.time(14, 10)    # demande d'Adel : 1 h avant
REOUVERTURE = datetime.time(17, 0)
CONTRATS = 1
PERTE_POSITION_MAX = 75.0      # demande d'Adel : 70-80 $ par position
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
    if etat.get("topstep_pos") or _api("/Position/searchOpen", {"accountId": int(COMPTE)}, jeton).get("positions"):
        return {"ok": False, "raison": "une position est déjà ouverte"}
    c = contrat(jeton, m)
    if not c:
        return {"ok": False, "raison": "contrat introuvable"}
    ts, tv = float(c["tickSize"]), float(c["tickValue"])
    r_ = abs(signal["e"] - signal["sl"])
    rr = abs((signal.get("tp2") or signal["tp"]) - signal["e"]) / r_ if r_ else 0
    if rr < 2:
        return {"ok": False, "raison": "gain visé < 2 × le risque : on n'entre pas"}   # règle d'Adel : 100 $ seulement pour 1:3, 60 $ pour 1:2
    plafond = PERTE_POSITION_MAX if rr >= 3 and not signal.get("contre") else 60.0   # contre-tendance : 60 $ max (16/11)
    tk = min(ticks(signal["e"] - signal["sl"], ts, tv), int(plafond / tv))
    n = nb_contrats(tk, tv) if 2 * tk * tv <= plafond else CONTRATS
    # Demande d'Adel (15/11) : sur Topstep une seule position → pas de TP posé d'avance. Le bot GARDE la position :
    # 2 contrats si le risque tient dans 75 $ → 50 % coupés au TP1 + SL à l'entrée (BE), le reste vise le TP2 ;
    # sinon 1 contrat → au TP1 le SL passe à BE et on garde jusqu'au TP2.
    ordre = {"accountId": int(COMPTE), "contractId": c["id"], "type": 2, "side": 0 if signal["sens"] == "LONG" else 1,
             "size": n, "stopLossBracket": {"ticks": tk, "type": 4}}
    try:
        fut = dernier_prix(jeton, c["id"])
    except Exception:
        fut = None
    ecart = (fut - signal["e"]) if fut else 0.0
    d = 1 if signal["sens"] == "LONG" else -1
    etat["topstep_pos"] = {"marche": m, "d": d, "n": n, "etape": 0, "contractId": c["id"], "tick": ts,
                           "e": arrondi_tick(signal["e"] + ecart, ts), "sl": arrondi_tick(signal["e"] + ecart - d * tk * ts, ts),
                           "tp1": arrondi_tick(signal["tp"] + ecart, ts),
                           "tp2": arrondi_tick((signal.get("tp2") or signal["tp"] + (signal["tp"] - signal["e"])) + ecart, ts),
                           "test": not REEL}
    if not REEL:
        journal(f"TOPSTEP TEST {ordre} plan {etat['topstep_pos']}")
        return {"ok": True, "test": True, "ordre": ordre}
    r = _api("/Order/place", ordre, jeton)
    journal(f"TOPSTEP {m} {signal['sens']} → {r}")
    if not r.get("success"):
        etat.pop("topstep_pos", None)
    return {"ok": bool(r.get("success")), "reponse": r, "ordre": ordre}


def nb_contrats(tk, valeur_tick):
    """2 micro-contrats seulement si le risque total (2 × SL) reste dans les 75 $ par position, sinon 1."""
    return 2 if 2 * tk * valeur_tick <= PERTE_POSITION_MAX else CONTRATS


def dernier_prix(jeton, contrat_id):
    fin = datetime.datetime.now(datetime.timezone.utc)
    r = _api("/History/retrieveBars", {"contractId": contrat_id, "live": False, "unit": 2, "unitNumber": 1, "limit": 5,
                                        "includePartialBar": True,
                                        "startTime": (fin - datetime.timedelta(minutes=30)).isoformat(),
                                        "endTime": fin.isoformat()}, jeton)
    barres = r.get("bars") or []
    return float(max(barres, key=lambda b: str(b.get("t", "")))["c"]) if barres else None


def _stop_ouvert(jeton, contrat_id):
    for o in _api("/Order/searchOpen", {"accountId": int(COMPTE)}, jeton).get("orders") or []:
        if o.get("contractId") == contrat_id and o.get("type") == 4:
            return o
    return None


def gerer(etat, prix=None, journal=print):
    """À chaque tour du bot : gère la position Topstep ouverte (TP1 → 50 % coupés + BE, TP2 → tout fermé, SL → fin).
    Renvoie les messages à envoyer au propriétaire. En mode TEST, rien n'est envoyé à Topstep, on suit seulement le plan."""
    pos = etat.get("topstep_pos")
    if not pos:
        return []
    p = prix if prix is not None else prix_futures(pos["marche"])
    if p is None:
        return []
    d, m, msgs = pos["d"], pos["marche"], []
    jeton = connexion() if REEL else None
    if REEL and jeton and not _api("/Position/searchOpen", {"accountId": int(COMPTE)}, jeton).get("positions"):
        etat.pop("topstep_pos", None)
        return [f"🏁 Topstep {m} : position terminée (SL / BE touché ou fermée)"]
    if (p - pos["sl"]) * d <= 0:
        etat.pop("topstep_pos", None)
        return [f"🛑 Topstep {m} : {'BE touché, 0 risque' if pos['etape'] else 'SL touché'} ({'test' if not REEL else 'réel'})"]
    if pos["etape"] == 0 and (p - pos["tp1"]) * d >= 0:
        if REEL and jeton:
            if pos["n"] > 1:
                _api("/Position/partialCloseContract", {"accountId": int(COMPTE), "contractId": pos["contractId"], "size": pos["n"] // 2}, jeton)
            o = _stop_ouvert(jeton, pos["contractId"])
            if o:
                _api("/Order/modify", {"accountId": int(COMPTE), "orderId": o["id"], "stopPrice": pos["e"]}, jeton)
        pos.update(etape=1, sl=pos["e"])
        msgs.append(f"🎯 Topstep {m} : TP1 touché → " + ("50 % encaissés + " if pos["n"] > 1 else "") + f"SL à l'entrée (BE), on vise le TP2 ({'test' if not REEL else 'réel'})")
    elif pos["etape"] == 1 and (p - pos["tp2"]) * d >= 0:
        if REEL and jeton:
            _api("/Position/closeContract", {"accountId": int(COMPTE), "contractId": pos["contractId"]}, jeton)
        etat.pop("topstep_pos", None)
        msgs.append(f"🏆 Topstep {m} : TP2 touché, tout est encaissé ({'test' if not REEL else 'réel'})")
    for x in msgs:
        journal(x)
    return msgs


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


# ── Prix Topstep pour les utilisateurs (demande d'Adel 15/11) ──────────────────────────────────────────
# Le graphique TradingView (CFD : BTCUSD / XAUUSD / NAS100) et les futures Topstep (MBT / MGC / MNQ) n'ont pas
# le même prix (écart de base). Le bot lit le VRAI dernier prix du micro-contrat et décale les niveaux du plan
# du même écart : l'utilisateur qui a choisi « Topstep » reçoit des niveaux directement utilisables.
TICKS = {"NASDAQ": 0.25, "GOLD": 0.1, "BTC": 5.0}
VALEUR_TICK = {"NASDAQ": 0.5, "GOLD": 1.0, "BTC": 0.5}   # $ par tick pour 1 micro-contrat (MNQ / MGC / MBT)
RISQUE_MAX_CONSEILLE = 100.0                              # règle d'Adel (15/11) : jamais plus de 100 $ de SL par position (compte 100K)


def risque_dollars(m, e, sl, contrats=1):
    """Perte en $ si le SL est touché, pour N micro-contrats."""
    return abs(e - sl) / TICKS.get(m, 1) * VALEUR_TICK.get(m, 1) * contrats
_CACHE_PRIX = {}


def prix_futures(m, maintenant=None):
    """Dernier prix du micro-contrat Topstep du marché (cache 60 s). None si Topstep n'est pas branché."""
    t = maintenant or time.time()
    c = _CACHE_PRIX.get(m)
    if c and t - c[0] < 60:
        return c[1]
    if m not in SYMBOLES or not os.environ.get("TOPSTEP_API_KEY"):
        return None
    jeton = connexion()
    if not jeton:
        return None
    k = contrat(jeton, m)
    if not k:
        return None
    fin = datetime.datetime.now(datetime.timezone.utc)
    r = _api("/History/retrieveBars", {"contractId": k["id"], "live": False, "unit": 2, "unitNumber": 1, "limit": 5,
                                        "includePartialBar": True,
                                        "startTime": (fin - datetime.timedelta(minutes=30)).isoformat(),
                                        "endTime": fin.isoformat()}, jeton)
    barres = r.get("bars") or []
    if not barres:
        return None
    p = float(max(barres, key=lambda b: str(b.get("t", "")))["c"])
    _CACHE_PRIX[m] = (t, p)
    return p


def arrondi_tick(v, tick):
    return round(round(v / tick) * tick, 4)


def niveaux_futures(m, prix_graphique, niveaux, prix_fut):
    """Décale chaque niveau {nom: prix TradingView} de l'écart futures − graphique, arrondi au tick du contrat."""
    if not prix_fut or not prix_graphique:
        return None
    ecart = prix_fut - prix_graphique
    tick = TICKS.get(m, 0.01)
    return {k: arrondi_tick(v + ecart, tick) for k, v in niveaux.items() if v}


def profit_ouvert(etat, m):
    """Gain/perte EN COURS (en $) de la position Topstep réelle du marché (prix du contrat − entrée)."""
    pos = etat.get("topstep_pos")
    if not (REEL and pos and pos.get("marche") == m):
        return None
    p = prix_futures(m)
    if p is None:
        return None
    restant = pos["n"] - (pos["n"] // 2 if pos.get("etape") else 0)
    return round((p - pos["e"]) * pos["d"] / TICKS.get(m, 1) * VALEUR_TICK.get(m, 1) * restant, 2)
