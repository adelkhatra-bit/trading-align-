from pathlib import Path
import re
import unittest


PINE = Path(__file__).resolve().parent / "pine" / "ALIGN_MTF_PRO_v25.pine"
PINE_V24 = Path(__file__).resolve().parent / "pine" / "ALIGN_MTF_PRO_v24.pine"
TIMEFRAMES = ("M1", "M3", "M5", "M10", "M15", "M30", "M45", "H1", "H2", "H4", "D1", "W1")


class PineTpPlanStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PINE.read_text(encoding="utf-8")
        cls.source_v24 = PINE_V24.read_text(encoding="utf-8")

    def test_tp_touch_state_is_bound_to_current_plan_levels(self):
        start = self.source.index("// TP1 touché :")
        end = self.source.index("// ═════════ LIGNES BLANCHES D'EXPLICATION", start)
        block = self.source[start:end]
        self.assertIn("(not na(tp1) and tp1 != tp1M)", block)
        self.assertIn("(not na(tp2) and tp2 != tp2M)", block)
        self.assertIn("(na(tp1) != na(tp1M))", block)
        self.assertIn("(na(tp2) != na(tp2M))", block)
        self.assertLess(block.index("if planTpChange"), block.index("if not tp1Ok and dirPlan"))

    def test_v24_is_a_context_only_companion_and_does_not_publish_a_second_plan_by_default(self):
        self.assertIn('voirPlan = input.bool(false, "Afficher le plan (TP / SL)"', self.source_v24)
        self.assertIn('voirFibo = input.bool(false, "Zone d\'entrée + Fibonacci"', self.source_v24)
        self.assertIn('voirSignauxV24 = input.bool(false, "Signaux indépendants v24 (désactivés par défaut)"', self.source_v24)
        self.assertIn("sigHaut = voirSignauxV24 and sigHaut0", self.source_v24)
        self.assertIn("sigBas  = voirSignauxV24 and sigBas0", self.source_v24)
        self.assertIn("CONTEXTE MTF v24 — plan Entry / SL / TP sur v25", self.source_v24)
        self.assertIn("dirsFermees = array.from(nz(d1Fermee), nz(d3Fermee)", self.source_v24)
        self.assertIn("dv = array.get(dirsFermees, i)", self.source_v24)
        self.assertIn("Bougie en formation :", self.source_v24)
        self.assertIn("visuel MTF d'accompagnement", self.source_v24)
        self.assertLessEqual(self.source_v24.count("request.security("), 40)
        self.assertNotIn('E " + px(ent) + "  TP " + px(tp1) + "  SL " + px(sl)', self.source_v24)

    def test_entry_sl_tp_visuals_are_hidden_until_the_plan_is_confirmed(self):
        self.assertIn("planConfirmedUi = dirPlan != 0 and strat != \"\" and dirPlan == dirFig", self.source)
        self.assertIn("if voirPlan and planConfirmedUi", self.source)
        self.assertNotIn("if voirPlan and dirPlan != 0", self.source)
        self.assertIn("voirTP2 and tp1Ok and voirPlan and planConfirmedUi", self.source)

    def test_visual_confirmation_line_and_label_are_preserved_without_entry_marker(self):
        self.assertIn("lConf := line.new(bar_index, ent, bar_index + 30, ent", self.source)
        self.assertIn('eConf := label.new(bar_index + 30, ent, "✅ CONFIRMATION"', self.source)
        self.assertIn("line.delete(lConf)", self.source)
        self.assertIn("label.delete(eConf)", self.source)
        self.assertNotIn('eE := label.new(x1, ent, "ENTRÉE "', self.source)
        self.assertNotIn("lE := line.new(x1, ent", self.source)
        self.assertIn("var table t = table.new(pos, 12, 3", self.source)
        self.assertIn("lZH := line.new(x1, zMil", self.source)

    def test_targets_and_stop_visual_contract_is_preserved(self):
        self.assertIn('eTP1 := label.new(x1, tp1, "TP1 " + px(tp1)', self.source)
        self.assertIn('eTP2 := label.new(x1, tp2, "TP2 " + px(tp2)', self.source)
        self.assertIn('eSL  := label.new(x1, sl, "STOP " + px(sl)', self.source)
        self.assertIn('voirTP2  = input.bool(false, "TP1 touché : garder TP1 + afficher TP2", group=grpX)', self.source)
        self.assertIn('label.set_text(eTP1, "✅ TP1 TOUCHÉ " + px(tp1M)', self.source)
        self.assertIn('label.set_text(eTP2, "🎯 TP2 VISÉ " + px(tp2M)', self.source)

    def test_bridge_exports_all_twelve_timeframes_and_strategy_trigger_map(self):
        self.assertIn("bridgePayload =", self.source)
        for tf in TIMEFRAMES:
            self.assertRegex(self.source, rf'"{tf}"\s*:\{{')
        self.assertIn('strat == "SWING" ? "H1"', self.source)
        self.assertIn('strat == "DAY" ? "M5"', self.source)
        self.assertIn('strat == "SCALPING" ? "M1"', self.source)

    def test_all_eleven_displayed_and_bridged_directions_use_the_last_closed_candle(self):
        for name in ("d1Fermee", "d3Fermee", "d5Fermee", "d10Fermee", "d15Fermee",
                     "d30Fermee", "d45Fermee", "d60Fermee", "d120Fermee", "d240Fermee", "dDFermee"):
            self.assertIn(name, self.source)
        self.assertIn('d3Fermee = request.security(syminfo.tickerid, "3", f_dir_confirme(), lookahead=barmerge.lookahead_on)', self.source)
        self.assertIn("dirsFermees = array.from(nz(d1Fermee), nz(d3Fermee), nz(d5Fermee)", self.source)
        self.assertIn("dvLive = array.get(dirs, i)", self.source)
        self.assertIn("dv = array.get(dirsFermees, i)", self.source)
        self.assertIn("Bougie en formation :", self.source)
        for name in ("d1Fermee", "d3Fermee", "d5Fermee", "d10Fermee", "d15Fermee",
                     "d30Fermee", "d45Fermee", "d60Fermee", "d120Fermee", "d240Fermee", "dDFermee", "dWFermee"):
            self.assertIn(f"f_align_v25_json_int(nz({name}))", self.source)
        self.assertIn("f_align_v25_json_dir(nz(d1Fermee))", self.source)
        self.assertIn("str.tostring(bullFermee)", self.source)
        self.assertIn("str.tostring(bearFermee)", self.source)
        self.assertIn("d5Strat = nz(d5Fermee)", self.source)
        self.assertIn("d1Strat = nz(d1Fermee)", self.source)
        self.assertIn("uD  = nz(dDFermee) == dP", self.source)
        self.assertIn("uW  = nz(dWFermee) == dP", self.source)
        self.assertIn('strat == "SWING" ? (nz(dDFermee) == dirPlan', self.source)
        self.assertIn('strat == "DAY" ? (nz(d60Fermee) == dirPlan and nz(d5Fermee) == dirPlan', self.source)
        self.assertIn('strat == "SCALPING" ? (nz(d60Fermee) != -dirPlan and nz(d15Fermee) == dirPlan and nz(d5Fermee) == dirPlan and nz(d1Fermee) == dirPlan)', self.source)

    def test_visual_and_bridge_share_the_coach_risk_reward_and_atr_gate(self):
        self.assertIn("planRiskRewardOk = not na(atr15) and atr15 > 0 and rrS >= 2.0 and planRisk <= 1.5 * atr15", self.source)
        self.assertIn("and bridgePlanGeometryOk and planRiskRewardOk and not na(ent)", self.source)
        self.assertIn("bridgeConfirmed = bridgePlanValid and planRiskRewardOk", self.source)
        self.assertIn("AUCUNE ENTRÉE : risque ou gain/risque insuffisant", self.source)
        self.assertIn("PLAN VALIDÉ : attendre le déclencheur", self.source)

    def test_risk_reward_ratio_is_declared_before_plan_confirmation_gate(self):
        rr_s = self.source.index("rrS =")
        risk_gate = self.source.index("planRiskRewardOk =")
        rr_later = self.source.index("rr  =")
        self.assertLess(rr_s, risk_gate)
        self.assertLess(risk_gate, rr_later)
        risk_line = next(line for line in self.source.splitlines() if line.startswith("planRiskRewardOk ="))
        self.assertIn("rrS >= 2.0", risk_line)

    def test_visual_plan_status_does_not_claim_entry_is_already_executable(self):
        self.assertIn("PLAN LONG VALIDÉ — ATTENTE ENTRÉE", self.source)
        self.assertIn("PLAN SHORT VALIDÉ — ATTENTE ENTRÉE", self.source)
        self.assertNotIn("▲ LONG CONFIRMÉ", self.source)
        self.assertNotIn("▼ SHORT CONFIRMÉ", self.source)

    def test_entry_sl_tp_geometry_is_guarded_before_bridge_publication(self):
        self.assertIn("bridgePlanValid =", self.source)
        self.assertRegex(self.source, r"bridgePlanValid\s*=\s*dirPlan != 0")
        self.assertIn('f_align_v25_json_num(bridgePlanValid ? ent : na)', self.source)
        self.assertIn('f_align_v25_json_num(bridgePlanValid ? sl : na)', self.source)
        self.assertIn('f_align_v25_json_num(bridgePlanValid ? tp1 : na)', self.source)
        self.assertIn('f_align_v25_json_num(bridgePlanValid ? tp2 : na)', self.source)


if __name__ == "__main__":
    unittest.main()
