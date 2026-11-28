from pathlib import Path
import hashlib
import re
import unittest

PINE = Path(__file__).parent / "pine" / "ALIGN_MTF_PRO_v24.pine"
BASELINE_GIT_BLOB_SHA = "392d83b32f2d5c244283b6eb95e33b106cb499a9"  # reviewed v24 context-only MTF reversal baseline

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


class VisualOnlyPineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PINE.read_text(encoding="utf-8")

    def test_indicator_identity_and_candle_close_visuals_are_preserved(self):
        self.assertIn('indicator("ALIGN MTF PRO (Inside)", shorttitle="ALIGN MTF"', self.source)
        self.assertIn("Clôture dans :", self.source)
        self.assertIn("Clôture de validation ", self.source)
        self.assertIn("f_reste(minUT)", self.source)
        self.assertIn("table.cell(t, i, 0", self.source)
        self.assertIn("VISUEL UNIQUEMENT", self.source)

    def test_rsi_crossovers_are_evaluated_unconditionally(self):
        self.assertIn(RSI_CROSSOVER_BLOCK, self.source)
        self.assertNotIn("rsiAchat = (ta.crossover(", self.source)
        self.assertNotIn("rsiVente = (ta.crossunder(", self.source)

    def test_visual_companion_has_no_outbound_alerts_or_bridge(self):
        self.assertIsNone(re.search(r"\balert(?:condition)?\s*\(", self.source))
        self.assertNotIn("bridgePayload", self.source)
        self.assertNotIn("bridgeEnabled", self.source)
        self.assertNotIn("ALIGN_MTF_PRO_V25", self.source)

    def test_all_other_v24_source_bytes_match_the_verified_baseline(self):
        normalized = self.source.replace(RSI_CROSSOVER_BLOCK, RSI_CROSSOVER_BASELINE_BLOCK, 1)
        normalized = normalized.replace(VISUAL_ONLY_MARKER, BASELINE_ALERT_BLOCK, 1)
        normalized = normalized.replace("// v24 est strictement contextuel : aucun Entry / SL / TP indépendant ne peut être affiché.\nvoirPlan = false", 'voirPlan = input.bool(false, "Afficher le plan (TP / SL)", group=grpA)', 1)
        normalized = normalized.replace('voirFibo = false', 'voirFibo = input.bool(false, "Zone d\'entrée + Fibonacci", group=grpA)', 1)
        normalized = normalized.replace("// Les signaux directionnels exécutables appartiennent exclusivement au v25.\nvoirSignauxV24 = false", 'voirSignauxV24 = input.bool(false, "Signaux indépendants v24 (désactivés par défaut)", group=grpA)', 1)
        normalized = normalized.replace('titre = zoneBas ? "PRESSION À LA RÉSISTANCE (CONTEXTE)" : zoneHaut ? "PRESSION AU SUPPORT (CONTEXTE)" : rsiOB >= 3 ? "RSI SURACHAT — CONTEXTE" : rsiOS >= 3 ? "RSI SURVENTE — CONTEXTE" : surcharge ? "COMPRESSION — SURVEILLANCE" : sens == 1 ? "BIAIS HAUSSIER — CONTEXTE" : sens == -1 ? "BIAIS BAISSIER — CONTEXTE" : "CONTEXTE MIXTE"', 'titre = zoneBas ? "RETOURNEMENT ▼" : zoneHaut ? "REBOND ▲" : fortHaut ? "★ ACHAT FORT" : fortBas ? "★ VENTE FORTE" : retHaut ? "RETOURNEMENT ▲" : retBas ? "RETOURNEMENT ▼" : rsiOB >= 3 ? "RSI SURACHAT " + str.tostring(rsiOB) + "/11" : rsiOS >= 3 ? "RSI SURVENTE " + str.tostring(rsiOS) + "/11" : surcharge ? "⚡ SURCHARGE" : sens == 1 ? "HAUSSE" : sens == -1 ? "BAISSE" : "ATTENDRE"', 1)
        raw = normalized.encode("utf-8")
        git_blob = hashlib.sha1(
            b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
        ).hexdigest()
        self.assertEqual(git_blob, BASELINE_GIT_BLOB_SHA)


if __name__ == "__main__":
    unittest.main()
