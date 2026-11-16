"""Régressions directionnelles : GOLD/NASDAQ ne publient pas d'entrées contre H1/H4."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def candle(t, o=100.0, h=101.0, l=99.0, c=100.0, v=100):
    return dict(t=t, o=o, h=h, l=l, c=c, v=v)


def retest_r(h4, d=1, h1=None):
    bars = [candle(i * 900) for i in range(40)]
    if d == 1:
        bars[20]["h"] = 102.0
        for i in range(34, 38):
            bars[i] = candle(i * 900, o=102.5, h=104.0, l=102.2, c=103.0)
        bars[38] = candle(38 * 900, o=102.2, h=103.0, l=101.9, c=102.5)
    else:
        bars[20]["l"] = 98.0
        for i in range(34, 38):
            bars[i] = candle(i * 900, o=97.5, h=97.8, l=96.0, c=97.0)
        bars[38] = candle(38 * 900, o=97.8, h=98.1, l=97.0, c=97.5)
    dirs = [0] * 11
    dirs[2], dirs[4], dirs[7], dirs[9] = d, d, d if h1 is None else h1, h4
    return dict(b15=bars, dirs=dirs, atr=1.0, t=40000)


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
    def test_gold_retest_requires_h1_and_h4_confirmation_both_directions(self):
        for d in (1, -1):
            self.assertIsNone(ab.entree_retest("GOLD", retest_r(0, d), {}))
            self.assertIsNone(ab.entree_retest("GOLD", retest_r(d, d, 0), {}))
            self.assertIsNone(ab.entree_retest("GOLD", retest_r(d, d, -d), {}))
            sens = "LONG" if d == 1 else "SHORT"
            self.assertIn(f"ENTRÉE SUR RETEST : {sens}", ab.entree_retest("GOLD", retest_r(d, d), {}))

    def test_nasdaq_retest_requires_h1_and_h4_confirmation_both_directions(self):
        for d in (1, -1):
            self.assertIsNone(ab.entree_retest("NASDAQ", retest_r(0, d), {}))
            self.assertIsNone(ab.entree_retest("NASDAQ", retest_r(d, d, 0), {}))
            self.assertIsNone(ab.entree_retest("NASDAQ", retest_r(d, d, -d), {}))
            sens = "LONG" if d == 1 else "SHORT"
            self.assertIn(f"ENTRÉE SUR RETEST : {sens}", ab.entree_retest("NASDAQ", retest_r(d, d), {}))

    def test_btc_retest_rule_is_unchanged(self):
        self.assertIn("ENTRÉE SUR RETEST : LONG", ab.entree_retest("BTC", retest_r(0), {}))

    def test_sniper_requires_both_h1_and_h4_for_gold_nasdaq_in_both_directions(self):
        for market in ("GOLD", "NASDAQ"):
            for d in (1, -1):
                for h1, h4 in ((d, 0), (0, d), (-d, -d), (d, -d), (-d, d)):
                    dirs = [0] * 11
                    dirs[7], dirs[9] = h1, h4
                    proposal, reason = ab._sniper({"market": market, "dirPlan": d, "dirs": dirs})
                    self.assertIsNone(proposal)
                    self.assertIn("CONFLUENCE_H1_H4", reason)
        _, reason_btc = ab._sniper({"market": "BTC", "dirPlan": 1, "dirs": [0,0,0,0,0,0,0,1,0,0,0]})
        self.assertNotIn("CONFLUENCE_H1_H4", reason_btc)

    def test_every_gold_nasdaq_strategy_requires_h1_and_h4_same_direction(self):
        for market in ("GOLD", "NASDAQ"):
            for d in (1, -1):
                for h1, h4 in ((d, 0), (0, d), (-d, -d), (d, -d), (-d, d)):
                    dirs = [d, d, d, 0, d, 0, 0, h1, 0, h4, d]
                    strat, status, reason = ab.strategie_alignement(dirs, d, d, market)
                    self.assertEqual(strat, "")
                    self.assertEqual(status, "EN ATTENTE")
                    self.assertIn("H4 et H1", reason)
                dirs = [d, d, d, 0, d, 0, 0, d, 0, d, d]
                strat, status, _ = ab.strategie_alignement(dirs, d, d, market)
                self.assertEqual(strat, "SWING")
                self.assertEqual(status, "CONFIRMÉ")

    def test_btc_keeps_its_existing_scalping_rule(self):
        dirs = [1, 1, 1, 0, 1, 0, 0, 0, 0, -1, 0]
        strat, status, _ = ab.strategie_alignement(dirs, 1, 0, "BTC")
        self.assertEqual(strat, "SCALPING")
        self.assertEqual(status, "CONFIRMÉ")

    def test_gold_nasdaq_h1_neutre_ne_rearme_pas_une_tendance_dans_les_deux_sens(self):
        for market in ("GOLD", "NASDAQ"):
            for d in (1, -1):
                r = {"market": market, "confirme": 0, "dirs": [0] * 11}
                r["dirs"][9] = d
                r["dirs"][7] = 0
                cle = {"arme": d}
                ab.tendance_armee(r, cle)
                self.assertEqual(r["confirme"], 0, (market, d))
                self.assertEqual(cle["arme"], 0, (market, d))

    def test_gold_nasdaq_h1_h4_alignes_peuvent_conserver_le_repli_dans_les_deux_sens(self):
        for market in ("GOLD", "NASDAQ"):
            for d in (1, -1):
                r = {"market": market, "confirme": 0, "dirs": [0] * 11}
                r["dirs"][9] = d
                r["dirs"][7] = d
                cle = {"arme": d}
                ab.tendance_armee(r, cle)
                self.assertEqual(r["confirme"], d, (market, d))
                self.assertTrue(r.get("repli"))

    def test_btc_garde_la_tolerance_h1_neutre_historique(self):
        for d in (1, -1):
            r = {"market": "BTC", "confirme": 0, "dirs": [0] * 11}
            r["dirs"][9] = d
            r["dirs"][7] = 0
            cle = {"arme": d}
            ab.tendance_armee(r, cle)
            self.assertEqual(r["confirme"], d)

    def test_confluence_finale_gold_nasdaq_exige_m5_m15_h1_h4_dans_les_deux_sens(self):
        for market in ("GOLD", "NASDAQ"):
            for d in (1, -1):
                dirs = [0] * 11
                for i in (2, 4, 7, 9):
                    dirs[i] = d
                r = {"market": market, "dirs": dirs}
                self.assertTrue(ab.confluence_entree_mtf(market, r, d))
                for i in (2, 4, 7, 9):
                    bad = list(dirs)
                    bad[i] = 0
                    self.assertFalse(ab.confluence_entree_mtf(market, {"dirs": bad}, d), (market, d, i))
        self.assertTrue(ab.confluence_entree_mtf("BTC", {"dirs": [0]}, 1))

    def test_reprise_position_gold_nasdaq_revalide_les_unites_actuelles(self):
        for market in ("GOLD", "NASDAQ"):
            for d in (1, -1):
                e, sl, tp = 100.0, 98.0, 104.0
                if d == -1:
                    sl, tp = 102.0, 96.0
                dirs = [0] * 11
                for i in (2, 4, 7, 9):
                    dirs[i] = d
                bars = [candle(0, o=99 if d == 1 else 101, c=100), candle(300)]
                r = {"t": 10000, "m1": [candle(0, c=e)], "b5": bars, "atr": 1.0, "dirs": dirs}
                cle = {"reprise": {"t": 9990, "d": d, "e": e, "sl": sl, "tp1": tp}}
                self.assertIn("REPRISE À L'ENTRÉE", ab.reprise_entree(market, r, cle))
                dirs[4] = -d
                cle = {"reprise": {"t": 9990, "d": d, "e": e, "sl": sl, "tp1": tp}}
                self.assertIsNone(ab.reprise_entree(market, dict(r, dirs=dirs), cle))

    def test_agent_ne_peut_pas_contourner_m15_par_cassure_ou_fvg(self):
        r = {
            "m1": [candle(0, c=100.0)], "r5": [50.0, 50.0], "posD": 0.5, "posW": 0.5,
            "confirme": 1, "dirs": [1, 1, 1, 0, -1, 0, 0, 1, 0, 1, 1],
            "t": 5000, "fermeture": False,
        }
        with mock.patch.object(ab, "manipulation"), \\
             mock.patch.object(ab, "meche_suspecte"), \\
             mock.patch.object(ab, "niveaux_cles"), \\
             mock.patch.object(ab, "resistance_fvg"), \\
             mock.patch.object(ab, "suivre_apres_sl"), \\
             mock.patch.object(ab, "reprise_entree", return_value=None), \\
             mock.patch.object(ab, "entree_retest", return_value=None), \\
             mock.patch.object(ab, "radar_climax", return_value=None), \\
             mock.patch.object(ab, "retournement_marche", return_value=None), \\
             mock.patch.object(ab, "plan_cassure") as cassure, \\
             mock.patch.object(ab, "point_entree") as fvg:
            out = ab.agent("GOLD", r, {}, "")
        cassure.assert_not_called()
        fvg.assert_not_called()
        self.assertTrue(any("ANTICIPATION uniquement" in x for x in out))

    def test_gold_nasdaq_climax_is_watch_only_without_h1_h4_confluence(self):
        dirs = [0] * 11
        dirs[7], dirs[9] = -1, -1
        for market, source in (("GOLD", "COMEX GC=F Yahoo proxy"), ("NASDAQ", "CME NQ=F Yahoo proxy")):
            bars = [dict(candle(i * 900), volume_source=source) for i in range(80)]
            bars[-2] = dict(candle(78 * 900, o=100, h=102, l=97, c=101, v=500), volume_source=source)
            r = dict(b15_long=bars, dirs=dirs, t=50000)
            msg = ab.radar_climax(market, r, {})
            self.assertIn("RADAR CLIMAX — SURVEILLANCE", msg)
            self.assertIn("Pas de position", msg)
            self.assertNotIn("Entrée ≈", msg)
            self.assertNotIn("prenable", msg)

    def test_gold_climax_rejects_paxg_token_volume_as_market_volume(self):
        bars = [dict(candle(i * 900), volume_source="Kraken PAXGUSD") for i in range(80)]
        bars[-2] = dict(candle(78 * 900, o=100, h=102, l=97, c=101, v=500), volume_source="Kraken PAXGUSD")
        dirs = [0] * 11
        dirs[7], dirs[9] = -1, -1
        r = dict(b15_long=bars, dirs=dirs, t=50000)
        self.assertIsNone(ab.radar_climax("GOLD", r, {}))

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

    def test_gold_nasdaq_confirmation_alert_requires_h1_and_h4(self):
        bars = [candle(0, c=98), candle(300, c=99), candle(600, c=101), candle(900, c=102)]
        for market in ("GOLD", "NASDAQ"):
            for h4, expected in ((0, False), (1, True)):
                r = dict(comp=0, dirs=[0, 0, 1, 0, 1, 0, 0, 1, 0, h4, 1],
                         sniper=None, dirPlan=1, strat="DAY", zone_pine={"zmil": 100},
                         b5=bars, t=10000)
                with mock.patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)), \
                     mock.patch.object(ab, "hb_etat_surveille", return_value={"d": 1, "n": 9}), \
                     mock.patch.object(ab, "strategie_alignement", return_value=("DAY", "CONFIRMÉ")), \
                     mock.patch.object(ab, "trait_indicateur", return_value=None):
                    events = ab.evenements_pine({}, market, r, {}, 50000)
                has_confirmation = "confirmation" in [e["kind"] for e in events]
                self.assertEqual(has_confirmation, expected, (market, h4, events))

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


if __name__ == "__main__":
    unittest.main()
