"""ALIGN — calcul et simulation des positions FundedNext (MT5 via MetaApi).

Aucun ordre broker réel n'est autorisé dans ALIGN. Le module conserve ses calculs,
lectures de prix et simulations ; AUTO_TRADE ne peut pas réactiver l'exécution réelle.

Limites de risque conservées pour les simulations :
  • perte du jour  : arrêt à -350 $
  • perte totale   : arrêt à -750 $ sous le solde de départ
  • risque         : 75 $ par position (calcul du SL derrière la mèche)
  • positions      : 2 max ouvertes par compte en modèle de simulation
"""
import json, os, re, time, datetime, math, urllib.request, urllib.error

SOLDE_DEPART = 10000.0
PERTE_JOUR_MAX = 350.0        # marge de 50 $ sous la règle des 400 $
PERTE_TOTALE_MAX = 750.0      # marge de 50 $ sous la règle des 800 $
RISQUE_DOLLARS = 50.0        # 1re entrée = la moitié du budget (stratégie rachats d'Adel, 15/11)
RISQUE_TOTAL_MAX = 100.0     # règle d'Adel : TOUTES les positions du plan ensemble ne perdent jamais plus de 100 $
RISQUE_RACHAT = 25.0         # chaque rachat sur repli ajoute au plus 25 $ de risque
REPLI_RACHAT = 0.4           # on rachète quand le prix a reculé de 40 % du chemin entrée → SL (dans le sens du plan)
POSITIONS_MAX = 4            # 1 entrée + jusqu'à 3 rachats, toujours dans le même sens
SL_ELARGI = 1.25              # demande d'Adel : SL plus large, au-delà de la mèche

# Marchés ALIGN actifs du graphique TradingView : BTCUSD et XAUUSD.
# Le nom exact sur le serveur MT5 FundedNext est retrouvé tout seul dans cette liste.
SYMBOLES = {"BTC": ["BTCUSD", "BTCUSD.", "BTCUSDm"], "GOLD": ["XAUUSD", "XAUUSD.", "GOLD"]}

TOKEN = os.environ.get("METAAPI_TOKEN", "")
RISQUE_CONTRE = 60.0   # demande d'Adel (16/11) : contre-tendance pris par le bot, mais jamais plus de 60 $ de risque


def budget_risque(e, sl, tp, tp2=None):
    """Règle d'Adel (15/11) : 100 $ de risque SEULEMENT si l'objectif rapporte au moins 3 fois le risque (1:3 → 300-400 $),
    60 $ si au moins 2 fois (1:2), sinon PAS de position. Renvoie le budget total en $ (0 = on n'entre pas)."""
    r = abs(e - sl)
    if r <= 0:
        return 0.0
    rr = abs((tp2 or tp) - e) / r
    return 100.0 if rr >= 3 else 60.0 if rr >= 2 else 0.0


