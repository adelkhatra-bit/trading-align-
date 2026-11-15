"""ALIGN — exécution automatique des positions sur les comptes FundedNext (MT5 via MetaApi).

Demande d'Adel (15/11) : le bot prend la position RÉELLEMENT au moment où il l'annonce,
en respectant les règles du challenge Stellar Lite 2-Step 10K, et ne doit JAMAIS faire sauter un compte.

Sécurité (codée en dur, non modifiable par un message) :
  • perte du jour  : arrêt à -350 $ (règle FundedNext : -400 $/jour)
  • perte totale   : arrêt à -750 $ sous le solde de départ (règle : -800 $ statique)
  • risque         : 75 $ par position (demande d'Adel : SL plus loin, derrière la mèche, on attend la confirmation)
  • positions      : 2 max ouvertes par compte, jamais deux sens opposés sur un même marché
  • mode TEST par défaut : AUTO_TRADE=1 obligatoire pour envoyer de vrais ordres

Secrets GitHub attendus : METAAPI_TOKEN, METAAPI_COMPTES (ids MetaApi séparés par des virgules,
le 1er = compte maître 12140656), METAAPI_REGION (ex. london).
"""
import json, os, time, datetime, urllib.request, urllib.error

SOLDE_DEPART = 10000.0
PERTE_JOUR_MAX = 350.0        # marge de 50 $ sous la règle des 400 $
PERTE_TOTALE_MAX = 750.0      # marge de 50 $ sous la règle des 800 $
RISQUE_DOLLARS = 50.0        # 1re entrée = la moitié du budget (stratégie rachats d'Adel, 15/11)
RISQUE_TOTAL_MAX = 100.0     # règle d'Adel : TOUTES les positions du plan ensemble ne perdent jamais plus de 100 $
RISQUE_RACHAT = 25.0         # chaque rachat sur repli ajoute au plus 25 $ de risque
REPLI_RACHAT = 0.4           # on rachète quand le prix a reculé de 40 % du chemin entrée → SL (dans le sens du plan)
POSITIONS_MAX = 4            # 1 entrée + jusqu'à 3 rachats, toujours dans le même sens
SL_ELARGI = 1.25              # demande d'Adel : SL plus large, au-delà de la mèche

# Mêmes marchés que le graphique TradingView d'Adel (CRYPTO:BTCUSD, FOREXCOM:XAUUSD, FX:NAS100).
# Le nom exact sur le serveur MT5 FundedNext est retrouvé tout seul dans cette liste.
SYMBOLES = {"BTC": ["BTCUSD", "BTCUSD.", "BTCUSDm"], "GOLD": ["XAUUSD", "XAUUSD.", "GOLD"],
            "NASDAQ": ["NDX100", "NAS100", "US100", "USTEC", "NDX100."]}

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


def volume(e, sl, taille_contrat, pas=0.01, mini=0.01, maxi=5.0, risque=None, elargi=True):
    """Lots pour risquer `risque` $ (RISQUE_DOLLARS par défaut) entre l'entrée et le SL (élargi pour la 1re entrée)."""
    dist = abs(e - sl) * (SL_ELARGI if elargi else 1)
    if dist <= 0 or taille_contrat <= 0:
        return 0.0
    lots = (RISQUE_DOLLARS if risque is None else risque) / (dist * taille_contrat)
    lots = int(lots / pas) * pas
    return round(min(maxi, lots), 2) if lots >= mini else 0.0


def sl_elargi(e, sl):
    return e - (e - sl) * SL_ELARGI


def symbole(etat, compte, m):
    """Nom du marché sur le serveur MT5 (mémorisé après la 1re recherche)."""
    cache = etat.setdefault("auto_symboles", {}).setdefault(compte, {})
    if m not in cache:
        dispo = set(_api("GET", f"{compte}/symbols") or [])
        cache[m] = next((s for s in SYMBOLES[m] if s in dispo), SYMBOLES[m][0])
    return cache[m]


