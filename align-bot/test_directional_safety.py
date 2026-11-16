"""Régressions directionnelles : GOLD/NASDAQ ne publient pas d'entrées contre H1/H4."""
import os
import sys
import unittest
import time
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab
from test_entree_retest import serie as serie_retest


def candle(t, o=100.0, h=101.0, l=99.0, c=100.0, v=100):
    return dict(t=t, o=o, h=h, l=l, c=c, v=v)


def retest_r(h4):
    # Source unique du scénario retest, partagé avec les tests unitaires dédiés.
    r = serie_retest()
    dirs = list(r["dirs"])
    dirs[9] = h4
    r["dirs"] = dirs
    r["dirs_cloturees"] = dirs.copy()
    return r

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
        self.assertIn("ENTRÉE POSSIBLE SUR RETEST : LONG", ab.entree_retest("GOLD", retest_r(1), {}))

    def test_nasdaq_retest_requires_h4_confirmation(self):
        self.assertIsNone(ab.entree_retest("NASDAQ", retest_r(0), {}))
        self.assertIn("ENTRÉE POSSIBLE SUR RETEST : LONG", ab.entree_retest("NASDAQ", retest_r(1), {}))

    def test_btc_retest_rule_is_unchanged(self):
        with mock.patch.object(ab, "objectifs", side_effect=AssertionError("BTC must keep its historical retest path")):
            message = ab.entree_retest("BTC", retest_r(0), {})
        self.assertIn("ENTRÉE SUR RETEST : LONG", message)
        self.assertNotIn("TP2", message)

    def test_rejected_gold_risk_does_not_consume_retest_cooldown(self):
        cle = {}
        with mock.patch.object(ab, "objectifs", return_value=((99.0, "invalid"), (98.0, "invalid"))):
            self.assertIsNone(ab.entree_retest("GOLD", retest_r(1), cle))
        self.assertFalse(cle.get("retest_vu"))

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

    def test_btc_keeps_its_existing_scalping_rule(self):
        dirs = [1, 1, 1, 0, 1, 0, 0, 0, 0, -1, 0]
        strat, status, _ = ab.strategie_alignement(dirs, 1, 0, "BTC")
        self.assertEqual(strat, "SCALPING")
        self.assertEqual(status, "CONFIRMÉ")

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

    def test_gold_nasdaq_confirmation_alert_requires_h1_and_h4(self):
        now = int(time.time())
        bars = [candle(now - 900, c=98), candle(now - 600, c=99),
                candle(now - 300, c=101), candle(now, c=102)]
        for market in ("GOLD", "NASDAQ"):
            for h4, expected in ((0, False), (1, True)):
                dirs = [0, 0, 1, 0, 1, 0, 0, 1, 0, h4, 1]
                r = dict(comp=0, dirs=dirs, dirs_cloturees=dirs,
                         sniper=None, dirPlan=1, strat="DAY", zone_pine={"zmil": 100},
                         b5=bars, b15=[candle(now - 1800), candle(now - 900)],
                         b1h=[candle(now - 7200), candle(now - 3600)],
                         b4h=[candle(now - 28800), candle(now - 14400)],
                         m1=[candle(now - 30, c=102)], atr5=1.0, atr=1.0, t=now)
                with mock.patch.object(ab, "etat_marche_hb", return_value=("ouvert", None)), \
                     mock.patch.object(ab, "hb_etat_surveille", return_value={"d": 1, "n": 9}), \
                     mock.patch.object(ab, "strategie_alignement", return_value=("DAY", "CONFIRMÉ")), \
                     mock.patch.object(ab, "trait_indicateur", return_value=None):
                    events = ab.evenements_pine({}, market, r, {}, now)
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
