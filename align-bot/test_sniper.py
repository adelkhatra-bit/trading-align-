"""Entrée sniper EN CASCADE (M1 -> M3 -> M5 -> M15) : quand le prix entre dans la zone du plan, vente (achat) au rejet confirmé sous le dernier plus haut
(au-dessus du dernier plus bas) de la plus petite UT valide ; SL derrière la mèche ; TP du plan conservé + TP1 intermédiaire ; jamais forcé.

SCÉNARIO « GOLD cette nuit » : SIMULÉ à partir de la capture d'Adel (plan SWING short, zone 3993,28 → 4012,79, entrée 4012,79 jamais atteinte,
pic à 3997,6 sous le dernier plus haut M5, chute vers 3978). Le rejeu sur les VRAIES bougies M1/M3/M5 se lance avec replay_sniper.py
(workflow sniper-replay.yml) : ce fichier ne prétend pas être du réel."""
import json
import unittest
import time
from unittest.mock import patch

import align_bot as ab
from test_parite_pine import jeu_simule

T0 = (int(time.time()) // 900 * 900) - 285 * 60  # ancrage commun M1/M3/M5 sur une frontière de 15 min
PTS = [(0, 3960), (30, 3980), (60, 3990), (120, 3996.0), (122, 3998.2), (124, 3996.0), (150, 3984), (163, 3996.0), (165, 3997.9), (167, 3996.0), (185, 3988),
       (193, 3995.0), (195, 3996.9), (197, 3995.0), (205, 3990), (215, 3993.3), (225, 3995.0), (229, 3995.8), (231, 3996.0), (233, 3995.2), (236, 3994.0),
       (240, 3992.0), (285, 3978.0)]     # structure M5 (3998,2) > M3 (3997,9) > M1 (3996,9), entrée dans la zone par le bas vers la minute 215, pic ~3997,6, chute


def chemin_nuit():
    def interp(m):
        for (a, pa), (b_, pb) in zip(PTS, PTS[1:]):
            if a <= m <= b_:
                return pa + (pb - pa) * (m - a) / (b_ - a)
        return PTS[-1][1]
    c = [interp(m) for m in range(286)]
    m1 = []
    for i, cl in enumerate(c):
        o = c[i - 1] if i else cl - 0.2
        m1.append(dict(t=T0 + 60 * i, o=o, h=max(o, cl) + 0.3, l=min(o, cl) - 0.3, c=cl))
    m1[232] = dict(t=m1[232]["t"], o=3995.8, h=3997.6, l=3994.8, c=3995.2)                  # le pic : mèche à 3997,6, clôture 3995,2
    m1[233] = dict(t=m1[233]["t"], o=3995.2, h=3995.4, l=3993.9, c=3994.0)
    return m1


def miroir(m1, pivot=3990.0):
    return [dict(t=x["t"], o=2 * pivot - x["o"], h=2 * pivot - x["l"], l=2 * pivot - x["h"], c=2 * pivot - x["c"]) for x in m1]


def r_at(m1all, k, long=False, **kw):
    m1 = m1all[:k + 1]; now = m1[-1]["t"] + 60
    b3, b5, b15 = (ab.regrouper(m1, n, 60, now_ts=now) for n in (3, 5, 15))
    f = lambda b: b + [dict(m1[-1])]                                          # la dernière bougie M5 / M15 du bot est en formation
    piv = 3990.0
    z = (3993.28, 4012.79) if not long else (2 * piv - 4012.79, 2 * piv - 3993.28)
    niveaux = [(3985.0, "15m"), (3979.5, "1h"), (3960.0, "4h")]
    if long:
        niveaux = [(2 * piv - v, n) for v, n in niveaux]
    r = dict(market="BTC", dirPlan=1 if long else -1, bull=10 if long else 1, bear=1 if long else 10, sens=1 if long else -1, dirs=[1 if long else -1] * 11, strat="SWING",
             atr=6.0, atr3=1.8, atr5=2.6, m1=m1, b3=b3, b5=f(b5), b15=f(b15), zone_pine=dict(za=z[0], zb=z[1], zmil=(z[0] + z[1]) / 2), niveaux=niveaux,
             b1h=[dict(t=now - 7200, o=100, h=101, l=99, c=100), dict(t=now - 3600, o=100, h=101, l=99, c=100)],
             b4h=[dict(t=now - 28800, o=100, h=101, l=99, c=100), dict(t=now - 14400, o=100, h=101, l=99, c=100)],
             plan=dict(d=1 if long else -1, e=(2 * piv - 4012.79) if long else 4012.79, sl=(2 * piv - 4019.86) if long else 4019.86,
                       tp1=(2 * piv - 3895.54) if long else 3895.54, tp2=(2 * piv - 3850.0) if long else 3850.0), prix=m1[-1]["c"])
    r.update(kw)
    return r


def premiere_proposition(m1all, long=False, debut=205, fin=284, **kw):
    refus = {}
    for k in range(debut, fin):
        sn, raison = ab._sniper(r_at(m1all, k, long, **kw))
        if sn:
            return k, sn
        refus[raison] = refus.get(raison, 0) + 1
    print("SNIPER_TEST_REFUSALS", sorted(refus.items(), key=lambda item: (-item[1], str(item[0])))[:8])
    return None, None


class Cascade(unittest.TestCase):
    M1 = chemin_nuit()

    def test_night_case_sell_at_the_rejection_with_sl_behind_the_wick(self):
        k, sn = premiere_proposition(self.M1)
        self.assertIsNotNone(sn)
        self.assertEqual(sn["d"], -1)
        self.assertTrue(3994.0 <= sn["e"] <= 3997.7, sn["e"])                                   # vente au niveau du rejet (~3995-3997)
        self.assertTrue(3998.5 <= sn["sl"] <= 4001.0, sn["sl"])                                # SL juste derrière la mèche du pic (~3999-4000 + marge)
        self.assertGreater(sn["sl"], 3997.6)                                                     # jamais sous la mèche
        self.assertIn("M1", sn["rejets"]); self.assertIn("M3", sn["rejets"])                    # rejet confirmé sur M1 ET M3
        self.assertTrue(all("mèche" in x or "balayage" in x or "englobante" in x for x in sn["rejets_detail"]))
        self.assertTrue(any(x.startswith("M1 : ") for x in sn["rejets_detail"]))
        self.assertTrue(all("wick" in x or "sweep" in x or "engulfing" in x for x in sn["rejets_detail_en"]))
        self.assertAlmostEqual(sn["tp2"], 3895.54)                                               # TP du plan conservé
        self.assertLess(sn["tp1"], sn["e"]); self.assertGreater(sn["tp1"], sn["tp2"])           # TP1 intermédiaire réaliste, avant le TP du plan
        self.assertGreaterEqual(sn["rr"], ab.GAIN_MIN); self.assertGreater(sn["rr_plan"], sn["rr"])
        res = ab.simuler_sniper(sn, self.M1[k + 1:])
        self.assertEqual(res["etat"], "TP1"); self.assertGreater(res["pnl"], 8)
        print((f"SNIPER_SIMULE minute {k} prix {self.M1[k]['c']:.2f} → vente {sn['e']:.2f} ({sn['src']}, rejet {'+'.join(sn['rejets'])}) SL {sn['sl']:.2f} "
                f"TP1 {sn['tp1']:.2f} ({sn['n1']}) TP plan {sn['tp2']:.2f} R/R {sn['rr']:.1f} (plan {sn['rr_plan']:.1f}) → {res['etat']} {res['pnl']:+.1f} pts")
              .encode("ascii", "backslashreplace").decode("ascii"))

    def test_plan_entry_4012_was_never_reachable_but_sniper_is(self):
        tous = ab.simuler_sniper(dict(d=-1, e=4012.79, sl=4019.86, tp1=3895.54, t=self.M1[0]["t"], marche=False), self.M1)
        self.assertEqual(tous["etat"], "non rempli")                                            # le plan SWING seul : position ratée
        self.assertIsNotNone(premiere_proposition(self.M1)[1])

    def test_cascade_goes_up_when_a_close_breaks_the_last_high(self):
        k, sn = premiere_proposition(self.M1)
        casse = [dict(x) for x in self.M1]
        casse[232] = dict(casse[232], o=3995.8, h=3998.4, c=3997.9, l=3994.8)                      # clôture M1 AU-DESSUS du dernier plus haut (3997,2)
        k2, sn2 = premiere_proposition(casse)
        self.assertTrue(sn2 is None or sn2["ut"] != "M1")

    def test_cascade_picks_lowest_ut_under_the_upper_ut_high(self):
        k, sn = premiere_proposition(self.M1)
        self.assertEqual(sn["ut"], "M1")                                                         # M1 sans plus haut supérieur valide au-dessus : la plus petite UT
        self.assertIn("plus haut", sn["src"])

    def test_never_forced(self):
        k, _ = premiere_proposition(self.M1)
        cas = {"UT non alignées": dict(bear=7), "sens flou": dict(sens=0), "contre la 1h": dict(dirs=[-1] * 7 + [1] + [-1] * 3), "contre la 4h": dict(dirs=[-1] * 9 + [1, -1]),
               "pas de direction": dict(dirPlan=0), "prix hors zone": dict(zone_pine=dict(za=4005.0, zb=4012.79, zmil=4009.0))}
        for nom, kw in cas.items():
            self.assertIsNone(ab.entree_sniper(r_at(self.M1, k, **kw)), nom)
        self.assertIsNone(ab.entree_sniper(r_at(self.M1, 150)), "avant l'entrée dans la zone")
        self.assertIsNone(ab.entree_sniper(r_at(self.M1, 231)), "pas de rejet confirmé encore (pic pas encore formé)")

    def test_long_mirror_in_a_buy_zone(self):
        miroir_m1 = miroir(self.M1)
        k, sn = premiere_proposition(miroir_m1, long=True)
        self.assertIsNotNone(sn); self.assertEqual(sn["d"], 1)
        self.assertLess(sn["sl"], sn["e"]); self.assertGreater(sn["tp1"], sn["e"]); self.assertGreater(sn["tp2"], sn["tp1"])
        self.assertEqual(ab.simuler_sniper(sn, miroir_m1[k + 1:])["etat"], "TP1")

    def test_m1_m3_m5_structure_levels_same_method_and_never_used_for_targets(self):
        r = r_at(self.M1, 236)
        niv = ab.niveaux_structure_ut(dict(r, m1=r["m1"]))
        self.assertEqual(sorted(niv), ["M1", "M3", "M5"])
        for nom, bars in (("M5", r["b5"][:-1]), ("M3", r["b3"])):                                  # même méthode que pivots() des niveaux 15 min / 1 h / 4 h / Daily
            quatre = tuple(x[0] if x else None for x in niv[nom])
            attendu = ab.pivots(bars, 5)
            self.assertEqual((quatre[0], quatre[1], quatre[2], quatre[3]), tuple(attendu))
        self.assertAlmostEqual(niv["M5"][0][0], 3997.2, places=1); self.assertAlmostEqual(niv["M5"][2][0], 3998.2, places=1)   # dernier et avant-dernier plus haut M5
        k, sn = premiere_proposition(self.M1)
        self.assertTrue(all(n in ("15m", "1h", "4h", "Daily") for _, n in r["niveaux"]))             # TP / plan : aucun niveau M1 / M3 / M5
        self.assertIn(sn["n1"], ("15m", "1h", "4h", "Daily")); self.assertAlmostEqual(sn["tp2"], 3895.54)   # TP inchangés par la cascade

    def test_pipeline_attaches_sniper_without_crashing(self):
        S = jeu_simule(11, 0.0006)
        r = ab.analyser_avec_memoire(dict(S, m15=S["m15"][:340]), {})
        self.assertIn("sniper", r); self.assertIsNotNone(r["atr3"])
        self.assertTrue(all(n in ("M1", "M3", "M5") for _, n in r["niveaux_ut"]) and r["niveaux_ut"])      # niveaux sniper visibles, séparés de r["niveaux"]
        self.assertTrue(all(n in ("15m", "1h", "4h", "Daily") for _, n in r["niveaux"]))


class TypesDeRejet(unittest.TestCase):
    def _base(self):
        return [dict(t=i, o=99.8, h=100.2, l=99.8, c=100.2) for i in range(20)]

    def test_simple_close_back_below_level_is_not_a_rejection_pattern(self):
        bars = self._base()
        bars.append(dict(t=20, o=99.95, h=99.99, l=99.0, c=99.8))
        self.assertIsNone(ab._rejet(bars, -1, 100.2, 1.0))

    def test_explicit_upper_wick_rejection_is_classified(self):
        bars = self._base()
        bars.append(dict(t=20, o=99.95, h=101.5, l=99.5, c=100.0))
        result = ab._rejet(bars, -1, 101.0, 1.0)
        self.assertIsNotNone(result)
        self.assertIn("mèche haute de rejet baissier", result["rejection_type"])
        self.assertIn("% de l'amplitude", result["rejection_type"])

    def test_bollinger_rejection_requires_a_real_sweep_and_reentry(self):
        bars = self._base()
        bars.append(dict(t=20, o=99.95, h=101.5, l=96.5, c=99.9))
        result = ab._rejet(bars, -1, 101.0, 1.0)
        self.assertIsNotNone(result)
        self.assertIn("balayage de la bande haute puis réintégration", result["rejection_type"])
        self.assertNotIn("mèche haute de rejet baissier", result["rejection_type"])


class PreAlerteMeche(unittest.TestCase):
    def test_in_progress_wick_is_not_reported_as_confirmed_stop_hunt(self):
        b15 = [dict(t=1000 + 900 * i, o=100.0, h=101.0, l=99.0, c=100.0) for i in range(21)]
        debut = b15[-1]["t"] + 900
        m1 = [
            dict(t=debut + 60 * i, o=100.0, h=100.5, l=99.2, c=99.8)
            for i in range(5)
        ]
        m1[0].update(o=100.0, h=100.1, l=98.0, c=99.0)
        m1[-1].update(c=100.2)
        out = []
        ab.meche_suspecte(out, "BTC", {"b15": b15, "atr": 1.0, "m1": m1}, {})
        message = "\\n".join(out)
        self.assertIn("mèche basse en formation", message)
        self.assertIn("Balayage de liquidité POSSIBLE", message)
        self.assertIn("clôture n'a pas confirmé", message)
        self.assertIn("Attendre la CLÔTURE M15", message)
        self.assertNotIn("Les stops viennent d'être pris", message)


class MessagesEtRegles(unittest.TestCase):
    M1 = chemin_nuit()

    PINE_PLAN = {
        "available": True, "confirmed": True, "triggered": True, "direction": -1,
        "entry": 4000.5, "sl": 4020.0, "tp1": 3970.0, "tp2": 3895.54,
        "zone_low": 3993.28, "zone_high": 4012.79,
        "entry_bar_time": 1_795_017_600_000, "entry_timeframe": "H1", "strategy": "SWING",
    }

    def evenement(self, etat=None, now=None, k=None, pine_plan=None):
        etat = {} if etat is None else etat
        k, sn = premiere_proposition(self.M1) if k is None else (k, None)
        r = dict(r_at(self.M1, k), comp=0, sqzs=[0] * 11, dirW=0, pctH=20, sniper=sn)
        # This test exercises only the Pine notification/rendering contract, not the local sniper detector.
        # Keep a deterministic M1/M3/M5 timing proposal independent from changing market-data fixtures.
        r["sniper"] = {"d": -1, "t": r["m1"][-1]["t"], "ut": "M1/M3", "rejets": ["M1", "M3"],
                       "rejets_detail": ["M1 : mèche haute de rejet baissier (52% de l'amplitude)",
                                          "M3 : bougie englobante baissière"],
                       "rejets_detail_en": ["M1: upper bearish rejection wick (52% of candle range)",
                                            "M3: bearish engulfing candle"]}
        now = now or r["m1"][-1]["t"]
        plan = self.PINE_PLAN if pine_plan is None else pine_plan
        with patch.object(ab, "cme_ouvert", return_value=True), \
             patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)), \
             patch.object(ab, "plan_indicateur", return_value=plan):
            return etat, [e for e in ab.evenements_pine(etat, "GOLD", r, etat.setdefault("GOLD", {}), now) if e["kind"] == "sniper"], r

    def test_message_in_addition_to_plan_short_varied_fr_en_once(self):
        etat, ev, r = self.evenement()
        self.assertEqual(len(ev), 1)
        fr = ab.texte_pine({}, ev[0]); en = ab.texte_pine({}, ev[0], True)
        self.assertLessEqual(len(fr), 3)
        self.assertIn("🎯 SNIPER VALIDÉ — SWING 🥇 GOLD : vente Pine 4000,5", fr[0])
        self.assertIn("zone 3993,28–4012,79", fr[0])
        self.assertIn("SL Pine 4020 • TP1 Pine 3970 • TP2 Pine 3895,54", fr[1])
        self.assertIn("timing M1/M3 • plan H1", fr[2])
        self.assertIn("mèche haute de rejet baissier", fr[2])
        self.assertIn("bougie englobante baissière", fr[2])
        self.assertIn("upper bearish rejection wick", en[2])
        self.assertIn("bearish engulfing candle", en[2])
        self.assertNotIn("mèche", " ".join(en))
        self.assertIn("validation ROBOT V12 avant position ouverte", fr[2])
        self.assertNotIn("POSITION OUVERTE", " ".join(fr))
        self.assertEqual(ev[0]["entree"], "4000,50")
        self.assertEqual((ev[0]["sl"], ev[0]["tp1"], ev[0]["tp"]), ("4020", "3970", "3895,54"))
        self.assertIn("SNIPER CONFIRMED — SWING", en[0]); self.assertIn("sell", en[0]); self.assertNotIn("vente", " ".join(en))
        self.assertIn("plan H1", en[2])
        self.assertEqual(len({" ".join(ab.texte_pine({"al_rot": {"p:sniper:GOLD": k}}, ev[0])) for k in (-1, 0, 1)}), 3)
        etat2, ev2, _ = self.evenement(etat, now=r["m1"][-1]["t"] + 60, k=None)
        self.assertEqual(ev2, [])                                                                 # une seule fois (même niveau, même UT)

    def test_local_sniper_never_publishes_without_matching_confirmed_pine_trigger(self):
        cases = (
            dict(self.PINE_PLAN, available=False),
            dict(self.PINE_PLAN, triggered=False),
            dict(self.PINE_PLAN, direction=1),
        )
        for plan in cases:
            with self.subTest(plan=plan):
                _, events, _ = self.evenement(pine_plan=plan)
                self.assertEqual(events, [])

    def test_local_sniper_rejection_expires_after_two_minutes(self):
        k, _ = premiere_proposition(self.M1)
        r = r_at(self.M1, k)
        stale_now = r["m1"][-1]["t"] + 121
        _, events, _ = self.evenement(now=stale_now)
        self.assertEqual(events, [])

    def test_free_sees_nothing_of_the_sniper_and_vip_gets_it(self):
        import inspect
        src = inspect.getsource(ab.alertes_courtes)
        self.assertIn("diffuser_evenements(etat, chats", src)                                          # VIP : chaîne + privés
        envois = []
        etat, ev, _ = self.evenement()
        with patch.object(ab, "TOKEN", "x"), patch.object(ab, "cme_ouvert", return_value=True), patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: envois.append((str(c), k["text"]))), \
             patch.object(ab, "destinataires_message", return_value=["canal"]), patch.object(ab, "evenements_pine", return_value=ev):
            etat["prospects"] = ["900"]
            ab.alertes_courtes(etat, set(), {"GOLD": {}}, 1_000_000)
        self.assertEqual([c for c, _ in envois], ["canal"])

    def test_plan_sl_broken_by_confirmed_close_triggers_reversal_in_preparation_message(self):
        """Règle du Pine (retDir) : SL du plan franchi par une clôture 15 min confirmée -> position annulée, retournement en préparation + message."""
        S = jeu_simule(11, 0.0006); m15 = S["m15"]; mem, etat = {}, {}
        ab.analyser_avec_memoire(dict(S, m15=m15[:340]), mem)
        mem["dir_fig"] = mem.get("dir_fig") or 1
        c = m15[340]["c"]
        mem["sl"] = (c + 5.0) if mem["dir_fig"] == 1 else (c - 5.0)                                # SL du plan placé du mauvais côté de la prochaine clôture
        ab.analyser_avec_memoire(dict(S, m15=m15[:341]), mem)
        r = ab.analyser_avec_memoire(dict(S, m15=m15[:342]), mem)
        self.assertNotEqual(r["ret_dir"], 0)
        self.assertIn("SL cassé à la clôture", " ".join(ab.ligne_retournement(r)))
        with patch.object(ab, "cme_ouvert", return_value=True), patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)):
            r["ret_conf"] = False
            ev = ab.evenements_pine(etat, "GOLD", dict(r, sniper=None), {}, r["m1"][-1]["t"])
        self.assertIn("ret_cancel", [e["kind"] for e in ev])
        r["ret_conf"] = True
        with patch.object(ab, "cme_ouvert", return_value=True), patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)):
            ev2 = ab.evenements_pine(etat, "GOLD", dict(r, sniper=None), {}, r["m1"][-1]["t"] + 900)
        self.assertIn("ret_conf", [e["kind"] for e in ev2])


