"""Regression contract: the public entry path must use Pine v25 plan levels."""
from pathlib import Path
import unittest

import align_bot as ab

BOT = Path(__file__).resolve().parent / "align_bot.py"
BRIDGE = Path(__file__).resolve().parent / "align_tv_bridge.py"
PINE = Path(__file__).resolve().parent / "pine" / "ALIGN_MTF_PRO_v25.pine"


class PineCanonicalEntryContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = BOT.read_text(encoding="utf-8")
        cls.bridge = BRIDGE.read_text(encoding="utf-8")
        cls.pine = PINE.read_text(encoding="utf-8")

    def test_main_agent_entry_path_uses_canonical_tv_plan(self):
        start = self.bot.index("def agent(m, r, cle, ferme):")
        end = self.bot.index("\n\ndef ", start + 1)
        agent = self.bot[start:end]
        self.assertIn("plan_indicateur(r)", agent)
        self.assertIn('entry = float(plan_tv["entry"])', agent)
        self.assertIn('stop = float(plan_tv["sl"])', agent)
        self.assertIn('tp1 = float(plan_tv["tp1"])', agent)
        self.assertIn('tp2 = plan_tv.get("tp2")', agent)
        self.assertIn('plan_tv["zone_low"]', agent)
        self.assertIn('plan_tv["zone_high"]', agent)
        self.assertNotIn("plan_pine(", agent)

    def test_bridge_derived_trigger_requires_closed_candle_zone_and_decision(self):
        self.assertIn("entry_triggered", self.bridge)
        self.assertIn('"entryTriggered": entry_triggered', self.bridge)
        self.assertIn("entry_bar_close", self.bridge)
        self.assertIn("entry_zone_low", self.bridge)
        self.assertIn("entry_zone_high", self.bridge)
        self.assertIn("entry_decision", self.bridge)

    def test_bot_trigger_gate_requires_bridge_trigger_and_confirmation(self):
        start = self.bot.index("def plan_indicateur(r):")
        end = self.bot.index("\nTTL_KRAKEN", start)
        plan = self.bot[start:end]
        self.assertIn('snap.get("confirmed") is True', plan)
        self.assertIn('robot.get("confirmed") is True', plan)
        self.assertIn('robot.get("entryTriggered") is True', plan)
        self.assertIn("retested_zone", plan)
        self.assertIn("candle_trigger", plan)
        self.assertIn("candle_before_stop", plan)

    def test_plan_pine_exports_same_source_current_price_and_zone_state(self):
        start = self.bot.index("def plan_indicateur(r):")
        end = self.bot.index("\nTTL_KRAKEN", start)
        plan = self.bot[start:end]
        self.assertIn('current_price = float(snap.get("price"))', plan)
        self.assertIn('"price": current_price', plan)
        self.assertIn('"price_in_zone": prix_tradingview_dans_zone(current_price, zone_low, zone_high)', plan)

    def test_agent_does_not_publish_direction_or_levels_before_pine_mtf_confirmation(self):
        start = self.bot.index("def agent(m, r, cle, ferme):")
        end = self.bot.index("\n\ndef ", start + 1)
        agent = self.bot[start:end]
        gate = agent.index('if not plan_tv.get("confirmed"):')
        self.assertIn("Aucun sens de trade ni niveau Entry/SL/TP publié.", agent)
        self.assertLess(gate, agent.index('entry = float(plan_tv["entry"])'))
        self.assertLess(gate, agent.index('if not plan_tv.get("triggered"):'))

    def test_pine_bridge_zone_labels_match_actual_support_and_resistance(self):
        self.assertIn('bridgeZone = zoneHaut ? "SUPPORT" : zoneBas ? "RESISTANCE" : "PLAN"', self.pine)

    def test_agent_blocks_entry_when_tradingview_price_left_pine_zone(self):
        start = self.bot.index("def agent(m, r, cle, ferme):")
        end = self.bot.index("\n\ndef ", start + 1)
        agent = self.bot[start:end]
        self.assertIn('if not plan_tv.get("price_in_zone"):', agent)
        self.assertIn("Aucune entrée au marché ; attendre le retour dans la zone.", agent)
        self.assertLess(agent.index('if not plan_tv.get("price_in_zone")'), agent.index('cle["pine_entry_bar_done"]'))

    def test_trade_strategy_and_execution_timeframe_follow_pine_with_local_filter_kept(self):
        self.assertIn('tr["strat_filtre"] = tr.get("strat")', self.bot)
        self.assertIn('tr["strat"] = plan_tv["strategy"]', self.bot)

    def test_pine_v25_coach_never_recomputes_legacy_v24_zone(self):
        start = self.bot.index("def coach_fvg(")
        end = self.bot.index("\ndef pine_entree(", start)
        coach = self.bot[start:end]
        self.assertLess(coach.index('startswith("Pine v25")'), coach.index("pe = pine_entree(r, d)"))
        self.assertIn('tv_price = float(tr["tv_price"])', coach)
        self.assertIn('float(tr["za"]), float(tr["zb"])', coach)

    def test_prix_tradingview_dans_zone_uses_closed_zone_boundaries_and_rejects_invalid_data(self):
        self.assertTrue(ab.prix_tradingview_dans_zone(100, 99, 101))
        self.assertTrue(ab.prix_tradingview_dans_zone(99, 99, 101))
        self.assertTrue(ab.prix_tradingview_dans_zone(101, 99, 101))
        self.assertFalse(ab.prix_tradingview_dans_zone(101.01, 99, 101))
        self.assertFalse(ab.prix_tradingview_dans_zone(98.99, 99, 101))
        self.assertFalse(ab.prix_tradingview_dans_zone(None, 99, 101))
        self.assertFalse(ab.prix_tradingview_dans_zone(float("nan"), 99, 101))

    def test_pine_v25_coach_reads_only_the_trade_snapshot_zone_and_price(self):
        lines = ab.coach_fvg(
            {}, 1, 999, attente=False,
            tr={
                "src": "Pine v25 M15 / M5", "za": 99, "zb": 101,
                "tv_price": 100, "entry_timeframe": "M5",
                "strategie": "DAY", "strat_filtre": "SWING",
            },
        )
        self.assertEqual(len(lines), 2)
        self.assertIn("99", lines[0])
        self.assertIn("101", lines[0])
        self.assertIn("Pine DAY (M5)", lines[1])
        self.assertIn("filtre local SWING", lines[1])

    def test_live_sniper_notification_requires_confirmed_pine_levels(self):
        start = self.bot.index("def evenements_pine(etat, m, r, cle, now):")
        end = self.bot.index("\ndef texte_pine(", start)
        events = self.bot[start:end]
        self.assertIn("plan_tv = plan_indicateur(r)", events)
        self.assertIn('plan_tv.get("available") is True', events)
        self.assertIn('plan_tv.get("confirmed") is True', events)
        self.assertIn('plan_tv.get("triggered") is True', events)
        self.assertIn("pine_direction == sn_direction", events)
        self.assertIn("entree=px(pine_entry)", events)
        self.assertIn("sl=px(pine_sl)", events)
        self.assertIn("tp1=px(pine_tp1)", events)
        self.assertNotIn('kind="scalp_inv"', events)

    def test_pine_payload_exports_levels_and_strategy_timeframe(self):
        marker = "// ═════════ BRIDGE ALIGN — export structuré du Pine v25"
        self.assertIn(marker, self.pine)
        payload = self.pine.split(marker, 1)[1]
        for key in ('"entry":', '"sl":', '"tp1":', '"tp2":', '"strategy":', '"entryTimeframe":'):
            self.assertIn(key, payload)
        self.assertIn('"planTimeframe":"M15"', payload)

    def test_bridge_never_exports_executable_plan_without_selected_strategy(self):
        marker = "bridgePlanValid ="
        line = next(line for line in self.pine.splitlines() if line.startswith(marker))
        self.assertIn('strat != ""', line)
        self.assertIn('bridgeEntryTf = strat == "SWING"', self.pine)
        self.assertIn('"UNSUPPORTED")', self.pine)
        self.assertIn('bridgeSignal = bridgeConfirmed ?', self.pine)
        self.assertIn('statutPlan = planConfirmedUi ?', self.pine)
        self.assertIn('AUCUNE ENTRÉE : attendre la confirmation MTF', self.pine)
        self.assertIn('planConfirmedUi ? "\\n\\nPLAN CONFIRMÉ "', self.pine)


    def test_pine_does_not_show_long_or_entry_levels_as_executable_before_mtf_confirmation(self):
        self.assertIn('bridgeSignal = bridgeConfirmed ?', self.pine)
        self.assertIn('"⏳ BIAIS LONG — EN ATTENTE"', self.pine)
        self.assertIn('"⏳ BIAIS SHORT — EN ATTENTE"', self.pine)
        self.assertIn('"ATTENDRE • AUCUNE STRATÉGIE"', self.pine)
        self.assertIn('planConfirmedUi ? "\\n\\nPLAN CONFIRMÉ "', self.pine)
        self.assertNotIn('dirPlan != 0 ? "\\n\\nPLAN "', self.pine)
        self.assertIn("vbg0 = zoneBas or zoneHaut ? color.rgb(170, 130, 0) : planConfirmedUi and dirPlan == 1", self.pine)

    def test_decision_line_illuminates_only_on_the_same_fresh_closed_trigger_as_bridge(self):
        self.assertIn("bridgeEntryFreshUi", self.pine)
        self.assertIn("bridgeEntryAgeMs <= 2 * bridgeEntryTfMs + 30000", self.pine)
        self.assertIn("bridgeEntryOhlcValidUi", self.pine)
        self.assertIn("bridgeEntryRetestedUi = bridgeEntryHigh >= zBas and bridgeEntryLow <= zHaut", self.pine)
        self.assertIn("bridgeEntryDecisionUi", self.pine)
        self.assertIn("bridgeEntryBeforeStopUi", self.pine)
        self.assertIn("entryTriggeredUi = bridgeConfirmed and bridgeEntryFreshUi", self.pine)
        self.assertIn("line.set_color(lZH, dirPlan == 1 ? color.lime : color.red)", self.pine)
        self.assertIn("🟢 ENTRÉE LONG VALIDÉE", self.pine)
        self.assertIn("🔴 ENTRÉE SHORT VALIDÉE", self.pine)

    def test_market_scope_remains_btc_and_gold_only_in_indicator(self):
        self.assertIn('bridgeMarket = isBtc ? "BTCUSD" : isGold ? "XAUUSD" : "UNSUPPORTED"', self.pine)
        self.assertNotIn('input.string("BTCUSD", "Marché ALIGN"', self.pine)
        self.assertNotIn("NAS100", self.pine)


if __name__ == "__main__":
    unittest.main()
