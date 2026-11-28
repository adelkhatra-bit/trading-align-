from pathlib import Path
import hashlib
import unittest

PINE = Path(__file__).parent / "pine" / "ALIGN_MTF_PRO_v25.pine"
BASELINE_GIT_BLOB_SHA = "09b58ccdcdf3264aa4e63473285e9246548b6f19"  # reviewed normalized v25 baseline after exact RSI and entry-direction blocks are restored
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
        self.assertIn(SETTINGS_BLOCK, self.source)
        self.assertIn(EXPORT_MARKER, self.source)
        tp_start = self.source.index("// TP1 touché :")
        tp_end = self.source.index("// Les deux objectifs restent visibles dès qu'un plan existe.", tp_start)
        baseline_tp_state = """// TP1 touché : on garde TP1 affiché et on montre TP2 (remis à zéro seulement si le sens change = position annulée)
var bool tp1Ok = false
var float tp1M = na
var float tp2M = na
if dirPlan != nz(dirPlan[1]) or na(tp1M)
    tp1Ok := false
    tp1M := tp1
    tp2M := tp2
if not tp1Ok and dirPlan != 0 and ((dirPlan == 1 and high >= tp1M) or (dirPlan == -1 and low <= tp1M))
    tp1Ok := true
if not tp1Ok
    tp1M := tp1
    tp2M := tp2
"""
        without_tp_change = self.source[:tp_start] + baseline_tp_state + self.source[tp_end:]
        # Normalize the RSI field introduced in the five-element MTF tuple.
        without_tp_change = without_tp_change.replace(
            "ta.rsi(close, lenRsi), ta.rsi(close, lenRsi)[1], time_close[1]",
            "ta.rsi(close, lenRsi), time_close[1]",
            1,
        )
        for live, closed, bridge_time in (
            ("r1", "r1Fermee", "bridgeTimeM1"), ("r2", "r2Fermee", "bridgeTimeM3"),
            ("r5", "r5Fermee", "bridgeTimeM5"), ("r10", "r10Fermee", "bridgeTimeM10"),
            ("r15", "r15Fermee", "bridgeTimeM15"), ("r30", "r30Fermee", "bridgeTimeM30"),
            ("r45", "r45Fermee", "bridgeTimeM45"), ("r60", "r60Fermee", "bridgeTimeH1"),
            ("r120", "r120Fermee", "bridgeTimeH2"), ("r240", "r240Fermee", "bridgeTimeH4"),
            ("rD", "rDFermee", "bridgeTimeD1"), ("rW", "rWFermee", "bridgeTimeW1"),
        ):
            without_tp_change = without_tp_change.replace(", " + live + ", " + closed + ", " + bridge_time + "]", ", " + live + ", " + bridge_time + "]", 1)
        without_tp_change = without_tp_change.replace("[dC, sC, rC, _, _] = f_etat()", "[dC, sC, rC, _] = f_etat()", 1)
        closed_rsi_start = without_tp_change.index("rsisFermees = array.from(")
        closed_rsi_end = without_tp_change.index('d1Fermee = request.security', closed_rsi_start)
        without_tp_change = without_tp_change[:closed_rsi_start] + without_tp_change[closed_rsi_end:]
        without_tp_change = without_tp_change.replace(
            "[d, sqz ? 1 : 0, ta.rsi(close, lenRsi), time_close[1]]",
            "[d, sqz ? 1 : 0, ta.rsi(close, lenRsi)]",
            1,
        )
        for bridge_time in (
            "bridgeTimeM1", "bridgeTimeM3", "bridgeTimeM5", "bridgeTimeM10",
            "bridgeTimeM15", "bridgeTimeM30", "bridgeTimeM45", "bridgeTimeH1",
            "bridgeTimeH2", "bridgeTimeH4", "bridgeTimeD1", "bridgeTimeW1",
        ):
            without_tp_change = without_tp_change.replace(f", {bridge_time}]", "]", 1)
        without_tp_change = without_tp_change.replace(
            "[dC, sC, rC, _] = f_etat()",
            "[dC, sC, rC] = f_etat()",
            1,
        )
        self.assertIn(RSI_CROSSOVER_BLOCK, self.source)
        without_tp_change = without_tp_change.replace(
            RSI_CROSSOVER_BLOCK,
            RSI_CROSSOVER_BASELINE_BLOCK,
            1,
        )
        # The v25 decision gate now reads closed strategy timeframes. Normalize only
        # these explicitly reviewed additions before checking every other source byte.
        for line in (
            'd1Fermee   = request.security(syminfo.tickerid, "1",   f_dir_confirme(), lookahead=barmerge.lookahead_on)\n',
            'dDFermee   = request.security(syminfo.tickerid, "D",   f_dir_confirme(), lookahead=barmerge.lookahead_on)\n',
            'dWFermee   = request.security(syminfo.tickerid, "W",   f_dir_confirme(), lookahead=barmerge.lookahead_on)\n',
        ):
            without_tp_change = without_tp_change.replace(line, "", 1)
        strategy_start = without_tp_change.find("uW  = nz(dWFermee) == dP")
        strategy_end_marker = "o1h = d1hStrat == -dP"
        strategy_end = without_tp_change.find(strategy_end_marker, strategy_start)
        self.assertGreaterEqual(strategy_start, 0)
        self.assertGreater(strategy_end, strategy_start)
        strategy_end += len(strategy_end_marker)
        baseline_strategy = """uW  = nz(dW) == dP
uD  = nz(dD) == dP
d4Strat = isGold ? nz(d240Fermee) : nz(d240)
d1hStrat = isGold ? nz(d60Fermee) : nz(d60)
d15Strat = isGold ? nz(d15Fermee) : nz(d15)
d5Strat = isGold ? nz(d5Fermee) : nz(d5)
u4  = d4Strat == dP
u1h = d1hStrat == dP
u15 = d15Strat == dP
u5  = d5Strat == dP
u1  = nz(d1) == dP
oW  = nz(dW) == -dP
o4  = d4Strat == -dP
o1h = d1hStrat == -dP"""
        without_tp_change = without_tp_change[:strategy_start] + baseline_strategy + without_tp_change[strategy_end:]
        risk_start = without_tp_change.find("planRisk = math.abs(ent - sl)")
        decision_end = without_tp_change.find("\n", risk_start)
        self.assertGreaterEqual(risk_start, 0)
        self.assertGreater(decision_end, risk_start)
        baseline_decision = 'decisionS = strat == "" ? "AUCUNE ENTRÉE" : scoreV < 60 ? "AUCUNE ENTRÉE : configuration insuffisante" : etatS != "CONFIRMÉ" ? "À SURVEILLER : confirmation manquante" : scoreV >= 85 ? "ENTRÉE POSSIBLE : fortement aligné" : scoreV >= 75 ? "INTÉRESSANT : attendre les conditions finales" : "À SURVEILLER : confirmation manquante"'
        without_tp_change = without_tp_change[:risk_start] + baseline_decision + without_tp_change[decision_end:]
        without_tp_change = without_tp_change.replace(
            "entryReadyUi = entryTriggeredUi and bridgeEntryClose >= zBas and bridgeEntryClose <= zHaut and (dirPlan == 1 ? bridgeEntryClose > (zBas + zHaut) / 2 : dirPlan == -1 ? bridgeEntryClose < (zBas + zHaut) / 2 : false)",
            "entryReadyUi = entryTriggeredUi and close >= zBas and close <= zHaut and (dirPlan == 1 ? close > (zBas + zHaut) / 2 : dirPlan == -1 ? close < (zBas + zHaut) / 2 : false)",
            1,
        )
        without_tp_change = without_tp_change.replace(
            "if (barstate.isconfirmed and (na(ent) or nouvelle15 or slFranchi)) or dirPlan != dirFig or strat != stratFig or planGeometryMismatch",
            "if (barstate.isconfirmed and (na(ent) or nouvelle15 or slFranchi)) or dirPlan != dirFig or strat != stratFig",
            1,
        )
        without_tp_change = without_tp_change.replace(
            "if (barstate.isconfirmed and (na(ent) or nouvelle15 or slFranchi)) or dirPlan != dirFig or strat != stratFig",
            "if barstate.isconfirmed and (na(ent) or nouvelle15 or dirPlan != dirFig or strat != stratFig or slFranchi)",
            1,
        )

        # Normalize the reviewed entry-label wording and its explicit non-executable disclaimer.
        without_tp_change = without_tp_change.replace(
            "// Le prix d'entrée planifié est affiché séparément du déclencheur réellement validé.",
            "// v25 (décision d'Adel) : plus de point d'entrée tracé sur le graphique (ni ligne ni étiquette ENTRÉE)",
            1,
        )
        without_tp_change = without_tp_change.replace(
            "🎯 ENTRÉE PLANIFIÉE — ATTENTE DÉCLENCHEUR",
            "✅ CONFIRMATION",
            1,
        )
        without_tp_change = without_tp_change.replace(
            '"🎯 PRIX D\'ENTRÉE PLANIFIÉ : " + px(ent) + "\\nCe niveau n\'est pas une entrée exécutable. Attendre la clôture du déclencheur M1 / M5 / H1 validé par le bridge." + ',
            '"✅ LIGNE DE CONFIRMATION : " + px(ent) + ',
            1,
        )
        # The pending/confirmed ribbon is the only additional permitted UI change:
        # replace that exact block with the v25 baseline before checking the rest byte-for-byte.
        ui_start = without_tp_change.find("// État de confirmation calculé pour l'affichage ; les champs d'export restent dans le bloc bridge canonique.")
        ui_end = without_tp_change.find("    actif = zoneBas", ui_start)
        self.assertGreaterEqual(ui_start, 0)
        self.assertGreater(ui_end, ui_start)
        titre_start = without_tp_change.find("    titre = ", ui_start)
        titre_end = without_tp_change.find("\n", titre_start)
        self.assertGreaterEqual(titre_start, ui_start)
        self.assertGreater(titre_end, titre_start)
        baseline_titre = without_tp_change[titre_start:titre_end + 1]
        baseline_ui = baseline_titre + """    ligne = (retDir != 0 and not retConf ? "↩ RETOURNEMENT  " : nVoy >= 3 ? "↩ " + str.tostring(nVoy) + "/5  " : "") + (dirPlan == 1 ? "▲ LONG" : dirPlan == -1 ? "▼ SHORT" : "ATTENDRE") + (dirPlan != 0 ? (strat != "" ? " • " + (strat == "SCALPING" ? "SCALP" : strat) + (etatS == "CONFIRMÉ" and scoreV >= 75 ? " ✅ " : " ⏳ ") + str.tostring(scoreV) : "") + "  TP " + px(tp1) + "  SL " + px(sl) : "   " + titre)
    plan = (retTxt != "" ? retTxt + "\n\n" : "") + (dirPlan != 0 ? "STRATÉGIE : " + (strat == "" ? "aucune" : strat + " — " + etatS) + "\nScore : " + str.tostring(scoreV) + " / 100\n• Alignement : " + str.tostring(ptsAlign) + " / 25\n• Structure : " + str.tostring(ptsStruct) + " / 20\n• Zone d'entrée : " + str.tostring(ptsZone) + " / 20\n• Volume : " + str.tostring(ptsVol) + " / 15" + (volOk ? "" : " (indisponible)") + "\n• Indicateurs : " + str.tostring(ptsInd) + " / 10\n• Risque / rendement : " + str.tostring(ptsRR) + " / 10\n⏱ Clôture de validation " + (strat == "SWING" ? "1h" : strat == "DAY" ? "5 min" : strat == "SCALPING" ? "1 min" : "15 min") + " dans " + f_mmss(f_reste((strat == "SWING" ? 60 : strat == "DAY" ? 5 : strat == "SCALPING" ? 1 : 15))) + "\nDécision : " + decisionS + "\nMotif : " + motifS + "\nPlan : " + calePlan + "\n\n" : "") + "SENS PROBABLE : " + (sens == 1 ? "HAUSSE " : sens == -1 ? "BAISSE " : "INDÉCIS ") + str.tostring(pctH) + "% hausse / " + str.tostring(100 - pctH) + "% baisse\n" + str.tostring(bull) + " UT en hausse • " + str.tostring(bear) + " en baisse • " + str.tostring(comp) + " comprimées\nRSI : " + str.tostring(rsiOB) + " UT en surachat (>70) • " + str.tostring(rsiOS) + " en survente (<30)" + (rsiOB >= 3 ? "\nSURCHARGE RSI HAUTE : éviter d'acheter, retournement baissier possible" : rsiOS >= 3 ? "\nSURCHARGE RSI BASSE : éviter de vendre, rebond possible" : "") + (retHaut ? "\nLes petites UT montent avant les grandes : retournement HAUSSIER en préparation" : retBas ? "\nLes petites UT baissent avant les grandes : retournement BAISSIER en préparation" : "") + (zoneBas ? "\nPrix sur une résistance " + tH1 + " : risque de retournement à la baisse" : zoneHaut ? "\nPrix sur un support " + tB1 + " : rebond possible" : "") + (dirPlan != 0 ? "\n\nPLAN " + (dirPlan == 1 ? "ACHAT" : "VENTE") + "\nEntrée " + px(ent) + " (" + tEnt + ")\nTP1 " + px(tp1) + " (" + tTP1 + ")\nTP2 " + px(tp2) + " (" + tTP2 + ")\nStop " + px(sl) + "\nGain/risque ≈ " + str.tostring(rr, "#.#") : "")
    vbg0 = zoneBas or zoneHaut ?  color.rgb(170, 130, 0) : dirPlan == 1 ?  color.rgb(0, 140, 70) : dirPlan == -1 ?  color.rgb(190, 30, 45) :  color.rgb(60, 60, 60)
"""
        without_tp_change = without_tp_change[:ui_start] + baseline_ui + without_tp_change[ui_end:]
        for marker, terminator in (
            ("planGeometryMismatch = dirPlan != 0 and (", "\n)"),
            ("bridgePlanGeometryOk = dirPlan == 1 ? (", ": false"),
        ):
            start = without_tp_change.find(marker)
            if start != -1:
                end = without_tp_change.find(terminator, start)
                self.assertNotEqual(end, -1, marker)
                end += len(terminator)
                if without_tp_change[end:end + 1] == "\n":
                    end += 1
                without_tp_change = without_tp_change[:start] + without_tp_change[end:]
        without_settings = without_tp_change.replace(SETTINGS_BLOCK, "", 1)
        without_export = without_settings.split(EXPORT_MARKER, 1)[0]
        if without_export.endswith("\n\n"):
            without_export = without_export[:-1]
        # Normalize the targeted reversal-direction guard and live entry-zone gate.
        direction_start = without_export.find("// Plan automatique : les grosses UT (2h, 4h, Daily) décident, sauf zone de retournement")
        direction_end = without_export.find("// GOLD : aucune direction de trade", direction_start)
        self.assertGreaterEqual(direction_start, 0)
        self.assertGreater(direction_end, direction_start)
        baseline_direction = """// Plan automatique : les grosses UT (2h, 4h, Daily) décident, sauf zone de retournement
dirBrut = zoneHaut ? 1 : zoneBas ? -1 : longT >= 2 ? 1 : longT <= -2 ? -1 : retHaut ? 1 : retBas ? -1 : sens
// Anti-parasites (vue 1 / 3 / 5 min) : le sens ne change qu'à la CLÔTURE d'une bougie,
// et seulement si le 15 min ou l'1h confirme le nouveau sens. Pas de LONG / SHORT qui clignote en cours de bougie.
var int dirStable = 0
if barstate.isconfirmed
    if dirStable == 0
        dirStable := dirBrut
    else if dirBrut != 0 and dirBrut != dirStable and (nz(d15Fermee) == dirBrut or nz(d60Fermee) == dirBrut)
        dirStable := dirBrut
    else if dirBrut == 0 and nz(d15Fermee) != dirStable and nz(d60Fermee) != dirStable
        dirStable := 0
"""
        without_export = without_export[:direction_start] + baseline_direction + without_export[direction_end:]
        without_export = without_export.replace(
            "entryReadyUi = entryTriggeredUi and close >= zBas and close <= zHaut and (dirPlan == 1 ? close > (zBas + zHaut) / 2 : dirPlan == -1 ? close < (zBas + zHaut) / 2 : false)",
            "entryReadyUi = entryTriggeredUi and close >= zBas and close <= zHaut",
            1,
        )
        # Normalize only the approved MTF table presentation changes; the dedicated
        # visual contract test asserts the new 1W column and closed-RSI semantics.
        without_export = without_export.replace(
            "var table t = table.new(pos, 12, 3",
            "var table t = table.new(pos, 11, 3",
            1,
        )
        without_export = without_export.replace(
            "rv = array.get(rsisFermees, i)",
            "rv = array.get(rsis, i)",
            1,
        )
        without_export = without_export.replace(
            "        // RSI affiché = dernière valeur clôturée, comme la direction utilisée pour la décision.\\n",
            "",
            1,
        )
        without_export = without_export.replace("RSI clôturé :", "RSI :", 1)
        without_export = without_export.replace("Compression en formation :", "Compression :", 1)
        without_export = without_export.replace(
            "OUI ⚡ (information provisoire)",
            "OUI ⚡ prêt à exploser (attendre la direction)",
            1,
        )
        weekly_start = without_export.find("    // Weekly : contexte clôturé affiché séparément")
        weekly_end = without_export.find("    titre = ", weekly_start)
        self.assertGreaterEqual(weekly_start, 0)
        self.assertGreater(weekly_end, weekly_start)
        without_export = without_export[:weekly_start] + without_export[weekly_end:]
        without_export = without_export.replace(
            "table.merge_cells(t, 0, 2, 11, 2)",
            "table.merge_cells(t, 0, 2, 10, 2)",
            1,
        )
        raw = without_export.encode("utf-8")
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        self.assertEqual(git_blob, BASELINE_GIT_BLOB_SHA)

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
            'strat == "SCALPING" ? (nz(d60Fermee) != -dirPlan and nz(d15Fermee) == dirPlan and nz(d5Fermee) == dirPlan and nz(d1Fermee) == dirPlan)',
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
        self.assertIn(
            "if (barstate.isconfirmed and (na(ent) or nouvelle15 or slFranchi)) or dirPlan != dirFig or strat != stratFig",
            self.source,
        )
        self.assertIn(
            'bridgePlanValid = dirPlan != 0 and strat != "" and dirPlan == dirFig and strat == stratFig and bridgePlanGeometryOk and not na(ent) and not na(sl) and not na(tp1) and not na(tp2)',
            self.source,
        )
        self.assertIn("dirFig := dirPlan", self.source)
        self.assertIn("stratFig := strat", self.source)

    def test_gold_plan_geometry_is_recomputed_and_invalid_direction_is_suppressed(self):
        self.assertIn("planGeometryMismatch = dirPlan != 0 and (", self.source)
        self.assertIn("or planGeometryMismatch", self.source)
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

    def test_no_secret_is_embedded_in_pine(self):
        self.assertNotIn("ALIGN_TV_INGEST_TOKEN", self.source)
        self.assertNotIn("ingest_token", self.source)
        self.assertNotIn("ALIGN_MTF_PRO_A", self.source)


if __name__ == "__main__":
    unittest.main()
