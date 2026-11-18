from pathlib import Path
import unittest

PINE = Path(__file__).parent / "pine" / "ALIGN_MTF_PRO_INSIDE_FVG_EVOLUTIVE.pine"


class PineBridgeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PINE.read_text(encoding="utf-8")

    def test_original_indicator_identity_and_visual_settings_are_preserved(self):
        self.assertIn('indicator("ALIGN MTF PRO (Inside)", shorttitle="ALIGN MTF"', self.source)
        self.assertIn('animer   = input.bool(true, "Animation en temps réel"', self.source)
        self.assertIn("clignote = animer and tick % 2 == 0", self.source)
        self.assertIn('voirPlan = input.bool(true, "Afficher le plan (TP / SL)"', self.source)

    def test_progressive_fvg_consumption_and_recoloring_are_preserved(self):
        self.assertIn("if sv == 1 and low < box.get_top(b)", self.source)
        self.assertIn("box.set_top(b, low)", self.source)
        self.assertIn("if sv == -1 and high > box.get_bottom(b)", self.source)
        self.assertIn("box.set_bottom(b, high)", self.source)
        self.assertIn("prox84 ? 55 : 85", self.source)
        self.assertIn('prox84 ? "FVG 👀" : "FVG"', self.source)

    def test_existing_human_alerts_remain_and_bridge_is_opt_in(self):
        self.assertIn('alert(syminfo.ticker + " " + nomSigH', self.source)
        self.assertIn('alert(syminfo.ticker + " " + nomSigB', self.source)
        self.assertIn('bridgeEnabled = input.bool(false,', self.source)
        self.assertIn('alert(bridgePayload, alert.freq_all)', self.source)
        self.assertIn("\"scalp_inverse\":", self.source)
        self.assertIn("\"strategy\":\"", self.source)

    def test_bridge_exports_active_plan_and_required_mtf_frames(self):
        for key in ('"entry"', '"sl"', '"tp1"', '"tp2"', '"lecture_1m"', '"lecture_5m"', '"lecture_15m"', '"lecture_60m"'):
            self.assertIn(key, self.source)
        for tf in ('M5', 'M15', 'H1', 'H4', 'D1', 'W1'):
            self.assertIn('"' + tf + '"', self.source)
        self.assertIn('"source":"ALIGN_MTF_PRO_A"', self.source)
        self.assertIn('>= 20000', self.source)

    def test_no_ingest_secret_is_embedded_in_source(self):
        self.assertNotIn("ALIGN_TV_INGEST_TOKEN", self.source)
        self.assertNotIn("ingest_token", self.source)


if __name__ == "__main__":
    unittest.main()