class SensDansLeGratuit(unittest.TestCase):
    """Adel garde le sens haussier / baissier dans le gratuit et sur la page ALIGN LIVE : jamais les niveaux."""

    def test_free_preparation_keeps_the_bias_without_levels(self):
        envois = []
        etat = {"prospects": ["900"]}
        with patch.object(ab, "_envoi_sur", side_effect=lambda c, **k: envois.append(k["text"])), patch.object(ab, "bot_on", return_value=True):
            ab.alerte_gratuite_preparation(etat, "🔔 JE PRÉPARE UNE POSITION — 🥇 GOLD\n🟥 SHORT ⬇️ descend\n📌 Entrée : 4012,5")
        self.assertEqual(envois, [])  # aucun teaser privé automatique

    def test_live_page_json_still_has_the_bias(self):
        etat = {}
        r = {"dirPlan": -1, "bull": 1, "bear": 10, "sens": -1, "pctH": 20, "strat": "SWING", "dirs": [-1] * 11, "dirW": 0, "atr": 2.0, "prix": 3983.5,
             "m1": [{"t": 1_800_000_000 - 20, "c": 3983.5}], "zone_pine": None}
        with patch.object(ab, "cme_ouvert", return_value=True):
            d = ab.construire_live(etat, {"GOLD": r}, 1_800_000_000)
        self.assertEqual(d["marches"][0]["biais"], "baissier"); self.assertEqual(d["marches"][0]["ut"], 10)