def lire_comptes(brut):
    """Ids MetaApi (format UUID) lus dans la variable, même collés deux fois ou sans virgule ; sans doublon, ordre gardé."""
    ids = re.findall(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", brut or "", re.I)
    return list(dict.fromkeys(ids)) or [c.strip() for c in (brut or "").split(",") if c.strip()]


COMPTES = lire_comptes(os.environ.get("METAAPI_COMPTES", ""))
REGION = os.environ.get("METAAPI_REGION", "london")
REEL = False  # Verrou ALIGN : aucune activation par variable d’environnement.


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
    if m not in SYMBOLES:
        raise ValueError("Marché désactivé dans ALIGN")
    cache = etat.setdefault("auto_symboles", {}).setdefault(compte, {})
    if m not in cache:
        dispo = set(_api("GET", f"{compte}/symbols") or [])
        cache[m] = next((s for s in SYMBOLES[m] if s in dispo), SYMBOLES[m][0])
    return cache[m]


ECART_MAX = 0.01        # 1 % : au-delà, le prix MT5 ne correspond pas au graphique → on ne trade pas
AGE_MAX = 120           # secondes : un prix plus vieux = marché fermé ou flux figé (vu le 15/11 : BTC figé à 68 387 le dimanche)


def prix_fiable(cotation, prix, prix_graphique, maintenant=None):
    """Garde-fou demandé par Adel (graphique parfait, zéro latence) : pas d'ordre si le prix FundedNext est figé
    (marché fermé, week-end) ou trop loin du prix du graphique TradingView qui a donné le signal."""
    t = cotation.get("time") or cotation.get("brokerTime")
    if t:
        try:
            dt = datetime.datetime.fromisoformat(str(t).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            age = ((maintenant or datetime.datetime.now(datetime.timezone.utc)) - dt).total_seconds()
            if age > AGE_MAX:
                return False, f"prix FundedNext figé depuis {int(age // 60)} min (marché fermé ?)"
        except ValueError:
            pass
    if prix_graphique and abs(prix - prix_graphique) / prix_graphique > ECART_MAX:
        return False, f"prix FundedNext {prix:.2f} trop loin du graphique {prix_graphique:.2f} (> 1 %)"
    return True, "ok"


def niveaux_mt5(signal, prix):
    """Le prix MT5 (CFD) n'est pas exactement celui de TradingView : on garde les mêmes DISTANCES
    (SL élargi et TP) mais on les pose à partir du vrai prix d'exécution → aucune confusion de niveaux."""
    d_sl = abs(signal["e"] - signal["sl"]) * SL_ELARGI
    d_tp = abs(signal["tp"] - signal["e"])
    if signal["sens"] == "LONG":
        return round(prix - d_sl, 2), round(prix + d_tp, 2)
    return round(prix + d_sl, 2), round(prix - d_tp, 2)


def niveaux_valides(signal):
    """Refuse les niveaux incohérents avec le sens du trade avant tout appel broker."""
    try:
        sens = str(signal.get("sens", "")).upper()
        e, sl, tp = (float(signal[k]) for k in ("e", "sl", "tp"))
        tp2 = float(signal["tp2"]) if signal.get("tp2") is not None else None
    except (KeyError, TypeError, ValueError, OverflowError):
        return False, "niveaux Entry/SL/TP absents ou non numériques"
    valeurs = (e, sl, tp) + ((tp2,) if tp2 is not None else ())
    if not all(math.isfinite(v) and v > 0 for v in valeurs):
        return False, "niveaux Entry/SL/TP non finis ou non positifs"
    if sens == "LONG":
        valide = sl < e < tp and (tp2 is None or tp2 >= tp)
    elif sens == "SHORT":
        valide = tp < e < sl and (tp2 is None or tp2 <= tp)
    else:
        return False, "sens du signal invalide"
    return (True, "ok") if valide else (False, "niveaux inversés ou TP2 incohérent avec le sens")


def executer(etat, signal, journal=print):
    """signal = {marche, sens: 'LONG'|'SHORT', e, sl, tp}. Renvoie la liste des résultats par compte."""
    m = signal["marche"]
    if m not in SYMBOLES:
        return [{"compte": None, "ok": False, "raison": "marché désactivé dans ALIGN"}]
    if m not in marches_actifs(etat):
        return [{"compte": None, "ok": False, "raison": f"{m} éteint dans l'admin"}]
    valide, raison = niveaux_valides(signal)
    if not valide:
        return [{"compte": None, "ok": False, "raison": raison}]
    if not TOKEN or not COMPTES:
        return [{"compte": None, "ok": False, "raison": "MetaApi pas encore branché"}]
    res = []
    for compte in COMPTES:
        try:
            if not assurer_deploye(compte, journal=journal):
                res.append({"compte": compte, "ok": False, "raison": "compte MetaApi pas encore en service"}); continue
            etat.setdefault("metaapi_deploy", {}).update(deploye=True, besoin_t=time.time())
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
            budget = budget_risque(signal["e"], signal["sl"], signal["tp"], signal.get("tp2"))
            if signal.get("contre"):                     # ↩ contre-tendance vers l'entrée du plan principal : prudence challenge, 60 $ max
                budget = min(budget, RISQUE_CONTRE)
            if not budget:
                res.append({"compte": compte, "ok": False, "raison": "gain visé < 2 × le risque : on n'entre pas"}); continue
            spec = _api("GET", f"{compte}/symbols/{sym}/specification")
            lots = volume(signal["e"], signal["sl"], float(spec.get("contractSize", 1)),
                          float(spec.get("volumeStep", 0.01)), float(spec.get("minVolume", 0.01)), risque=budget / 2)
            if not lots:
                res.append({"compte": compte, "ok": False, "raison": "SL trop large pour le risque"}); continue
            px = _api("GET", f"{compte}/symbols/{sym}/current-price")
            prix = float(px["ask"] if signal["sens"] == "LONG" else px["bid"])
            ok_p, raison_p = prix_fiable(px, prix, signal["e"])
            if not ok_p:
                res.append({"compte": compte, "ok": False, "raison": raison_p}); continue
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
                                                      "pas": float(spec.get("volumeStep", 0.01)), "be": False, "rachats": 0, "budget": budget}
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
    reste = min(RISQUE_TOTAL_MAX, plan.get("budget", RISQUE_TOTAL_MAX)) - risque_positions(positions, plan["taille"])
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


def profit_ouvert(etat, m):
    """Gain/perte EN COURS (en $) des positions ALIGN réelles sur ce marché, tous comptes MetaApi. None si aucune."""
    if not (REEL and TOKEN and COMPTES):
        return None
    total, vu = 0.0, False
    for compte in COMPTES:
        sym = (etat.get("auto_symboles") or {}).get(compte, {}).get(m)
        for p in _api("GET", f"{compte}/positions") or []:
            if "ALIGN" in str(p.get("comment", "")) and (not sym or p.get("symbol") == sym):
                vu = True
                total += float(p.get("profit", 0)) + float(p.get("swap", 0)) + float(p.get("commission", 0))
    return round(total, 2) if vu else None


# ── Économies MetaApi (inquiétude d'Adel sur la consommation) ────────────────────────────────────────────────────
# MetaApi facture à l'heure tant que le compte est « Deployed ». Le bot le met en service seulement quand une entrée
# approche (ou qu'une position est ouverte) et le retire après 45 min sans besoin. Une entrée surprise attend la mise en service (≤ 90 s).
PROVISIONING = "https://mt-provisioning-api-v1.agiliumtrade.agiliumtrade.ai/users/current/accounts/"
RETRAIT_APRES = 45 * 60


def _prov(methode, chemin):
    req = urllib.request.Request(PROVISIONING + chemin, method=methode, data=b"" if methode == "POST" else None,
                                 headers={"auth-token": TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        txt = r.read().decode() or "{}"
    return json.loads(txt) if txt.strip().startswith("{") else {}


def etat_compte(compte):
    return (_prov("GET", compte) or {}).get("state", "")


def assurer_deploye(compte, attendre=90, pause=5, journal=print):
    """Met le compte en service si besoin et attend qu'il soit DEPLOYED (au plus `attendre` secondes)."""
    st = etat_compte(compte)
    if st == "DEPLOYED":
        return True
    if st in ("UNDEPLOYED", "UNDEPLOYING", ""):
        _prov("POST", f"{compte}/deploy")
        journal(f"METAAPI mise en service du compte {compte}")
    fin = time.time() + attendre
    while time.time() < fin:
        time.sleep(pause)
        if etat_compte(compte) == "DEPLOYED":
            return True
    return False


def gerer_deploiement(etat, besoin, maintenant=None, journal=print):
    """besoin = une entrée approche ou une position / un plan est en cours sur un marché allumé.
    Besoin → mise en service (sans attendre). Plus de besoin depuis 45 min → retrait (plus de facturation horaire)."""
    if not (TOKEN and COMPTES):
        return None
    maintenant = maintenant or time.time()
    d = etat.setdefault("metaapi_deploy", {})
    if besoin or etat.get("mt5_plan"):
        d["besoin_t"] = maintenant
        if not d.get("deploye"):
            for c in COMPTES:
                try:
                    if etat_compte(c) != "DEPLOYED":
                        _prov("POST", f"{c}/deploy")
                except Exception as ex:
                    journal(f"METAAPI deploy {c} : {ex}")
            d["deploye"] = True
            return "deploy"
        return None
    if d.get("deploye", True) and maintenant - float(d.get("besoin_t", 0)) > RETRAIT_APRES:
        for c in COMPTES:
            try:
                if etat_compte(c) == "DEPLOYED":
                    _prov("POST", f"{c}/undeploy")
            except Exception as ex:
                journal(f"METAAPI undeploy {c} : {ex}")
        d["deploye"] = False
        journal("METAAPI comptes retirés (aucune entrée en vue) : plus de facturation horaire")
        return "undeploy"
    return None
