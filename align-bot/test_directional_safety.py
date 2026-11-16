"""Garde-fous directionnels Gold/NASDAQ ; BTC conserve sa logique historique."""
import os, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def candle(t, o=100.0, h=101.0, l=99.0, c=100.0, v=100):
    return dict(t=t, o=o, h=h, l=l, c=c, v=v)


def retest_r(h4):
    bars = [candle(i * 900) for i in range(40)]
    bars[20]["h"] = 102.0
    for i in range(33, 38):
        bars[i] = candle(i * 900, o=102.5, h=104.0, l=102.2, c=103.0)
    bars[38] = candle(38 * 900, o=102.2, h=103.0, l=101.9, c=102.5)
    dirs = [0] * 11
    dirs[2], dirs[4], dirs[7], dirs[9] = 1, 1, 1, h4
    return dict(b15=bars, dirs=dirs, atr=1.0, t=40000)


def sniper_r(market, h1, h4):
    dirs = [1] * 11
    dirs[7], dirs[9] = h1, h4
    bars1 = [candle(i * 60) for i in range(50)]
    return dict(market=market, dirPlan=1, dirs=dirs, atr3=1.0, atr=1.0, atr5=1.0,
                zone_pine={"za": 90.0, "zb": 110.0}, m1=bars1,
                b3=[candle(i * 180) for i in range(20)],
                b5=[candle(i * 300) for i in range(12)],
                b15=[candle(i * 900) for i in range(12)],
                bull=11, bear=0, sens=1, niveaux=[])


class DirectionSafety(unittest.TestCase):
    def test_gold_retest_requires_h4_confirmation(self):
        self.assertIsNone(ab.entree_retest("GOLD", retest_r(0), {}))
        self.assertIn("ENTRÉE SUR RETEST : LONG", ab.entree_retest("GOLD", retest_r(1), {}))

    def test_nasdaq_retest_requires_h4_confirmation(self):
        self.assertIsNone(ab.entree_retest("NASDAQ", retest_r(0), {}))
        self.assertIn("ENTRÉE SUR RETEST : LONG", ab.entree_retest("NASDAQ", retest_r(1), {}))

    def test_btc_retest_rule_remains_unchanged(self):
        self.assertIn("ENTRÉE SUR RETEST : LONG", ab.entree_retest("BTC", retest_r(0), {}))

    def test_sniper_requires_h1_and_h4_same_direction_for_gold_nasdaq(self):
        for market in ("GOLD", "NASDAQ"):
            proposal, reason = ab._sniper(sniper_r(market, 1, 0))
            self.assertIsNone(proposal)
            self.assertIn("CONTEXTE_HTF", reason)
            proposal, reason = ab._sniper(sniper_r(market, 1, -1))
            self.assertIsNone(proposal)
            self.assertIn("CONTEXTE_HTF", reason)

    def test_btc_sniper_htf_rule_is_not_changed(self):
        r = sniper_r("BTC", 1, 0)
        with mock.patch.object(ab, "niveaux_structure_ut", return_value={}), \
             mock.patch.object(ab, "niveaux_ut", return_value=(None, None, None, None)):
            _, reason = ab._sniper(r)
        self.assertNotIn("CONTEXTE_HTF", reason)

    def test_gold_nasdaq_climax_is_watch_only_without_h1_h4_confluence(self):
        bars = [candle(i * 900) for i in range(80)]
        bars[-2] = candle(78 * 900, o=100, h=102, l=97, c=101, v=500)
        dirs = [0] * 11
        dirs[7], dirs[9] = -1, -1
        r = dict(b15_long=bars, dirs=dirs, t=50000)
        for market in ("GOLD", "NASDAQ"):
            msg = ab.radar_climax(market, r, {})
            self.assertIn("RADAR CLIMAX — SURVEILLANCE", msg)
            self.assertIn("Observation uniquement", msg)
            self.assertNotIn("Entrée ≈", msg)
            self.assertNotIn("prenable", msg)

    def test_gold_nasdaq_do_not_emit_inverse_scalp_events_btc_keeps_legacy(self):
        r = dict(comp=0, dirs=[0, 0, 1, 0, 1, 0, 0, 1, 0, 1, 1],
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