def niveaux_mt5(signal, prix):
    """Le prix MT5 (CFD) n'est pas exactement celui de TradingView : on garde les mêmes DISTANCES
    (SL élargi et TP) mais on les pose à partir du vrai prix d'exécution → aucune confusion de niveaux."""
    d_sl = abs(signal["e"] - signal["sl"]) * SL_ELARGI
    d_tp = abs(signal["tp"] - signal["e"])
    if signal["sens"] == "LONG":
        return round(prix - d_sl, 2), round(prix + d_tp, 2)
    return round(prix + d_sl, 2), round(prix - d_tp, 2)


def executer(etat, signal, journal=print):
    """signal = {marche, sens: 'LONG'|'SHORT', e, sl, tp}. Renvoie la liste des résultats par compte."""
    m = signal["marche"]
    if m not in marches_actifs(etat):
        return [{"compte": None, "ok": False, "raison": f"{m} éteint dans l'admin"}]
    if not TOKEN or not COMPTES:
        return [{"compte": None, "ok": False, "raison": "MetaApi pas encore branché"}]
    res = []
    for compte in COMPTES:
        try:
            info = _api("GET", f"{compte}/account-information")
            ok, raison = garde_fou(etat, compte, float(info.get("equity", 0)))
            if not ok:
                res.append({"compte": compte, "ok": False, "raison": raison}); continue
            sym = symbole(etat, compte, m)
            pos = _api("GET", f"{compte}/positions") or []
            if len(pos) >= POSITIONS_MAX:
                res.append({"compte": compte, "ok": False, "raison": "déjà 4 positions"}); continue
            sens_mt = "POSITION_TYPE_BUY" if signal["sens"] == "LONG" else "POSITION_TYPE_SELL"
            if any(p.get("symbol") == sym and p.get("type") != sens_mt for p in pos):
                res.append({"compte": compte, "ok": False, "raison": "position opposée interdite"}); continue
            spec = _api("GET", f"{compte}/symbols/{sym}/specification")
            lots = volume(signal["e"], signal["sl"], float(spec.get("contractSize", 1)),
                          float(spec.get("volumeStep", 0.01)), float(spec.get("minVolume", 0.01)))
            if not lots:
                res.append({"compte": compte, "ok": False, "raison": "SL trop large pour le risque"}); continue
            px = _api("GET", f"{compte}/symbols/{sym}/current-price")
            prix = float(px["ask"] if signal["sens"] == "LONG" else px["bid"])
            sl_mt5, tp_mt5 = niveaux_mt5(signal, prix)
            ordre = {"actionType": "ORDER_TYPE_BUY" if signal["sens"] == "LONG" else "ORDER_TYPE_SELL", "symbol": sym,
                     "volume": lots, "stopLoss": sl_mt5, "takeProfit": tp_mt5, "comment": "ALIGN"}
            if not REEL:
                journal(f"AUTO_TRADE TEST {compte} {ordre}")
                res.append({"compte": compte, "ok": True, "test": True, "ordre": ordre}); continue
            r = _api("POST", f"{compte}/trade", ordre)
            res.append({"compte": compte, "ok": r.get("stringCode") in ("TRADE_RETCODE_DONE", "ERR_NO_ERROR"), "reponse": r, "ordre": ordre})
            etat.setdefault("mt5_plan", {})[compte] = {"marche": m, "sens": signal["sens"], "sym": sym, "e": prix, "sl": sl_mt5,
                                                      "tp": tp_mt5, "taille": float(spec.get("contractSize", 1)),
                                                      "pas": float(spec.get("volumeStep", 0.01)), "be": False, "rachats": 0}
        except Exception as ex:
            res.append({"compte": compte, "ok": False, "raison": f"erreur {ex}"})
        time.sleep(0.5)
    journal(f"AUTO_TRADE {m} {signal['sens']} → {res}")
    return res


# ── Stratégie FTMO / FundedNext d'Adel (15/11) : rachats sur repli, 100 $ de risque MAXIMUM au total ──────────
def risque_positions(positions, taille):
    """Perte totale en $ si toutes les positions du plan touchent leur SL."""
    return sum(abs(float(p["openPrice"]) - float(p.get("stopLoss") or p["openPrice"])) * taille * float(p["volume"]) for p in positions)


