"""Regression contract: the public entry path must use Pine v25 plan levels."""
from pathlib import Path
import unittest

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

    def test_bot_accepts_canonical_plan_only_from_m15_active_snapshot(self):
        start = self.bot.index("def plan_indicateur(r):")
        end = self.bot.index("\nTTL_KRAKEN", start)
        plan = self.bot[start:end]
        self.assertIn('if active_tf != "M15":', plan)
        self.assertIn("source du plan canonique attendue depuis le graphique M15", plan)

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

    def test_live_sniper_notification_requires_confirmed_pine_levels(self):
        start = self.bot.index("def evenements_pine(etat, m, r, cle, now):")
        end = self.bot.index("\ndef texte_pine(", start)
        events = self.bot[start:end]
        self.assertIn("plan_tv = plan_indicateur(r)", events)
        self.assertIn('plan_tv.get("available") is True', events)
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

    def test_market_scope_remains_btc_and_gold_only_in_indicator(self):
        self.assertIn('options=["BTCUSD", "XAUUSD"]', self.pine)
        self.assertNotIn("NAS100", self.pine)


if __name__ == "__main__":
    unittest.main()