class PropositionPineV25(unittest.TestCase):
    """Le v24 visuel ne change que sur le RSI et la suppression des sorties d'alerte ; son design reste protégé."""
    RACINE = __import__("pathlib").Path(__file__).resolve().parent / "pine"
    RSI_CROSSOVER_BLOCK = """rsiCrossSigUp   = ta.crossover(rC, rsiSig)
rsiCross30Up     = ta.crossover(rC, 30)
rsiCross50Up     = ta.crossover(rC, 50)
rsiCrossSigDown  = ta.crossunder(rC, rsiSig)
rsiCross70Down   = ta.crossunder(rC, 70)
rsiCross50Down   = ta.crossunder(rC, 50)
rsiAchat = (rsiCrossSigUp and rC < 50) or rsiCross30Up or rsiCross50Up
rsiVente = (rsiCrossSigDown and rC > 50) or rsiCross70Down or rsiCross50Down
"""
    RSI_CROSSOVER_BASELINE_BLOCK = """rsiAchat = (ta.crossover(rC, rsiSig) and rC < 50) or ta.crossover(rC, 30) or ta.crossover(rC, 50)
rsiVente = (ta.crossunder(rC, rsiSig) and rC > 50) or ta.crossunder(rC, 70) or ta.crossunder(rC, 50)
"""
    VISUAL_ONLY_MARKER = """// VISUEL UNIQUEMENT — aucune alerte sortante, aucun bridge, aucune donnée consommée par ROBOT V12.
"""
    BASELINE_ALERT_BLOCK = r"""// ═════════ ALERTES (créer une alerte « N'importe quel appel alert() ») ═════════
if sigHaut
    alert(syminfo.ticker + " " + nomSigH + " | " + pqH + " | " + str.replace_all(planH, "\n", " | "), alert.freq_once_per_bar_close)
if sigBas
    alert(syminfo.ticker + " " + nomSigB + " | " + pqB + " | " + str.replace_all(planB, "\n", " | "), alert.freq_once_per_bar_close)
if retHaut and not retHaut[1]
    alert(syminfo.ticker + " : retournement HAUSSIER en préparation, TP1 " + px(hT1), alert.freq_once_per_bar_close)
if retBas and not retBas[1]
    alert(syminfo.ticker + " : retournement BAISSIER en préparation, TP1 " + px(bT1), alert.freq_once_per_bar_close)
alertcondition(sigHaut, "Signal ACHAT", "Signal ACHAT ALIGN MTF")
alertcondition(sigBas, "Signal VENTE", "Signal VENTE ALIGN MTF")
"""

    def test_v24_untouched_and_diff_has_no_design_change(self):
        import hashlib
        v24 = (self.RACINE / "ALIGN_MTF_PRO_v24.pine").read_text(encoding="utf-8").replace("\r\n", "\n")
        self.assertEqual(v24.count(self.RSI_CROSSOVER_BLOCK), 1)
        self.assertEqual(v24.count(self.VISUAL_ONLY_MARKER), 1)
        normalized = v24.replace(self.RSI_CROSSOVER_BLOCK, self.RSI_CROSSOVER_BASELINE_BLOCK, 1)
        normalized = normalized.replace(self.VISUAL_ONLY_MARKER, self.BASELINE_ALERT_BLOCK, 1)
        normalized = normalized.replace("// v24 est strictement contextuel : aucun Entry / SL / TP indépendant ne peut être affiché.\\nvoirPlan = false", 'voirPlan = input.bool(false, "Afficher le plan (TP / SL)", group=grpA)', 1)
        normalized = normalized.replace("voirFibo = false", 'voirFibo = input.bool(false, "Zone d\'entrée + Fibonacci", group=grpA)', 1)
        normalized = normalized.replace("// Les signaux directionnels exécutables appartiennent exclusivement au v25.\\nvoirSignauxV24 = false", 'voirSignauxV24 = input.bool(false, "Signaux indépendants v24 (désactivés par défaut)", group=grpA)', 1)
        normalized = normalized.replace('titre = zoneBas ? "PRESSION À LA RÉSISTANCE (CONTEXTE)" : zoneHaut ? "PRESSION AU SUPPORT (CONTEXTE)" : rsiOB >= 3 ? "RSI SURACHAT — CONTEXTE" : rsiOS >= 3 ? "RSI SURVENTE — CONTEXTE" : surcharge ? "COMPRESSION — SURVEILLANCE" : sens == 1 ? "BIAIS HAUSSIER — CONTEXTE" : sens == -1 ? "BIAIS BAISSIER — CONTEXTE" : "CONTEXTE MIXTE"', 'titre = zoneBas ? "RETOURNEMENT ▼" : zoneHaut ? "REBOND ▲" : fortHaut ? "★ ACHAT FORT" : fortBas ? "★ VENTE FORTE" : retHaut ? "RETOURNEMENT ▲" : retBas ? "RETOURNEMENT ▼" : rsiOB >= 3 ? "RSI SURACHAT " + str.tostring(rsiOB) + "/11" : rsiOS >= 3 ? "RSI SURVENTE " + str.tostring(rsiOS) + "/11" : surcharge ? "⚡ SURCHARGE" : sens == 1 ? "HAUSSE" : sens == -1 ? "BAISSE" : "ATTENDRE"', 1)
        self.assertEqual(hashlib.sha256(normalized.encode("utf-8")).hexdigest(), "ff45aaa9684b011d89f5761f7a0bb047221448f63a4f12413167ead6d03a25c0")  # toutes les zones hors RSI et sorties d'alerte restent identiques au v24 publié

        diff = (self.RACINE / "PROPOSITION_v25_sniper.diff").read_text(encoding="utf-8").splitlines()
        modifs = [l[1:] for l in diff if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        self.assertGreater(len(modifs), 20)
        for l in modifs:
            if "al135" in l or l.strip().startswith(("lE   :=", "eE   :=")):
                continue                                           # seule exception voulue par Adel : trait d'entrée jaune → vert si 1/3/5 min alignées
            for interdit in ("color.", "table.", "label.new", "line.new", "box.new", "bgcolor", "plotshape", "size.", "style=", "position."):
                self.assertNotIn(interdit, l)
        v25 = (self.RACINE / "ALIGN_MTF_PRO_v25_PROPOSITION.pine").read_text(encoding="utf-8")
        self.assertIn("NON PUBLIÉE", v25)
        self.assertEqual(v25.count("request.security("), 28)           # 21 en v24 + 3 niveaux (M1, M3, M5) + 4 clôtures (M1, M3, M5, M15) ; limite TradingView : 40
        for marque in ("niveauxSn", "snOk", "entP", "lv1", "lv3", "lv5", "bbU"):                   # niveaux M1/M3/M5 séparés + cascade
            self.assertIn(marque, v25)


if __name__ == "__main__":
    unittest.main()
