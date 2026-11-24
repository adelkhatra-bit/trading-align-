from pathlib import Path
import hashlib
import unittest

PINE = Path(__file__).parent / "pine" / "ALIGN_MTF_PRO_v25.pine"
BASELINE_GIT_BLOB_SHA = "578c0a1f58c03e658c42c91aeeca37e865e31e7c"  # v25 : ancienne base b49cb3ff… + suppression demandée par Adel du point ENTRÉE (ligne + étiquette) ; rien d'autre ne change
SETTINGS_BLOCK = """// ═════════ BRIDGE ALIGN (optionnel, sans modification visuelle) ═════════
grpBridge = "Bridge ALIGN (optionnel)"
bridgeEnabled = input.bool(true, "Envoyer les snapshots au ROBOT V12", group=grpBridge)
// Le marché est routé automatiquement depuis le ticker du graphique.

"""
EXPORT_MARKER = "// ═════════ BRIDGE ALIGN — export structuré du Pine v25 (sans toucher aux signaux/visuels) ═════════"


class CanonicalPineBridgeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PINE.read_text(encoding="utf-8")

    def test_canonical_indicator_identity_and_animation_default_are_preserved(self):
        self.assertIn('indicator("ALIGN MTF PRO v25 (Inside)", shorttitle="ALIGN MTF v25"', self.source)
        self.assertIn('animer   = input.bool(true, "Animation en temps réel", group=grpA)', self.source)
        self.assertIn("clignote = animer and tick % 2 == 0", self.source)
        self.assertIn('voirPlan = input.bool(true, "Afficher le plan (TP / SL)"', self.source)

    def test_original_pine_is_byte_identical_outside_the_two_bridge_blocks(self):
        self.assertIn(SETTINGS_BLOCK, self.source)
        self.assertIn(EXPORT_MARKER, self.source)
        without_settings = self.source.replace(SETTINGS_BLOCK, "", 1)
        without_export = without_settings.split(EXPORT_MARKER, 1)[0]
        if without_export.endswith("\n\n"):
            without_export = without_export[:-1]
        raw = without_export.encode("utf-8")
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        self.assertEqual(git_blob, BASELINE_GIT_BLOB_SHA)

    def test_only_btc_and_gold_are_supported_for_signals_and_bridge(self):
        self.assertNotIn('input.string("BTCUSD", "Marché ALIGN"', self.source)
        self.assertIn('bridgeMarket = isBtc ? "BTCUSD" : isGold ? "XAUUSD" : "UNSUPPORTED"', self.source)
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
        for key in ('"entry"', '"sl"', '"tp1"', '"tp2"', '"lecture_1m"', '"lecture_5m"', '"lecture_15m"', '"lecture_60m"'):
            self.assertIn(key, self.source)
        for tf in ("M1", "M3", "M5", "M10", "M15", "M30", "M45", "H1", "H2", "H4", "D1", "W1"):
            self.assertIn('"' + tf + '"', self.source)
        self.assertIn(">= 20000", self.source)
        self.assertLessEqual(self.source.count("request.security("), 40)
        for variable, tf in (("bridgeTimeM3", "3"), ("bridgeTimeM10", "10"), ("bridgeTimeM45", "45")):
            self.assertIn(f'{variable} = request.security(syminfo.tickerid, "{tf}", time, lookahead=barmerge.lookahead_off)', self.source)
        self.assertIn('bridgeTfSeconds == 180 ? "M3"', self.source)
        self.assertIn('bridgeTfSeconds == 600 ? "M10"', self.source)
        self.assertIn('bridgeTfSeconds == 2700 ? "M45"', self.source)
        export_block = self.source.split(EXPORT_MARKER, 1)[1]
        expected_m3 = '''"M3":{"direction":' + f_align_v25_json_int(d2) + ',"rsi":' + f_align_v25_json_num(r2)'''
        wrong_m3 = '''"M3":{"direction":' + f_align_v25_json_int(d3) + ',"rsi":' + f_align_v25_json_num(r3)'''
        self.assertIn(expected_m3, export_block)
        self.assertNotIn(wrong_m3, export_block)
        for missing_value_fallback in ("f_align_v25_json_num(nz(r1, 50))", "f_align_v25_json_num(nz(r5, 50))", "f_align_v25_json_num(nz(r15, 50))", "f_align_v25_json_num(nz(r60, 50))", "str.tostring(nz(d1))"):
            self.assertNotIn(missing_value_fallback, export_block)
        self.assertIn('na(v) ? "null" : str.tostring(v)', export_block)
        self.assertIn('na(v) ? "null" : v == 1', export_block)

    def test_robot_v12_exports_closed_mtf_directions_for_entry_confirmation(self):
        self.assertIn(
            "bridgeClosedMtfOk = isGold ? (nz(d5Fermee) == dirPlan and nz(d15Fermee) == dirPlan and nz(d60Fermee) == dirPlan and nz(d240Fermee) == dirPlan) : (nz(d60Fermee) == dirPlan)",
            self.source,
        )
        self.assertIn(
            'bridgeConfirmed = bridgePlanValid and etatS == "CONFIRMÉ" and scoreV >= 75 and bridgeClosedMtfOk',
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

    def test_higher_chart_uses_last_closed_lower_timeframe_intrabar_for_entry_trigger(self):
        export_block = self.source.split(EXPORT_MARKER, 1)[1]
        self.assertIn("timeframe.in_seconds(bridgeEntryTf) < timeframe.in_seconds()", export_block)
        self.assertIn("request.security_lower_tf(syminfo.tickerid, bridgeEntryTf", export_block)
        self.assertIn("array.get(bridgeEntryTimeArray, bridgeEntryLast)", export_block)
        self.assertIn('bridgeEntryTimeSafe = bridgeEntryTf == "" ? na : bridgeEntryTime', export_block)

    def test_no_secret_is_embedded_in_pine(self):
        self.assertNotIn("ALIGN_TV_INGEST_TOKEN", self.source)
        self.assertNotIn("ingest_token", self.source)
        self.assertNotIn("ALIGN_MTF_PRO_A", self.source)


if __name__ == "__main__":
    unittest.main()