def decision(plan, positions, prix):
    """Que faire maintenant ? → ('rachat', lots) | ('be', None) | (None, None). Pur calcul, testé sans MetaApi.
    • le prix recule d'au moins 40 % du chemin entrée → SL (sans toucher le SL) : on RACHÈTE, petit, si le budget de 100 $ le permet ;
    • le prix a fait +1R depuis l'entrée moyenne : tous les SL passent à l'entrée moyenne (BE), plus aucun risque."""
    d = 1 if plan["sens"] == "LONG" else -1
    if not positions:
        return None, None
    vol = sum(float(p["volume"]) for p in positions)
    moy = sum(float(p["openPrice"]) * float(p["volume"]) for p in positions) / vol
    r1 = abs(plan["e"] - plan["sl"])
    if not plan.get("be") and r1 > 0 and d * (prix - moy) >= r1:
        return "be", moy
    if plan.get("be") or len(positions) >= POSITIONS_MAX:
        return None, None
    recul = d * (plan["e"] - prix)
    if recul < REPLI_RACHAT * r1 or d * (prix - plan["sl"]) <= 0:
        return None, None
    if plan.get("rachats", 0) >= 1 and d * (plan.get("dernier_rachat", plan["e"]) - prix) < 0.25 * r1:
        return None, None                                    # pas deux rachats au même endroit
    reste = RISQUE_TOTAL_MAX - risque_positions(positions, plan["taille"])
    budget = min(RISQUE_RACHAT, reste)
    lots = volume(prix, plan["sl"], plan["taille"], plan.get("pas", 0.01), risque=budget, elargi=False) if budget > 0 else 0
    return ("rachat", lots) if lots else (None, None)


def gerer(etat, journal=print):
    """À chaque tour du bot : rachats sur repli et passage à BE, sur chaque compte MetaApi. Renvoie les messages pour le propriétaire."""
    msgs = []
    for compte, plan in list((etat.get("mt5_plan") or {}).items()):
        try:
            pos = [p for p in (_api("GET", f"{compte}/positions") or []) if p.get("symbol") == plan["sym"] and "ALIGN" in str(p.get("comment", ""))]
            if not pos:
                etat["mt5_plan"].pop(compte, None)
                msgs.append(f"🏁 FundedNext {plan['marche']} : plan terminé (TP, SL ou BE)")
                continue
            q = _api("GET", f"{compte}/symbols/{plan['sym']}/current-price")
            prix = float(q["bid"] if plan["sens"] == "LONG" else q["ask"])
            quoi, x = decision(plan, pos, prix)
            if quoi == "rachat":
                ordre = {"actionType": "ORDER_TYPE_BUY" if plan["sens"] == "LONG" else "ORDER_TYPE_SELL", "symbol": plan["sym"],
                         "volume": x, "stopLoss": plan["sl"], "takeProfit": plan["tp"], "comment": "ALIGN rachat"}
                if REEL:
                    _api("POST", f"{compte}/trade", ordre)
                plan["rachats"] = plan.get("rachats", 0) + 1
                plan["dernier_rachat"] = prix
                msgs.append(f"➕ FundedNext {plan['marche']} : rachat {x} lot sur le repli (risque total ≤ {RISQUE_TOTAL_MAX:.0f} $) ({'réel' if REEL else 'test'})")
            elif quoi == "be":
                for p in pos:
                    if REEL:
                        _api("POST", f"{compte}/trade", {"actionType": "POSITION_MODIFY", "positionId": p["id"],
                                                          "stopLoss": round(x, 2), "takeProfit": p.get("takeProfit") or plan["tp"]})
                plan["be"] = True
                msgs.append(f"🔒 FundedNext {plan['marche']} : +1R atteint → tous les SL à l'entrée moyenne (BE) ({'réel' if REEL else 'test'})")
        except Exception as ex:
            journal(f"AUTO_TRADE gerer {compte} : {ex}")
    for x in msgs:
        journal(x)
    return msgs
