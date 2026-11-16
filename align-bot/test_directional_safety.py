"""Régressions directionnelles : GOLD/NASDAQ ne publient pas d'entrées contre H1/H4."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def candle(t, o=100.0, h=101.0, l=99.0, c=100.0, v=100):
    return dict(t=t, o=o, h=h, l=l, c=c, v=v)


def retest_r(h4):
    bars = [candle(i * 900) for i in range(40)]
    bars[20]["h"] = 102.0
    for i in range(34, 38):
        bars[i] = candle(i * 900, o=102.5, h=104.0, l=102.2, c=103.0)
    bars[38] = candle(38 * 900, o=102.2, h=103.0, l=101.9, c=102.5)
    dirs = [0] * 11
    dirs[2], dirs[4], dirs[7], dirs[9] = 1, 1, 1, h4
    return dict(b15=bars, dirs=dirs, atr=1.0, grosses=[(110.0, "4h"), (120.0, "Daily")], t=40000)


def reversal_r(dirs, volume_last=100, price=100.0):
    b5 = [candle(i * 300, 100 - (i % 3)) for i in range(20)]
    b15 = [candle(i * 900) for i in range(50)]
    b15[-2]["v"] = volume_last
    b1 = [candle(i * 3600, 100, h=110, l=90) for i in range(10)]
    b4 = [candle(i * 14400, 100, h=130, l=70) for i in range(10)]
    return dict(dirs=dirs, b5=b5, b15=b15, b15_long=b15,
                b1h=b1, b4h=b4, m1=[candle(0, price)], t=10000)


LONG_GOLD = [1, 1, 1, 0, 1, 0, -1, -1, -1, -1, -1]
LONG_BTC = [1, 1, 1, 0, 1, 1, 1, 1, -1, -1, -1]


class DirectionSafety(unittest.TestCase):
    def test_gold_retest_requires_h4_confirmation(self):
        self.assertIsNone(ab.entree_retest("GOLD", retest_r(0), {}))
        msg = ab.entree_retest("GOLD", retest_r(1), {})
        self.assertIn("ENTRÉE POSSIBLE SUR RETEST : LONG", msg)
        self.assertIn("TP1 :", msg); self.assertIn("TP2 :", msg)

    def test_nasdaq_retest_requires_h4_confirmation(self):
        self.assertIsNone(ab.entree_retest("NASDAQ", retest_r(0), {}))
        msg = ab.entree_retest("NASDAQ", retest_r(1), {})
        self.assertIn("ENTRÉE POSSIBLE SUR RETEST : LONG", msg)
        self.assertIn("TP1 :", msg); self.assertIn("TP2 :", msg)

    def test_btc_retest_rule_is_unchanged(self):
        self.assertIn("ENTRÉE SUR RETEST : LONG", ab.entree_retest("BTC", retest_r(0), {}))

    def test_sniper_requires_both_h1_and_h4_for_gold_nasdaq(self):
        for market in ("GOLD", "NASDAQ"):
            for h1, h4 in ((1, 0), (0, 1), (-1, -1), (1, -1)):
                dirs = [0] * 11
                dirs[7], dirs[9] = h1, h4
                proposal, reason = ab._sniper({"market": market, "dirPlan": 1, "dirs": dirs})
                self.assertIsNone(proposal)
                self.assertIn("CONFLUENCE_H1_H4", reason)
        _, reason_btc = ab._sniper({"market": "BTC", "dirPlan": 1, "dirs": [0,0,0,0,0,0,0,1,0,0,0]})
        self.assertNotIn("CONFLUENCE_H1_H4", reason_btc)

    def test_every_gold_nasdaq_strategy_requires_h1_and_h4_same_direction(self):
        for market in ("GOLD", "NASDAQ"):
            for h1, h4 in ((1, 0), (0, 1), (-1, -1), (1, -1), (-1, 1)):
                dirs = [1, 1, 1, 0, 1, 0, 0, h1, 0, h4, 1]
                strat, status, reason = ab.strategie_alignement(dirs, 1, 1, market)
                self.assertEqual(strat, "")
                self.assertEqual(status, "EN ATTENTE")
                self.assertIn("H4 et H1", reason)
            dirs = [1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1]
            strat, status, _ = ab.strategie_alignement(dirs, 1, 1, market)
            self.assertEqual(strat, "SWING")
            self.assertEqual(status, "CONFIRMÉ")

    def test_gold_nasdaq_strategy_also_requires_m5_and_m15(self):
        for market in ("GOLD", "NASDAQ"):
            for idx in (2, 4):
                dirs = [1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1]
                dirs[idx] = -1
                strat, status, reason = ab.strategie_alignement(dirs, 1, 1, market)
                self.assertEqual(strat, "")
                self.assertEqual(status, "EN ATTENTE")
                self.assertIn("M5 et M15", reason)

    def test_gold_nasdaq_confirmation_helper_rejects_short_term_countertrend(self):
        aligned = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        self.assertEqual(ab.direction_confirmee_marche("GOLD", aligned, 1), 1)
        for idx in (2, 4, 7, 9):
            dirs = aligned.copy()
            dirs[idx] = -1
            self.assertEqual(ab.direction_confirmee_marche("GOLD", dirs, 1), 0)
            self.assertEqual(ab.direction_confirmee_marche("NASDAQ", dirs, 1), 0)
        self.assertEqual(ab.direction_confirmee_marche("BTC", [0] * 11, 1), 1)

    def test_cloture_direction_ignore_bougie_m5_m15_en_formation(self):
        closed = [candle(i * 60, o=100 + i, h=101 + i, l=99 + i, c=100 + i) for i in range(50)]
        forming = candle(50 * 60, o=150, h=151, l=-1001, c=-1000)
        series = {k: closed + [forming] if k in {"1", "5", "15", "30", "1h", "4h", "D"} else closed
                  for k in ab.UT}
        dirs = ab.directions_cloturees(series)
        self.assertEqual(dirs[2], 1)
        self.assertEqual(dirs[4], 1)
        self.assertEqual(ab.etat_ut(series["5"])[0], -1)

    def test_tendance_armee_ne_rearme_pas_gold_si_m5_m15_baissiers(self):
        dirs = [1] * 11
        dirs[2] = -1
        dirs[4] = -1
        r = {"market": "GOLD", "confirme": 0, "dirs": [1] * 11, "dirs_cloturees": dirs}
        cle = {"arme": 1}
        ab.tendance_armee(r, cle)
        self.assertEqual(r["confirme"], 0)
        self.assertEqual(cle["arme"], 0)
        self.assertFalse(r.get("repli"))

    def test_reprise_entree_gold_attend_le_realignement_des_quatre_ut(self):
        dirs = [1] * 11
        dirs[2] = -1
        r = {"t": 1000, "m1": [candle(900, c=100)], "b5": [candle(900)],
             "atr": 1.0, "dirs_cloturees": dirs}
        cle = {"reprise": {"d": 1, "e": 100.0, "sl": 98.0, "tp1": 104.0, "t": 900}}
        self.assertIsNone(ab.reprise_entree("GOLD", r, cle))
        self.assertIn("reprise", cle)

    def test_sniper_gold_nasdaq_refuse_m5_ou_m15_a_contre_sens(self):
        for market in ("GOLD", "NASDAQ"):
            for idx in (2, 4):
                dirs = [1] * 11
                dirs[idx] = -1
                proposal, reason = ab._sniper({"market": market, "dirPlan": 1, "dirs_cloturees": dirs})
                self.assertIsNone(proposal)
                self.assertIn("CONFLUENCE_M5_M15", reason)

    def test_btc_keeps_its_existing_scalping_rule(self):
        dirs = [1, 1, 1, 0, 1, 0, 0, 0, 0, -1, 0]
        strat, status, _ = ab.strategie_alignement(dirs, 1, 0, "BTC")
        self.assertEqual(strat, "SCALPING")
        self.assertEqual(status, "CONFIRMÉ")

    def test_gold_nasdaq_climax_is_watch_only_when_m5_m15_disagree_even_if_h1_h4_align(self):
        bars = [candle(i * 900) for i in range(80)]
        bars[-2] = candle(78 * 900, o=100, h=102, l=97, c=101, v=500)
        dirs = [1] * 11
        dirs[2], dirs[4] = -1, -1
        r = dict(b15_long=bars, dirs=dirs, dirs_cloturees=dirs, t=50000)
        for market in ("GOLD", "NASDAQ"):
            msg = ab.radar_climax(market, r, {})
            self.assertIn("RADAR CLIMAX — SURVEILLANCE", msg)
            self.assertIn("Clôtures M5=baissier, M15=baissier, H1=haussier, H4=haussier", msg)
            self.assertIn("aucune entrée", msg.lower())

    def test_gold_nasdaq_confirmed_climax_includes_tp1_tp2_and_risk_reward(self):
        bars = [candle(i * 900) for i in range(80)]
        bars[-2] = candle(78 * 900, o=100, h=102, l=97, c=101, v=500)
        dirs = [1] * 11
        r = dict(b15_long=bars, dirs=dirs, dirs_cloturees=dirs, t=50000,
                 atr=1.0, grosses=[(110.0, "4h"), (120.0, "Daily")])
        for market in ("GOLD", "NASDAQ"):
            msg = ab.radar_climax(market, r, {})
            self.assertIn("RETOURNEMENT CONFIRMÉ — LONG POSSIBLE", msg)
            self.assertIn("TP1 :", msg)
            self.assertIn("TP2 :", msg)
            self.assertIn("Gain/risque", msg)
            self.assertNotIn("sans TP", msg)

    def test_gold_nasdaq_climax_is_watch_only_without_h1_h4_confluence(self):
        bars = [candle(i * 900) for i in range(80)]
        bars[-2] = candle(78 * 900, o=100, h=102, l=97, c=101, v=500)
        dirs = [0] * 11
        dirs[7], dirs[9] = -1, -1
        r = dict(b15_long=bars, dirs=dirs, t=50000)
        for market in ("GOLD", "NASDAQ"):
            msg = ab.radar_climax(market, r, {})
            self.assertIn("RADAR CLIMAX — SURVEILLANCE", msg)
            self.assertIn("Pas de position", msg)
            self.assertNotIn("Entrée ≈", msg)
            self.assertNotIn("prenable", msg)

    def test_gold_nasdaq_reversal_is_observation_only_btc_keeps_legacy(self):
        for market in ("GOLD", "NASDAQ"):
            msg = ab.retournement_marche(market, reversal_r(LONG_GOLD, 500), {})
            self.assertIn("RETOURNEMENT EN OBSERVATION", msg)
            self.assertIn("PAS DE POSITION", msg)
            self.assertNotIn("Entrée ≈", msg)
            self.assertNotIn("Cible 1", msg)
            self.assertIsNone(ab.retournement_marche(market, reversal_r([1,1,1,0,1,0,0,1,0,1,0]), {}))
        msg_btc = ab.retournement_marche("BTC", reversal_r(LONG_BTC), {})
        self.assertIn("Cible 1", msg_btc)

    def test_manual_telegram_analysis_assigns_market_before_sniper(self):
        result = {"dirs": [0] * 11, "dirPlan": 0}
        seen = {}
        def capture_sniper(r):
            seen["market"] = r.get("market")
            return None
        with mock.patch.object(ab, "analyser", return_value=result) as analyser, \
             mock.patch.object(ab, "entree_sniper", side_effect=capture_sniper) as sniper, \
             mock.patch.object(ab, "tendance_armee"), \
             mock.patch.object(ab, "annonce_proche", return_value=""), \
             mock.patch.object(ab, "news_txt", return_value=""), \
             mock.patch.object(ab, "contexte_macro", return_value=""):
            out = ab.analyse_marche({"GOLD": {}}, "XAUUSD")
        analyser.assert_called_once()
        self.assertEqual(analyser.call_args.args[0], "XAUUSD")
        self.assertEqual(analyser.call_args.kwargs["market"], "GOLD")
        self.assertEqual(out["market"], "GOLD")
        self.assertEqual(seen["market"], "GOLD")
        sniper.assert_called_once_with(out)

    def test_gold_nasdaq_trigger_uses_last_closed_m5_not_forming_candle(self):
        closed = candle(300, o=100, h=100.5, l=99.5, c=100)
        forming = candle(600, o=100.2, h=100.9, l=99.5, c=100.8)
        r = {"b5": [closed, forming], "market": "GOLD"}
        self.assertEqual(ab.derniere_bougie_m5_declencheur(r, "GOLD"), closed)
        self.assertEqual(ab.derniere_bougie_m5_declencheur(r, "NASDAQ"), closed)
        self.assertEqual(ab.derniere_bougie_m5_declencheur(r, "BTC"), forming)
        self.assertIsNone(ab.rejet(r, 1, 100, 1.0))  # la mèche haussière provisoire n'est pas une clôture
        r["market"] = "BTC"
        self.assertIsNotNone(ab.rejet(r, 1, 100, 1.0))  # comportement BTC historique préservé

    def test_gold_nasdaq_breakout_waits_for_m5_close_btc_legacy_unchanged(self):
        bars = [candle(i * 300, o=99.8, h=100.0, l=99.5, c=99.8) for i in range(22)]
        candidate = candle(22 * 300, o=99.8, h=100.0, l=99.5, c=100.0)
        forming = candle(23 * 300, o=100.0, h=101.2, l=99.9, c=101.0)
        bars.extend([candidate, forming])
        r = {"b5": bars, "r5": [50, 50, 50], "atr": 1.0, "atr5": 1.0,
             "m1": [candle(23 * 60, c=101.0)], "grosses": [(105.0, "4h"), (110.0, "Daily")]}
        r["market"] = "GOLD"
        self.assertIsNone(ab.plan_cassure(r, 1))
        r["market"] = "NASDAQ"
        self.assertIsNone(ab.plan_cassure(r, 1))
        r["market"] = "BTC"
        self.assertIsNotNone(ab.plan_cassure(r, 1))

    def test_gold_nasdaq_confirmation_alert_requires_all_four_closed_timeframes(self):
        bars = [candle(0, c=98), candle(300, c=99), candle(600, c=101), candle(900, c=102)]
        for market in ("GOLD", "NASDAQ"):
            cases = ((1, 1, 0, False), (1, 1, 1, True), (-1, 1, 1, False), (1, -1, 1, False))
            for m5, m15, h4, expected in cases:
                dirs = [0, 0, m5, 0, m15, 0, 0, 1, 0, h4, 1]
                r = dict(comp=0, dirs=dirs, dirs_cloturees=dirs,
                         sniper=None, dirPlan=1, strat="DAY", zone_pine={"zmil": 100},
                         b5=bars, t=10000)
                with mock.patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)), \
                     mock.patch.object(ab, "hb_etat_surveille", return_value={"d": 1, "n": 9}), \
                     mock.patch.object(ab, "strategie_alignement", return_value=("DAY", "CONFIRMÉ")), \
                     mock.patch.object(ab, "trait_indicateur", return_value=None):
                    events = ab.evenements_pine({}, market, r, {}, 50000)
                has_confirmation = "confirmation" in [e["kind"] for e in events]
                self.assertEqual(has_confirmation, expected, (market, m5, m15, h4, events))

    def test_gold_nasdaq_do_not_emit_inverse_scalp_events_btc_keeps_legacy(self):
        r = dict(comp=0, dirs=[0,0,1,0,1,0,0,1,0,1,1],
                 sniper=None, dirPlan=1, strat="", zone_pine=None)
        fake_si = dict(d=-1, e=100.0)
        for market in ("GOLD", "NASDAQ"):
            with mock.patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)), \
                 mock.patch.object(ab, "hb_etat_surveille", return_value={"d": 1, "n": 9}), \
                 mock.patch.object(ab, "scalp_inverse", return_value=fake_si) as inverse, \
                 mock.patch.object(ab, "trait_indicateur", return_value=None):
                events = ab.evenements_pine({}, market, r, {}, 50000)
            inverse.assert_not_called()
            self.assertNotIn("scalp_inv", [e["kind"] for e in events])

        with mock.patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)), \
             mock.patch.object(ab, "hb_etat_surveille", return_value={"d": 1, "n": 9}), \
             mock.patch.object(ab, "scalp_inverse", return_value=fake_si) as inverse, \
             mock.patch.object(ab, "trait_indicateur", return_value=None):
            events = ab.evenements_pine({}, "BTC", r, {}, 50000)
        inverse.assert_called_once()
        self.assertIn("scalp_inv", [e["kind"] for e in events])


    def test_pine_v25_uses_closed_m5_m15_h1_h4_for_gold_nasdaq(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pine", "ALIGN_MTF_PRO_v25.pine")
        pine = open(path, encoding="utf-8").read()
        self.assertIn("isGoldNasdaq", pine)
        self.assertIn("lookahead=barmerge.lookahead_on", pine)
        self.assertIn("dirPlan = isGoldNasdaq and not gnConfluence ? 0 : dirStable", pine)
        self.assertIn("gnConfluence and dirStable == 1", pine)
        self.assertIn("gnConfluence and dirStable == -1", pine)

if __name__ == "__main__":
    unittest.main()
