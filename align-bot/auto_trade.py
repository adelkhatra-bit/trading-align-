"""ALIGN — exécution automatique des positions sur les comptes FundedNext (MT5 via MetaApi).

Demande d'Adel (15/11) : le bot prend la position RÉELLEMENT au moment où il l'annonce,
en respectant les règles du challenge Stellar Lite 2-Step 10K, et ne doit JAMAIS faire sauter un compte.

Sécurité (codée en dur, non modifiable par un message) :
  • perte du jour  : arrêt à -350 $ (règle FundedNext : -400 $/jour)
  • perte totale   : arrêt à -750 $ sous le solde de départ (règle : -800 $ statique)
  • risque         : 0,5 % du solde de départ par position (50 $ sur 10 000 $)
  • positions      : 2 max ouvertes par compte, jamais deux sens opposés sur un même marché
  • mode TEST par défaut : AUTO_TRADE=1 obligatoire pour envoyer de vrais ordres

Secrets GitHub attendus : METAAPI_TOKEN, METAAPI_COMPTES (ids MetaApi séparés par des virgules,
le 1er = compte maître 12140656), METAAPI_REGION (ex. london).
"""
import json, os, time, datetime, urllib.request, urllib.error

SOLDE_DEPART = 10000.0
PERTE_JOUR_MAX = 350.0        # marge de 50 $ sous la règle des 400 $
PERTE_TOTALE_MAX = 750.0      # marge de 50 $ sous la règle des 800 $
RISQUE_PCT = 0.005
POSITIONS_MAX = 2
SL_ELARGI = 1.15              # demande d'Adel : SL un peu plus large quand tout est confirmé

# Symboles du serveur MT5 FundedNext (à confirmer à la 1re connexion via /symbols)
SYMBOLES = {"BTC": "BTCUSD", "GOLD": "XAUUSD", "NASDAQ": "NDX100"}

TOKEN = os.environ.get("METAAPI_TOKEN", "")
COMPTES = [c.strip() for c in os.environ.get("METAAPI_COMPTES", "").split(",") if c.strip()]
REGION = os.environ.get("METAAPI_REGION", "london")
REEL = os.environ.get("AUTO_TRADE", "0") == "1"


def _api(methode, chemin, corps=None):
    url = f"https://mt-client-api-v1.{REGION}.agiliumtrade.ai/users/current/accounts/{chemin}"
    req = urllib.request.Request(url, method=methode, data=json.dumps(corps).encode() if corps is not None else None,
                                 headers={"auth-token": TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode() or "{}")


def marches_actifs(etat):
    """Boutons admin on/off par marché (par défaut : aucun marché tant qu'Adel ne l'a pas allumé)."""
    return {m for m, on in (etat.get("auto_marches") or {}).items() if on}


def garde_fou(etat, compte, equite):
    """Renvoie (autorisé, raison). Coupe tout si une limite approche."""
    jour = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    j = etat.setdefault("auto_jour", {}).setdefault(compte, {})
    if j.get("date") != jour:
        j.update(date=jour, depart=equite, coupe=False)
    if etat.get("auto_coupe_total", {}).get(compte):
        return False, "compte coupé (perte totale)"
    if equite <= SOLDE_DEPART - PERTE_TOTALE_MAX:
        etat.setdefault("auto_coupe_total", {})[compte] = True
        return False, "perte totale proche de la limite"
    if j.get("coupe") or equite <= j["depart"] - PERTE_JOUR_MAX:
        j["coupe"] = True
        return False, "perte du jour proche de la limite"
    return True, "ok"


def volume(e, sl, taille_contrat, pas=0.01, mini=0.01, maxi=5.0):
    """Lots pour risquer 0,5 % du solde de départ entre l'entrée et le SL élargi."""
    dist = abs(e - sl) * SL_ELARGI
    if dist <= 0 or taille_contrat <= 0:
        return 0.0
    lots = (SOLDE_DEPART * RISQUE_PCT) / (dist * taille_contrat)
    lots = int(lots / pas) * pas
    return round(min(maxi, lots), 2) if lots >= mini else 0.0


def sl_elargi(e, sl):
    return e - (e - sl) * SL_ELARGI


def executer(etat, signal, journal=print):
    """signal = {marche, sens: 'LONG'|'SHORT', e, sl, tp}. Renvoie la liste des résultats par compte."""
    m = signal["marche"]
    if m not in marches_actifs(etat):
        return [{"compte": None, "ok": False, "raison": f"{m} éteint dans l'admin"}]
    if not TOKEN or not COMPTES:
        return [{"compte": None, "ok": False, "raison": "MetaApi pas encore branché"}]
    sym, res = SYMBOLES[m], []
    for compte in COMPTES:
        try:
            info = _api("GET", f"{compte}/account-information")
            ok, raison = garde_fou(etat, compte, float(info.get("equity", 0)))
            if not ok:
                res.append({"compte": compte, "ok": False, "raison": raison}); continue
            pos = _api("GET", f"{compte}/positions") or []
            if len(pos) >= POSITIONS_MAX:
                res.append({"compte": compte, "ok": False, "raison": "déjà 2 positions"}); continue
            sens_mt = "POSITION_TYPE_BUY" if signal["sens"] == "LONG" else "POSITION_TYPE_SELL"
            if any(p.get("symbol") == sym and p.get("type") != sens_mt for p in pos):
                res.append({"compte": compte, "ok": False, "raison": "position opposée interdite"}); continue
            spec = _api("GET", f"{compte}/symbols/{sym}/specification")
            lots = volume(signal["e"], signal["sl"], float(spec.get("contractSize", 1)),
                          float(spec.get("volumeStep", 0.01)), float(spec.get("minVolume", 0.01)))
            if not lots:
                res.append({"compte": compte, "ok": False, "raison": "SL trop large pour le risque"}); continue
            ordre = {"actionType": "ORDER_TYPE_BUY" if signal["sens"] == "LONG" else "ORDER_TYPE_SELL", "symbol": sym,
                     "volume": lots, "stopLoss": round(sl_elargi(signal["e"], signal["sl"]), 2),
                     "takeProfit": round(signal["tp"], 2), "comment": "ALIGN"}
            if not REEL:
                journal(f"AUTO_TRADE TEST {compte} {ordre}")
                res.append({"compte": compte, "ok": True, "test": True, "ordre": ordre}); continue
            r = _api("POST", f"{compte}/trade", ordre)
            res.append({"compte": compte, "ok": r.get("stringCode") in ("TRADE_RETCODE_DONE", "ERR_NO_ERROR"), "reponse": r, "ordre": ordre})
        except Exception as ex:
            res.append({"compte": compte, "ok": False, "raison": f"erreur {ex}"})
        time.sleep(0.5)
    journal(f"AUTO_TRADE {m} {signal['sens']} → {res}")
    return res
