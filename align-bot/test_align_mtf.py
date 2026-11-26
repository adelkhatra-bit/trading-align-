            align_bot.noter(state, "11", "BTC", state["BTC"]["trade"]["qui"]["11"], 104.0, "TP1 touché")
        self.assertNotIn("11", state["bot_off"])
        self.assertIn("Suivi maintenu uniquement sur : GOLD", sent[0]["text"])
        self.assertNotIn("next:yes", sent[0]["reply_markup"])


class PineOnlyEntryGateTests(unittest.TestCase):
    def _market(self, entry_bar_time=900_000, current_price=101.0):
        return {
            "market": "BTC",
            "dirs": [1] * 11,
            "rsis": [55] * 11,
            "m1": [candle(1_000_000, c=current_price)],
            "r5": [55, 55, 55],
            "b5": [candle(i) for i in range(24)],
            "confirme": 1,
            "fermeture": False,
            "annonce": False,
            "atr": 20.0,
            "atr5": 10.0,
            "atr15": 20.0,
            "posD": 0.5,
            "posW": 0.5,
            "basD": 80.0,
            "hautD": 120.0,
            "basW": 70.0,
            "hautW": 130.0,
            "t": 1_800_000_000,
            "news": "",
            "niv_cles": [],
            "grosses": [],
            "niveaux": [],
            "fvg": [],
            "asie": None,
            "macro": [],
            "ema15": 100.0,
            "ema5": 100.0,
            "b15": [candle(i, o=100, h=102, l=98, c=101) for i in range(3)],
            "tv_indicator_mtf": {
                "available": True,
                "activeTimeframe": "M5",
                "snapshots": {
                    "M15": {
                        "fresh": True,
                        "price": 100.0,
                        "confirmed": True,
                        "robotV12": {
                            "signal": "LONG", "entry": 100.0, "sl": 95.0,
                            "tp1": 110.0, "tp2": 120.0,
                            "planTimeframe": "M15", "entryTimeframe": "M5", "strategy": "DAY",
                            "entryZoneLow": 99.0, "entryZoneHigh": 101.0,
                            "entryDecision": 100.0,
                            "entryBarTime": entry_bar_time,
                            "entryBarOpen": 99.5, "entryBarHigh": 101.0,
                            "entryBarLow": 99.0, "entryBarClose": 100.5,
                            "entryTriggered": False,
                            "confirmed": True,
                        }
                    }
                }
            }
        }

    def test_healthy_bridge_without_direction_reports_mtf_wait_not_bridge_failure(self):
        from unittest.mock import patch
        r = self._market()
        r["confirme"] = 0
        r["require_tv_bridge"] = True
        state = {"t1m": 0}
        with patch.object(align_bot, "plan_cassure", side_effect=AssertionError("local breakout fallback called")), patch.object(align_bot, "point_entree", side_effect=AssertionError("local entry fallback called")):
            out = align_bot.agent("BTC", r, state, "")
        message = " ".join(str(item[0] if isinstance(item, tuple) else item) for item in out)
        self.assertIn("aucune direction multi-UT confirmée", message)
        self.assertIn("Aucun plan Entry/SL/TP émis", message)
        self.assertNotIn("bridge Pine", message)
        self.assertFalse(state.get("trade"))
        self.assertFalse(state.get("ordre"))

    def test_required_bridge_missing_never_falls_back_to_local_entry(self):
        from unittest.mock import patch
        r = self._market()
        r["tv_indicator_mtf"] = {"available": False, "reason": "bridge unavailable"}
        r["require_tv_bridge"] = True
        state = {"t1m": 0}
        with patch.object(align_bot, "plan_cassure", side_effect=AssertionError("local breakout fallback called")), \
             patch.object(align_bot, "point_entree", side_effect=AssertionError("local entry fallback called")):
            out = align_bot.agent("BTC", r, state, "")
        self.assertFalse(state.get("trade"))
        self.assertFalse(state.get("ordre"))
        # Bridge tombé en cours de run (PRET=1) = même règle que le mode sans signal (PRET=0) :
        # aucune entrée, aucune alerte locale, et aucune panne technique diffusée (journal seulement).
        self.assertFalse(any("TradingView" in str(x) or "bridge" in str(x) for x in out))

    def test_no_signal_mode_sends_nothing_and_never_falls_back(self):
        from unittest.mock import patch
        r = self._market()
        r["tv_indicator_mtf"] = {"available": False, "reason": "bridge unavailable"}
        r["require_tv_bridge"] = True
        state = {"t1m": 0}
        with patch.dict(align_bot.os.environ, {"ALIGN_TV_BRIDGE_PRET": "0"}), \
             patch.object(align_bot, "plan_cassure", side_effect=AssertionError("local breakout fallback called")), \
             patch.object(align_bot, "point_entree", side_effect=AssertionError("local entry fallback called")):
            out = align_bot.agent("BTC", r, state, "")
        self.assertFalse(state.get("trade"))
        self.assertFalse(state.get("ordre"))
        self.assertFalse(any("TradingView" in str(x) or "bridge" in str(x) for x in out),
                         "en mode sans signal, aucune panne technique n'est diffusée")

    def test_no_signal_mode_silences_every_local_alert_emitter(self):
        """Bridge absent : aucune alerte calculée en local (radar, retournement, niveaux…) n'est émise."""
        from unittest.mock import patch
        r = self._market()
        r["require_tv_bridge"] = True
        r["tv_indicator_mtf"] = {"available": False, "reason": "bridge inaccessible", "snapshots": {}}
        state = {"t1m": 0}
        locaux = ["manipulation", "meche_suspecte", "niveaux_cles", "resistance_fvg", "suivre_apres_sl",
                  "reprise_entree", "entree_retest", "radar_climax", "retournement_marche",
                  "plan_cassure", "point_entree"]
        patches = [patch.object(align_bot, n, side_effect=AssertionError(f"{n} appelé en mode sans signal"))
                   for n in locaux]
        with patch.dict(align_bot.os.environ, {"ALIGN_TV_BRIDGE_PRET": "0"}):
            for p_ in patches:
                p_.start()
            try:
                out = align_bot.agent("BTC", r, state, "")
            finally:
                for p_ in patches:
                    p_.stop()
        self.assertEqual(out, [])
        self.assertFalse(state.get("trade"))

    def test_bridge_absent_au_demarrage_puis_revenu_relance_le_marche(self):
        """Run démarré sans bridge (PRET=0) : dès que de vraies données fraîches arrivent, le marché repart."""
        from unittest.mock import patch
        with patch.dict(align_bot.os.environ, {"ALIGN_TV_BRIDGE_PRET": "0"}):
            self.assertTrue(align_bot.mode_sans_signal({"tv_indicator_mtf": {"available": False}}))
            self.assertTrue(align_bot.mode_sans_signal({}))
            self.assertFalse(align_bot.mode_sans_signal({"tv_indicator_mtf": {"available": True}}))
        with patch.dict(align_bot.os.environ, {"ALIGN_TV_BRIDGE_PRET": "1"}):
            self.assertFalse(align_bot.mode_sans_signal({}))

    def test_bridge_pret_au_demarrage_puis_tombe_coupe_les_alertes_locales(self):
        """Bridge bon au démarrage (PRET=1) puis indisponible pendant le run : mode sans signal pour ce marché."""
        from unittest.mock import patch
        with patch.dict(align_bot.os.environ, {"ALIGN_TV_BRIDGE_PRET": "1"}):
            tombe = {"require_tv_bridge": True, "tv_indicator_mtf": {"available": False, "reason": "bridge inaccessible"}}
            self.assertTrue(align_bot.mode_sans_signal(tombe))
            revenu = {"require_tv_bridge": True, "tv_indicator_mtf": {"available": True}}
            self.assertFalse(align_bot.mode_sans_signal(revenu))
            # Marché sans exigence de bridge : inchangé.
            self.assertFalse(align_bot.mode_sans_signal({"require_tv_bridge": False, "tv_indicator_mtf": {"available": False}}))

    def test_required_bridge_suppresses_all_local_entry_emitters_when_healthy(self):
        """Même bridge sain : seuls le plan/trigger Pine v25 peuvent produire Entry/SL/TP."""
        from unittest.mock import patch
        r = self._market()
        r["require_tv_bridge"] = True
        state = {"t1m": 0}
        with patch.dict(align_bot.os.environ, {"ALIGN_TV_BRIDGE_PRET": "1"}), \
             patch.object(align_bot, "reprise_entree", side_effect=AssertionError("local resume entry called")), \
             patch.object(align_bot, "entree_retest", side_effect=AssertionError("local retest entry called")), \
             patch.object(align_bot, "radar_climax", side_effect=AssertionError("local radar entry called")), \
             patch.object(align_bot, "retournement_marche", side_effect=AssertionError("local BTC reversal levels called")):
            out = align_bot.agent("BTC", r, state, "")
        self.assertFalse(state.get("trade"))
        self.assertEqual(state.get("ordre", {}).get("e"), 100.0)
        self.assertTrue(any("Attendre le retest" in str(x) for x in out))
        self.assertFalse(any("RADAR_LOCAL" in str(x) for x in out))

    def test_manipulation_bridge_mode_never_publishes_local_entry_or_stop(self):
        bars = [
            dict(candle(i * 900, o=100.0, h=101.0, l=99.0, c=100.0), v=100)
            for i in range(21)
        ]
        bars.append(dict(candle(21 * 900, o=100.0, h=101.0, l=97.0, c=100.5), v=400))
        out = []
        stale_local_order = {"e": 100.0, "sl": 97.0, "tp1": 123.45, "n1": "ancien TP local"}
        align_bot.manipulation(out, "BTC", {
            "b15": bars, "atr": 1.0, "t": 20_000,
            "annonce": False, "confirme": 1, "require_tv_bridge": True,
        }, {"ordre": stale_local_order})
        message = "\n".join(str(item[0] if isinstance(item, tuple) else item) for item in out)
        self.assertIn("Aucun Entry/SL local", message)
        self.assertNotIn("Point d'entrée visé", message)
        self.assertNotIn("SL un peu", message)
        self.assertNotIn("123,45", message)
        self.assertNotIn("TP visé", message)

    def test_required_bridge_waits_for_pine_closed_entry_trigger(self):
        from unittest.mock import patch
        r = self._market()
        r["require_tv_bridge"] = True
        state = {"t1m": 0}
        with patch.object(align_bot, "plan_cassure", side_effect=AssertionError("local breakout fallback called")), \
             patch.object(align_bot, "point_entree", side_effect=AssertionError("local entry fallback called")):
            out = align_bot.agent("BTC", r, state, "")
        self.assertFalse(state.get("trade"))
        self.assertEqual(state.get("ordre")["e"], 100.0)
        self.assertTrue(any("Attendre le retest" in str(x) for x in out))

    def test_required_bridge_uses_exact_pine_levels_once_per_closed_entry_bar(self):
        from unittest.mock import patch
        r = self._market()
        r["require_tv_bridge"] = True
        r["tv_indicator_mtf"]["snapshots"]["M15"]["robotV12"]["entryTriggered"] = True
        state = {"t1m": 0}
        with patch.object(align_bot, "plan_cassure", side_effect=AssertionError("local breakout fallback called")), \
             patch.object(align_bot, "point_entree", side_effect=AssertionError("local entry fallback called")), \
             patch.object(align_bot, "pause_entree_marche", return_value=None), \
             patch.object(align_bot, "bloque_dw", return_value=False), \
             patch.object(align_bot, "profil_trade", return_value={"mode": "DAY"}), \
             patch.object(align_bot, "memoire_refuse", return_value=(False, 0, 0)), \
             patch.object(align_bot, "carte_coach", return_value="PINE_SIGNAL"), \
             patch.object(align_bot, "strategie_trade", return_value={"strat": "SWING"}):
            out = align_bot.agent("BTC", r, state, "")
            self.assertTrue(state.get("trade"))
            self.assertEqual(state["trade"]["strat"], "DAY")
            self.assertEqual(state["trade"]["strat_filtre"], "SWING")
            self.assertEqual(
                (state["trade"]["e"], state["trade"]["sl"], state["trade"]["tp1"], state["trade"]["tp2"]),
                (100.0, 95.0, 110.0, 120.0),
            )
            self.assertEqual(state["trade"]["pine_order_id"], "900000|M5|1")
            self.assertEqual(state.get("pine_entry_bar_done"), 900_000)
            second = align_bot.agent("BTC", r, state, "")
        self.assertEqual(second, [])
        self.assertEqual(state["trade"]["e"], 100.0)

    def test_required_bridge_does_not_send_entry_after_tradingview_price_left_zone(self):
        from unittest.mock import patch
        r = self._market()
        r["require_tv_bridge"] = True
        r["tv_indicator_mtf"]["snapshots"]["M15"]["price"] = 102.0
        r["tv_indicator_mtf"]["snapshots"]["M15"]["robotV12"]["entryTriggered"] = True
        state = {"t1m": 0}
        with patch.object(align_bot, "plan_cassure", side_effect=AssertionError("local breakout fallback called")), patch.object(align_bot, "point_entree", side_effect=AssertionError("local entry fallback called")), patch.object(align_bot, "pause_entree_marche", return_value=None), patch.object(align_bot, "bloque_dw", return_value=False), patch.object(align_bot, "profil_trade", return_value={"mode": "DAY"}), patch.object(align_bot, "memoire_refuse", return_value=(False, 0, 0)), patch.object(align_bot, "strategie_trade", return_value={"strat": "DAY"}):
            out = align_bot.agent("BTC", r, state, "")
        self.assertFalse(state.get("trade"))
        self.assertEqual(state.get("ordre", {}).get("e"), 100.0)
        self.assertTrue(any("hors zone M15" in str(x) for x in out))
        self.assertFalse(state.get("pine_entry_bar_done"))


