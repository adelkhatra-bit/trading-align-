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
        self.assertIn('"price_in_zone": zone_low <= current_price <= zone_high', plan)

    def test_agent_blocks_entry_when_tradingview_price_left_pine_zone(self):
        start = self.bot.index("def agent(m, r, cle, ferme):")
        end = self.bot.index("\n\ndef ", start + 1)
        agent = self.bot[start:end]
        self.assertIn('if not plan_tv.get("price_in_zone"):', agent)
        self.assertIn("Aucune entrée au marché ; attendre le retour dans la zone.", agent)
        self.assertLess(agent.index('if not plan_tv.get("price_in_zone")'), agent.index('cle["pine_entry_bar_done"]'))

    def test_agent_requires_local_strategy_to_match_pine_strategy(self):
        start = self.bot.index("def agent(m, r, cle, ferme):")
        end = self.bot.index("\n\ndef ", start + 1)
        agent = self.bot[start:end]
        self.assertIn('strategie_locale = (strategie_trade(r, d) or {}).get("strat")', agent)
        self.assertIn('if strategie_locale != plan_tv["strategy"]:', agent)

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
