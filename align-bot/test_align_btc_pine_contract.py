"""Contract tests for the dedicated BTC-only TradingView Pine indicator."""
from pathlib import Path
import unittest

PINE = Path(__file__).resolve().parent / "pine" / "ALIGN_BTC_MTF_PRO_v25.pine"


class AlignBtcPineContract(unittest.TestCase):
    def test_indicator_is_a_distinct_btc_only_script(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn('indicator("ALIGN BTC MTF PRO v25 (Dedicated)", shorttitle="ALIGN BTC v25"', source)
        self.assertIn('isBtc = str.contains(tickerUpper, "BTC") or str.contains(tickerUpper, "XBT")', source)
        self.assertIn("isGold = false", source)
        self.assertIn("isSupportedMarket = isBtc", source)
        self.assertIn('bridgeEnabled = input.bool(false, "Envoyer les snapshots au ROBOT V12", group=grpBridge)', source)
        self.assertIn('bridgeMarket = isBtc ? "BTCUSD" : "UNSUPPORTED"', source)
        self.assertIn('"source":"ALIGN_MTF_PRO_V25"', source)
        self.assertNotIn('bridgeMarket = isBtc ? "BTCUSD" : isGold ? "XAUUSD"', source)

    def test_btc_ui_and_bridge_use_the_strategy_specific_closed_mtf_gates(self):
        source = PINE.read_text(encoding="utf-8")
        bridge = next(line for line in source.splitlines() if line.startswith("bridgeClosedMtfOk = "))
        self.assertIn('strat == "SWING" ?', bridge)
        self.assertIn('strat == "DAY" ?', bridge)
        self.assertIn('strat == "SCALPING" ?', bridge)
        self.assertIn("nz(dDFermee) == dirPlan", bridge)
        self.assertIn("nz(dWFermee) != -dirPlan", bridge)
        self.assertIn("nz(d5Fermee) == dirPlan", bridge)
        self.assertIn("nz(d1Fermee) == dirPlan", bridge)
        self.assertIn("planConfirmedUi", source)
        self.assertIn("bridgeSignal = bridgeConfirmed ?", source)

    def test_gold_routing_is_not_present_in_the_dedicated_btc_export(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertNotIn('"XAUUSD"', source)
        self.assertNotIn('isGold = str.contains', source)
        self.assertIn('"UNSUPPORTED"', source)

    def test_every_timeframe_direction_comes_from_its_last_closed_candle(self):
        source = PINE.read_text(encoding="utf-8")
        for tf, name in (
            ('"1"', "d1Fermee"), ('"3"', "d3Fermee"), ('"5"', "d5Fermee"),
            ('"10"', "d10Fermee"), ('"15"', "d15Fermee"), ('"30"', "d30Fermee"),
            ('"45"', "d45Fermee"), ('"60"', "d60Fermee"), ('"120"', "d120Fermee"),
            ('"240"', "d240Fermee"), ('"D"', "dDFermee"), ('"W"', "dWFermee"),
        ):
            self.assertIn(name + ' = request.security(syminfo.tickerid, ' + tf + ', f_dir_confirme(), lookahead=barmerge.lookahead_on)', source)
        self.assertIn("dirs = array.from(nz(d1Fermee), nz(d3Fermee)", source)
        self.assertIn("dirBrut = zoneLongConfirmee ? 1 : zoneShortConfirmee ? -1 : longT >= 2 ? 1 : longT <= -2 ? -1 : 0", source)
        self.assertIn("dirStable = dirBrut", source)
        self.assertNotIn("var int dirStable = 0", source)

    def test_btc_strategy_and_entry_sl_targets_share_the_canonical_m15_plan(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn("uW = nz(dWFermee) == dP", source)
        self.assertIn("uD = nz(dDFermee) == dP", source)
        self.assertIn("d4Strat = nz(d240Fermee)", source)
        self.assertIn("d1hStrat = nz(d60Fermee)", source)
        self.assertIn("d15Strat = nz(d15Fermee)", source)
        self.assertIn("d5Strat = nz(d5Fermee)", source)
        self.assertIn("d1Strat = nz(d1Fermee)", source)
        self.assertIn("ent = entC", source)
        self.assertIn("tp1 = tp1C", source)
        self.assertIn("tp2 = tp2C", source)
        self.assertIn("sl = slC", source)
        self.assertNotIn("var float ent = na", source)
        self.assertNotIn("var int dirStable = 0", source)
        self.assertIn('request.security(syminfo.tickerid, "15", [open[1], ta.highest(high, 10)[1], ta.lowest(low, 10)[1], close[1]', source)

    def test_validation_score_and_risk_gate_use_canonical_m15_inputs(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn("distE = math.abs(planClose15 - ent)", source)
        self.assertIn("distE <= 0.5 * planAtr15", source)
        self.assertIn("volOk = not na(planVol15) and planVol15 > 0 and not na(planVolMoy15) and planVolMoy15 > 0", source)
        self.assertIn('rsiT = strat == "SWING" ? nz(r60Fermee, 50) : strat == "DAY" ? nz(r5Fermee, 50) : nz(r1Fermee, 50)', source)
        self.assertIn("sensPlan = longT > 0 ? 1 : longT < 0 ? -1 : 0", source)
        self.assertIn("planRiskRewardOk = not na(atr15) and atr15 > 0 and rrS >= 2.0 and planRisk <= 1.5 * atr15", source)
        self.assertIn("and planRiskRewardOk and not na(ent)", source)
        self.assertIn("bridgeConfirmed = bridgePlanValid and planRiskRewardOk", source)

    def test_plan_and_confirmation_are_independent_of_the_chart_timeframe(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn("longT += i >= 7 ? dv : 0", source)
        levels = source.split("f_dessus(refClose, refAtr) =>", 1)[1].split("[hau1, tH1, hau2, tH2]", 1)[0]
        self.assertIn("math.abs(v - a1) > refAtr * 0.3", levels)
        self.assertIn("math.abs(v - b1) > refAtr * 0.3", levels)
        self.assertNotIn("atrC", levels)
        self.assertIn("if voirPlan and planConfirmedUi", source)

    def test_entry_stop_targets_and_table_keep_explanatory_hover_text(self):
        source = PINE.read_text(encoding="utf-8")
        self.assertIn("eE := label.new", source)
        self.assertIn('tooltip="ENTRÉE ALIGN', source)
        self.assertIn('tooltip="Stop placé derrière', source)
        self.assertIn('tooltip="Objectif 1 :', source)
        self.assertIn('tooltip="Objectif 2 :', source)
        self.assertIn("tooltip=tip", source)
        self.assertIn('table.cell(t, 11, 0, "1W"', source)


if __name__ == "__main__":
    unittest.main()
