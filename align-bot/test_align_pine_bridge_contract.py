from pathlib import Path
import hashlib
import unittest

PINE = Path(__file__).parent / "pine" / "ALIGN_MTF_PRO_v25.pine"
BASELINE_GIT_BLOB_SHA = "823635f039ff3b59c39867a7b59dfa3ed6fafaf1"
SETTINGS_BLOCK = """// ═════════ BRIDGE ALIGN (optionnel, sans modification visuelle) ═════════
grpBridge = "Bridge ALIGN (optionnel)"
bridgeEnabled = input.bool(false, "Envoyer les snapshots au ROBOT V12", group=grpBridge)
bridgeMarket = input.string("BTCUSD", "Marché ALIGN", options=["BTCUSD", "XAUUSD", "NAS100"], group=grpBridge)

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

    def test_existing_human_alerts_are_preserved_and_bridge_is_opt_in(self):
        self.assertIn('alert(syminfo.ticker + " " + nomSigH', self.source)
        self.assertIn('alert(syminfo.ticker + " " + nomSigB', self.source)
        self.assertIn('bridgeEnabled = input.bool(false, "Envoyer les snapshots au ROBOT V12"', self.source)
        self.assertIn('alert(bridgePayload, alert.freq_all)', self.source)
        self.assertIn('"source":"ALIGN_MTF_PRO_V25"', self.source)

    def test_active_plan_and_all_required_mtf_timeframes_are_exported(self):
        for key in ('"entry"', '"sl"', '"tp1"', '"tp2"', '"lecture_1m"', '"lecture_5m"', '"lecture_15m"', '"lecture_60m"'):
            self.assertIn(key, self.source)
        for tf in ("M1", "M5", "M15", "M30", "H1", "H2", "H4", "D1", "W1"):
            self.assertIn('"' + tf + '"', self.source)
        self.assertIn(">= 20000", self.source)
        self.assertLessEqual(self.source.count("request.security("), 40)
        export_block = self.source.split(EXPORT_MARKER, 1)[1]
        for missing_value_fallback in ("f_align_v25_json_num(nz(r1, 50))", "f_align_v25_json_num(nz(r5, 50))", "f_align_v25_json_num(nz(r15, 50))", "f_align_v25_json_num(nz(r60, 50))", "str.tostring(nz(d1))"):
            self.assertNotIn(missing_value_fallback, export_block)
        self.assertIn('na(v) ? "null" : str.tostring(v)', export_block)
        self.assertIn('na(v) ? "null" : v == 1', export_block)

    def test_robot_v12_exports_closed_mtf_directions_for_entry_confirmation(self):
        self.assertIn(
            "bridgeClosedMtfOk = isGoldNasdaq ? (nz(d5Fermee) == dirPlan and nz(d15Fermee) == dirPlan and nz(d60Fermee) == dirPlan and nz(d240Fermee) == dirPlan) : (nz(d60Fermee) == dirPlan)",
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

    def test_no_secret_is_embedded_in_pine(self):
        self.assertNotIn("ALIGN_TV_INGEST_TOKEN", self.source)
        self.assertNotIn("ingest_token", self.source)
        self.assertNotIn("ALIGN_MTF_PRO_A", self.source)


if __name__ == "__main__":
    unittest.main()