class TelegramTp1Tp2BridgeTests(unittest.TestCase):
    def _snapshot(self, robot, timeframe="M15"):
        robot = dict(robot)
        entry, stop = float(robot["entry"]), float(robot["sl"])
        signal = str(robot.get("signal") or "LONG").upper()
        risk = abs(entry - stop)
        robot.setdefault("planTimeframe", "M15")
        robot.setdefault("strategy", "DAY")
        robot.setdefault("entryTimeframe", {"SCALPING": "M1", "DAY": "M5", "SWING": "H1"}.get(robot["strategy"], "M5"))
        if signal == "LONG":
            robot.setdefault("entryZoneLow", entry - 0.2 * risk)
            robot.setdefault("entryZoneHigh", entry + 0.2 * risk)
        else:
            robot.setdefault("entryZoneLow", entry - 0.2 * risk)
            robot.setdefault("entryZoneHigh", entry + 0.2 * risk)
        robot.setdefault("entryDecision", (robot["entryZoneLow"] + robot["entryZoneHigh"]) / 2)
        robot.setdefault("entryBarTime", 900_000)
        robot.setdefault("entryBarOpen", entry)
        robot.setdefault("entryBarHigh", max(entry, robot["entryZoneHigh"]))
        robot.setdefault("entryBarLow", min(entry, robot["entryZoneLow"]))
        robot.setdefault("entryBarClose", entry)
        robot.setdefault("entryTriggered", False)
        return {"tv_indicator_mtf": {
            "available": True,
            "activeTimeframe": timeframe,
            "snapshots": {timeframe: {"fresh": True, "price": entry, "confirmed": True, "robotV12": robot}}
        }}

    def test_indicator_bridge_reads_both_targets_for_long(self):
        plan = align_bot.plan_indicateur(self._snapshot({
            "entry": 100, "sl": 95, "tp1": 110, "tp2": 120, "signal": "LONG"
        }))
        self.assertTrue(plan["available"])
        self.assertEqual((plan["tp1"], plan["tp2"], plan["tp"]), (110.0, 120.0, 110.0))

    def test_indicator_bridge_reads_both_targets_for_short(self):
        plan = align_bot.plan_indicateur(self._snapshot({
            "entry": 100, "sl": 105, "tp1": 90, "tp2": 80, "signal": "SHORT"