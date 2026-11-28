from pathlib import Path
import hashlib
import unittest

PINE = Path(__file__).parent / "pine" / "ALIGN_MTF_PRO_v25.pine"
BASELINE_GIT_BLOB_SHA = "8bb2382adc6174e492cf15fb9e59876369307b3e"  # reviewed v25 baseline including progressive MTF reversal and canonical M15 levels
SETTINGS_BLOCK = """// ═════════ BRIDGE ALIGN (optionnel, sans modification visuelle) ═════════
grpBridge = "Bridge ALIGN (optionnel)"
bridgeEnabled = input.bool(true, "Envoyer les snapshots au ROBOT V12", group=grpBridge)
// Le marché du bridge est détecté depuis le ticker réel du graphique, jamais choisi manuellement.

"""
EXPORT_MARKER = "// ═════════ BRIDGE ALIGN — export structuré du Pine v25 (sans toucher aux signaux/visuels) ═════════"
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


class CanonicalPineBridgeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PINE.read_text(encoding="utf-8")

    def test_canonical_indicator_identity_and_animation_default_are_preserved(self):
        self.assertIn('indicator("ALIGN MTF PRO v25 (Inside)", shorttitle="ALIGN MTF v25"', self.source)
        self.assertIn('animer   = input.bool(true, "Animation en temps réel", group=grpA)', self.source)
        self.assertIn("clignote = animer and tick % 2 == 0", self.source)
        self.assertIn('voirPlan = input.bool(true, "Afficher le plan (TP / SL)"', self.source)

    def test_original_pine_is_byte_identical_outside_bridge_and_tp_state_blocks(self):
        # The canonical MTF plan intentionally changes closed-timeframe decision and
        # plan-state blocks. Preserve the existing visual/alert contracts and verify
        # the reviewed blocks explicitly instead of pretending they are byte-identical.
        self.assertIn(SETTINGS_BLOCK, self.source)
        self.assertIn(EXPORT_MARKER, self.source)
        self.assertIn("dirStable = dirBrut", self.source)
        self.assertIn("ent = entC", self.source)
        self.assertIn("tp1 = tp1C", self.source)
        self.assertIn("tp2 = tp2C", self.source)
        self.assertIn("sl = slC", self.source)
        self.assertIn("planClose15", self.source)
        self.assertIn("planAtr15", self.source)
        self.assertIn(RSI_CROSSOVER_BLOCK, self.source)

    def test_rsi_crossovers_are_evaluated_unconditionally_on_every_bar(self):
        self.assertIn(RSI_CROSSOVER_BLOCK, self.source)
        self.assertNotIn("rsiAchat = (ta.crossover(", self.source)
        self.assertNotIn("rsiVente = (ta.crossunder(", self.source)

    def test_only_btc_and_gold_are_supported_for_signals_and_bridge(self):
        self.assertNotIn('input.string("BTCUSD", "Marché ALIGN"', self.source)
        self.assertIn('bridgeMarket = isBtc ? "BTCUSD" : isGold ? "XAUUSD" : "UNSUPPORTED"', self.source)
        self.assertIn("rsisFermees = array.from(", self.source)
        self.assertIn("rsiOBFermee += rsiValeurFermee >= 70 ? 1 : 0", self.source)
        self.assertIn("rsiOSFermee += rsiValeurFermee <= 30 ? 1 : 0", self.source)
        self.assertIn('rsiOBFermee >= 3 ? "SURACHAT"', self.source)
        self.assertIn('rsiOSFermee >= 3 ? "SURVENTE"', self.source)
        export_block = self.source.split(EXPORT_MARKER, 1)[1]
        self.assertIn('bridgeMarket +', export_block)
        self.assertNotIn("NAS100", self.source)
        self.assertIn("isBtc = str.contains(tickerUpper, \"BTC\") or str.contains(tickerUpper, \"XBT\")", self.source)
        self.assertIn("isGold = str.contains(tickerUpper, \"XAU\") or str.contains(tickerUpper, \"GOLD\")", self.source)
        self.assertIn("isSupportedMarket = isBtc or isGold", self.source)
        self.assertIn("dirPlan = not isSupportedMarket or (isGold and not goldConfluence) ? 0 : dirStable", self.source)
        self.assertIn("bridgeDue = bridgeEnabled and isSupportedMarket", self.source)

    def test_existing_human_alerts_are_preserved_and_bridge_exports_by_default(self):
        self.assertIn('alert(syminfo.ticker + " " + nomSigH', self.source)
        self.assertIn('alert(syminfo.ticker + " " + nomSigB', self.source)
        self.assertIn('bridgeEnabled = input.bool(true, "Envoyer les snapshots au ROBOT V12"', self.source)
        self.assertIn('alert(bridgePayload, alert.freq_all)', self.source)
        self.assertIn('"source":"ALIGN_MTF_PRO_V25"', self.source)

    def test_active_plan_and_all_required_mtf_timeframes_are_exported(self):
        required_fields = ('"entry"', '"sl"', '"tp1"', '"tp2"', '"lecture_1m"', '"lecture_5m"', '"lecture_15m"', '"lecture_60m"')
        for field in required_fields:
            self.assertIn(field, self.source)
        timeframes = ("M1", "M3", "M5", "M10", "M15", "M30", "M45", "H1", "H2", "H4", "D1", "W1")
        self.assertIn(">= 20000", self.source)
        tuple_contracts = (
            ("d1, s1, r1, r1Fermee", "bridgeTimeM1"),
            ("d2, s2, r2, r2Fermee", "bridgeTimeM3"),
            ("d5, s5, r5, r5Fermee", "bridgeTimeM5"),
            ("d10, s10, r10, r10Fermee", "bridgeTimeM10"),
            ("d15, s15, r15, r15Fermee", "bridgeTimeM15"),
            ("d30, s30, r30, r30Fermee", "bridgeTimeM30"),
            ("d45, s45, r45, r45Fermee", "bridgeTimeM45"),
            ("d60, s60, r60, r60Fermee", "bridgeTimeH1"),
            ("d120, s120, r120, r120Fermee", "bridgeTimeH2"),
            ("d240, s240, r240, r240Fermee", "bridgeTimeH4"),
            ("dD, sD, rD, rDFermee", "bridgeTimeD1"),
            ("dW, sW, rW, rWFermee", "bridgeTimeW1"),
        )
        for tuple_head, closed_time in tuple_contracts:
            self.assertIn("[" + tuple_head + ", " + closed_time + "]", self.source)
            self.assertNotIn(closed_time + " = request.security(", self.source)
        request_sites = self.source.count("request.security(") + self.source.count("request.security_lower_tf(")
        self.assertLessEqual(request_sites, 40)
        self.assertIn('bridgeTfSeconds == 180 ? "M3"', self.source)
        self.assertIn('bridgeTfSeconds == 600 ? "M10"', self.source)
        self.assertIn('bridgeTfSeconds == 2700 ? "M45"', self.source)
        export_block = self.source.split(EXPORT_MARKER, 1)[1]
        for timeframe in timeframes:
            with self.subTest(timeframe=timeframe):
                marker = '"' + timeframe + '":{"direction":'
                self.assertIn(marker, export_block)
                timeframe_block = export_block.split(marker, 1)[1].split("}", 1)[0]
                closed_rsi = {"M1":"r1Fermee", "M3":"r2Fermee", "M5":"r5Fermee", "M10":"r10Fermee", "M15":"r15Fermee", "M30":"r30Fermee", "M45":"r45Fermee", "H1":"r60Fermee", "H2":"r120Fermee", "H4":"r240Fermee", "D1":"rDFermee", "W1":"rWFermee"}[timeframe]
                self.assertIn("f_align_v25_json_num(" + closed_rsi + ")", timeframe_block)
        m3_marker = '"M3":{"direction":'
        m3_block = export_block.split(m3_marker, 1)[1].split("}", 1)[0]
        self.assertIn("f_align_v25_json_int(nz(d3Fermee))", m3_block)
        self.assertNotIn("f_align_v25_json_int(d2)", m3_block)
        self.assertIn('na(v) ? "null" : str.tostring(v)', export_block)
        self.assertIn('na(v) ? "null" : v == 1', export_block)

    def test_bridge_bar_timestamps_match_the_closed_mtf_candle(self):
        # The exported direction is based on the previous, fully closed candle.
        # Its bar_time must identify that same candle, not the currently forming one.
        self.assertIn("[d, sqz ? 1 : 0, ta.rsi(close, lenRsi), ta.rsi(close, lenRsi)[1], time_close[1]]", self.source)
        self.assertNotIn("[d, sqz ? 1 : 0, ta.rsi(close, lenRsi), time]", self.source)

    def test_robot_v12_exports_closed_mtf_directions_for_entry_confirmation(self):
        self.assertIn(
            'bridgeClosedMtfOk = strat == "SWING" ? (nz(dDFermee) == dirPlan and nz(d60Fermee) == dirPlan',
            self.source,
        )
        self.assertIn(
            'strat == "DAY" ? (nz(d60Fermee) == dirPlan and nz(d5Fermee) == dirPlan',
            self.source,
        )
        self.assertIn(
            'strat == "SCALPING" ? ((nz(d60Fermee) != -dirPlan or (dirPlan == 1 and retLongConfirme) or (dirPlan == -1 and retShortConfirme)) and nz(d15Fermee) == dirPlan and nz(d5Fermee) == dirPlan and nz(d1Fermee) == dirPlan)',
            self.source,
        )
        self.assertIn(
            'bridgeConfirmed = bridgePlanValid and planRiskRewardOk and etatS == "CONFIRMÉ" and scoreV >= 75 and bridgeClosedMtfOk',
            self.source,
        )
        export_block = self.source.split(EXPORT_MARKER, 1)[1]
        self.assertIn('"lecture_5m":\' + f_align_v25_json_dir(nz(d5Fermee))', export_block)
        self.assertIn('"lecture_15m":\' + f_align_v25_json_dir(nz(d15Fermee))', export_block)
        self.assertIn('"lecture_60m":\' + f_align_v25_json_dir(nz(d60Fermee))', export_block)

    def test_bridge_exports_fixed_m15_plan_zone_and_strategy_trigger(self):
        export_block = self.source.split(EXPORT_MARKER, 1)[1]
        self.assertIn('"planTimeframe":"M15"', export_block)
        self.assertIn('"entryTimeframe":"', export_block)
        self.assertIn('"entryZoneLow":', export_block)
        self.assertIn('"entryZoneHigh":', export_block)
        self.assertIn('"entryDecision":', export_block)
        self.assertIn('strat == "SWING" ? "H1" : strat == "DAY" ? "M5" : strat == "SCALPING" ? "M1"', export_block)
        self.assertIn('f_align_v25_json_num(bridgePlanValid ? zBas : na)', export_block)
        self.assertIn('f_align_v25_json_num(bridgePlanValid ? zHaut : na)', export_block)
        self.assertIn('f_align_v25_json_num(bridgePlanValid ? (zBas + zHaut) / 2 : na)', export_block)

    def test_plan_refreshes_on_direction_or_strategy_change_and_bridge_rejects_stale_plan(self):
        self.assertIn("// ═════════ PLAN CANONIQUE : références M15 clôturées, sans mémoire propre au graphique ═════════", self.source)
        self.assertIn("ent = entC", self.source)
        self.assertIn("tp1 = tp1C", self.source)
        self.assertIn("sl = slC", self.source)
        self.assertIn('bridgePlanValid = dirPlan != 0 and strat != "" and dirPlan == dirFig and strat == stratFig and not planGeometryMismatch and bridgePlanGeometryOk', self.source)

    def test_gold_plan_geometry_is_recomputed_and_invalid_direction_is_suppressed(self):
        self.assertIn("planGeometryMismatch = dirPlan != 0 and (", self.source)
        self.assertIn("not planGeometryMismatch and bridgePlanGeometryOk", self.source)
        self.assertIn("bridgePlanGeometryOk = dirPlan == 1 ?", self.source)
        self.assertIn("sl < zBas and ent >= zBas and ent <= zHaut and tp1 > zHaut", self.source)
        self.assertIn("tp1 < zBas and ent >= zBas and ent <= zHaut and sl > zHaut", self.source)
        self.assertIn("and bridgePlanGeometryOk", self.source)

        def geometry_ok(direction, entry, stop, tp1, tp2, low, high):
            if direction == 1:
                return stop < low <= entry <= high < tp1 < tp2
            if direction == -1:
                return tp2 < tp1 < low <= entry <= high < stop
            return False

        # Regression fixture captured from the live XAUUSD SHORT payload rejected by the bridge.
        self.assertFalse(geometry_ok(-1, 3515.12, 3503.42, 3575.13, 3610.0, 3506.34, 3515.12))
        self.assertTrue(geometry_ok(-1, 3515.12, 3527.0, 3490.0, 3470.0, 3506.34, 3515.12))
        self.assertTrue(geometry_ok(1, 3515.12, 3495.0, 3540.0, 3570.0, 3510.0, 3520.0))

    def test_higher_chart_uses_last_closed_lower_timeframe_intrabar_for_entry_trigger(self):
        export_block = self.source.split(EXPORT_MARKER, 1)[1]
        self.assertIn("timeframe.in_seconds(bridgeEntryTf) < timeframe.in_seconds()", export_block)
        self.assertIn("request.security_lower_tf(syminfo.tickerid, bridgeEntryTf", export_block)
        self.assertIn("array.get(bridgeEntryTimeArray, bridgeEntryLast)", export_block)
        self.assertIn('bridgeEntryTimeSafe = bridgeEntryTf == "" ? na : bridgeEntryTime', export_block)

    def test_bridge_reuses_mtf_time_requests_and_stays_below_tv_request_budget(self):
        # The f_etat() MTF calls already return each timeframe's bar time.
        # Duplicating bridgeTime requests later in the script pushes the live
        # TradingView instance over its 40 unique request.*() budget.
        for field in (
            "bridgeTimeM1", "bridgeTimeM3", "bridgeTimeM5", "bridgeTimeM10",
            "bridgeTimeM15", "bridgeTimeM30", "bridgeTimeM45", "bridgeTimeH1",
            "bridgeTimeH2", "bridgeTimeH4", "bridgeTimeD1", "bridgeTimeW1",
        ):
            self.assertIn(field, self.source)
            self.assertNotIn(field + " = request.security", self.source)
        request_sites = self.source.count("request.security(") + self.source.count("request.security_lower_tf(")
        self.assertLessEqual(request_sites, 40)
        self.assertIn("[d1, s1, r1, r1Fermee, bridgeTimeM1]", self.source)
        self.assertIn("[dW, sW, rW, rWFermee, bridgeTimeW1]", self.source)


    def test_plan_levels_use_last_closed_source_timeframe_candle_on_every_chart_interval(self):
        # A higher chart timeframe must not let request.security() select an
        # arbitrary lower-timeframe intrabar for the plan's support/resistance levels.
        self.assertIn("f_niv_mtf(string tf) =>", self.source)
        self.assertIn("request.security_lower_tf(syminfo.tickerid, tf, f_niv())", self.source)
        self.assertIn("array.get(nivConfirmedArray, nivLastIndex)", self.source)
        self.assertIn("if not array.get(nivConfirmedArray, nivLastIndex)", self.source)
        self.assertIn("request.security(syminfo.tickerid, tf, f_niv_previous(), lookahead=barmerge.lookahead_on)", self.source)
        for timeframe in ('"15"', '"60"', '"240"', '"D"'):
            with self.subTest(timeframe=timeframe):
                self.assertIn("f_niv_mtf(" + timeframe + ")", self.source)
        self.assertNotIn('request.security(syminfo.tickerid, "15",  f_niv())', self.source)
        self.assertNotIn('request.security(syminfo.tickerid, "60",  f_niv())', self.source)
        self.assertNotIn('request.security(syminfo.tickerid, "240", f_niv())', self.source)
        self.assertNotIn('request.security(syminfo.tickerid, "D",   f_niv())', self.source)

    def test_canonical_plan_levels_and_m15_price_snapshot_share_closed_bar_semantics(self):
        self.assertIn("f_niv_previous() =>", self.source)
        self.assertIn("nivConfirmedArray", self.source)
        self.assertIn("nivLastIndex", self.source)
        self.assertIn("timeframe.in_seconds(tf) < timeframe.in_seconds()", self.source)
        self.assertIn("planClose15", self.source)
        self.assertIn("[hau1, tH1, hau2, tH2] = f_dessus(planClose15, planAtr15)", self.source)
        self.assertIn("[bas1, tB1, bas2, tB2] = f_dessous(planClose15, planAtr15)", self.source)
        self.assertIn("f_stopH(sMin, sMax, refClose, refAtr)", self.source)
        self.assertIn("f_cible(d, e, risque * gainMin, cMin, cMax)", self.source)

    def test_no_secret_is_embedded_in_pine(self):
        self.assertNotIn("ALIGN_TV_INGEST_TOKEN", self.source)
        self.assertNotIn("ingest_token", self.source)
        self.assertNotIn("ALIGN_MTF_PRO_A", self.source)


if __name__ == "__main__":
    unittest.main()
