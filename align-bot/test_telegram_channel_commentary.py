import unittest
import urllib.parse
from unittest.mock import patch

import align_bot as ab


class TelegramMarketChannelCommentaryTests(unittest.TestCase):
    def test_m15_commentary_reaches_only_its_configured_channel_in_pull_mode(self):
        state = {"canaux_marche": {"BTC": "-100btc"}}
        result = {"b15": [{"t": 1000}, {"t": 2000}]}

        with patch.object(ab, "TOKEN", "test-token"), \
             patch.object(ab, "TELEGRAM_PULL_MODE", True), \
             patch.object(ab, "DERNIER_ETAT", state), \
             patch.object(ab, "http_json", return_value={"ok": True, "result": {"message_id": 42}}) as request, \
             patch.object(ab, "texte_coach_live", return_value="🎙 COACH COMMENTATEUR\nℹ️ Info, pas une entrée"), \
             patch.object(ab, "boutons_chaine_marche", return_value=None):
            ab.notifier_canal_marche(state, "BTC", result, {})

        self.assertEqual(request.call_count, 1)
        self.assertEqual(state["canal_live"]["BTC"]["dernier_t"], 1000)
        self.assertIn("-100btc", str(request.call_args))

    def test_market_commentary_permission_rejects_wrong_channel_market_and_trade_levels(self):
        state = {"canaux_marche": {"BTC": "-100btc"}}
        old_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_chat_id", None)
        old_market = getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_market", None)
        with patch.object(ab, "TELEGRAM_PULL_MODE", True), patch.object(ab, "DERNIER_ETAT", state):
            ab.TELEGRAM_PULL_CONTEXT.market_commentary_chat_id = "-100btc"
            ab.TELEGRAM_PULL_CONTEXT.market_commentary_market = "BTC"
            try:
                self.assertTrue(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "-100btc", "text": "🎙 BILAN 15 MIN — Info, pas une entrée"}
                ))
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "-100other", "text": "🎙 BILAN 15 MIN"}
                ))
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "-100btc", "text": "Entry 100 / SL 95 / TP 110"}
                ))
                ab.TELEGRAM_PULL_CONTEXT.market_commentary_market = "NASDAQ"
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "-100btc", "text": "🎙 BILAN 15 MIN"}
                ))
                ab.TELEGRAM_PULL_CONTEXT.market_commentary_market = "BTC"
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendPhoto", {"chat_id": "-100btc", "caption": "🎙 BILAN 15 MIN"}
                ))
            finally:
                ab.TELEGRAM_PULL_CONTEXT.market_commentary_chat_id = old_chat
                ab.TELEGRAM_PULL_CONTEXT.market_commentary_market = old_market

    def test_private_live_coach_commentary_reaches_only_opted_in_subscriber(self):
        state = {"coach_live": {"BTC": {"101": {"started_t": 1000}}}}
        result = {"b15": [{"t": 1000}, {"t": 2000}]}

        with patch.object(ab, "TOKEN", "test-token"), \
             patch.object(ab, "TELEGRAM_PULL_MODE", True), \
             patch.object(ab, "DERNIER_ETAT", state), \
             patch.object(ab, "LANG_EN", {"101"}), \
             patch.object(ab, "http_json", return_value={"ok": True, "result": {"message_id": 43}}) as request, \
             patch.object(ab, "texte_coach_live", return_value="🎙 COACH COMMENTATEUR\nℹ️ Info, pas une entrée"), \
             patch.object(ab, "markup_analyse", return_value=None):
            ab.notifier_coach_live(state, "BTC", result, {})

        self.assertEqual(request.call_count, 1)
        self.assertIn("101", str(request.call_args))
        sent_text = urllib.parse.parse_qs(request.call_args.args[1].decode())["text"][0]
        self.assertIn("LIVE COMMENTATOR", sent_text)
        self.assertNotIn("COACH COMMENTATEUR", sent_text)
        self.assertEqual(state["coach_live"]["BTC"]["101"]["dernier_t"], 1000)

    def test_confirmed_private_position_message_is_fully_translated(self):
        trade = {
            "d": 1, "e": 100.0, "sl": 95.0, "tp1": 110.0, "tp2": 120.0,
            "sl_ut": "5 min",
        }
        french = (
            "🎯 POSITION ALIGN DÉTECTÉE — BTC\\n"
            + ab.resume_ordre(trade)
            + "\\n📍 Suivi actif : SL / passage à BE / TP."
            + "\\nℹ️ ALIGN ne transmet aucun ordre à ton broker."
        )
        english = ab.traduire(french)
        for expected in (
            "ALIGN POSITION DETECTED", "Entry 100", "chart 5 min", "(wick)",
            "Active tracking:", "move to BE", "does not send any orders to your broker",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, english)
        for french_label in ("POSITION ALIGN DÉTECTÉE", "Entrée 100", "vue 5 min",
                             "mèche", "Suivi actif", "passage à BE", "ne transmet aucun ordre"):
            with self.subTest(french_label=french_label):
                self.assertNotIn(french_label, english)

    def test_private_coach_flash_commentary_is_fully_translated(self):
        market = {
            "m1": [
                {"o": 100.0, "c": 100.0},
                {"o": 100.0, "c": 101.0},
                {"o": 101.0, "c": 102.0},
                {"o": 102.0, "c": 104.0},
            ],
            "atr": 1.0,
            "confirme": 1,
        }
        flash = ab.flash_commentateur("BTC", market, {})
        english = ab.traduire(flash)
        for expected in ("IT'S MOVING!", "Buyers are accelerating", "in 3 min",
                         "With the trend", "Waiting for the 15-min close"):
            with self.subTest(expected=expected):
                self.assertIn(expected, english)
        for french_label in ("ÇA BOUGE", "Les acheteurs accélèrent",
                             "Dans le sens de la tendance", "J'attends la clôture"):
            with self.subTest(french_label=french_label):
                self.assertNotIn(french_label, english)

    def test_private_coach_position_requires_exact_opt_in_and_confirmed_position_text(self):
        state = {"coach_live": {"BTC": {"101": {"started_t": 1000}}}}
        old_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_chat_id", None)
        old_market = getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_market", None)
        with patch.object(ab, "TELEGRAM_PULL_MODE", True), patch.object(ab, "DERNIER_ETAT", state):
            ab.TELEGRAM_PULL_CONTEXT.coach_commentary_chat_id = "101"
            ab.TELEGRAM_PULL_CONTEXT.coach_commentary_market = "BTC"
            try:
                position = "🎯 POSITION ALIGN DÉTECTÉE — BTC\nEntrée 100\nSL 95\nTP 110"
                self.assertTrue(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "101", "text": position}
                ))
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "202", "text": position}
                ))
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "101", "text": "Entrée 100 / SL 95 / TP 110"}
                ))
                state["BTC"] = {"trade": {"d": 1, "e": 100, "sl": 95, "tp1": 110}}
                coach_summary = (
                    "🎙 COACH COMMENTATEUR\\n📂 Position : 🟢 LONG\\n"
                    "🟡 Entrée : 100\\n🔴 SL : 95\\n🔵 TP1 : 110"
                )
                self.assertTrue(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "101", "text": coach_summary}
                ))
                state["BTC"]["trade"] = None
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "101", "text": coach_summary}
                ))
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendPhoto", {"chat_id": "101", "caption": "🎙 BILAN 15 MIN"}
                ))
                state["quiet"] = ["101"]
                self.assertFalse(ab._telegram_sortant_autorise(
                    "sendMessage", {"chat_id": "101", "text": "🎙 BILAN 15 MIN"}
                ))
            finally:
                ab.TELEGRAM_PULL_CONTEXT.coach_commentary_chat_id = old_chat
                ab.TELEGRAM_PULL_CONTEXT.coach_commentary_market = old_market

    def test_private_coach_helper_restores_temporary_permission_after_send(self):
        old_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_chat_id", None)
        old_market = getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_market", None)
        with patch.object(ab, "_envoi_sur", side_effect=lambda *a, **k: (
            getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_chat_id", None),
            getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_market", None),
        )) as send:
            result = ab._telegram_envoyer_commentaire_coach_prive(
                {"coach_live": {"GOLD": {"101": {"started_t": 1000}}}},
                "101", "GOLD", "Commentaire"
            )
        self.assertEqual(result, ("101", "GOLD"))
        send.assert_called_once()
        self.assertEqual(getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_chat_id", None), old_chat)
        self.assertEqual(getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_market", None), old_market)

    def test_commentary_helper_restores_temporary_permission_after_send(self):
        state = {"canaux_marche": {"GOLD": "-100gold"}}
        old_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_chat_id", None)
        old_market = getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_market", None)
        with patch.object(ab, "_envoi_sur", side_effect=lambda *a, **k: (
            getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_chat_id", None),
            getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_market", None),
        )) as send:
            result = ab._telegram_envoyer_commentaire_canal(state, "GOLD", "-100gold", "Commentaire")
        self.assertEqual(result, ("-100gold", "GOLD"))
        send.assert_called_once()
        self.assertEqual(getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_chat_id", None), old_chat)
        self.assertEqual(getattr(ab.TELEGRAM_PULL_CONTEXT, "market_commentary_market", None), old_market)


    def test_live_coach_commentary_and_activation_are_fully_translated(self):
        candle = {"o": 100.0, "h": 102.0, "l": 99.0, "c": 101.0, "t": 2000}
        market = {
            "m1": [{"c": 101.0}],
            "b15": [candle, {"o": 100.0, "h": 102.0, "l": 99.0, "c": 101.0, "t": 2000}],
            "confirme": 1,
            "dirs": [-1] * 11,  # valeurs live volontairement opposées : elles ne doivent pas être utilisées
            "dirs_cloturees": [1] * 11,
            "sqzs": [0] * 11,
        }
        with patch.object(ab, "prochaine_cloture_bougie", return_value=3000):
            french = ab.texte_coach_live("BTC", candle, market, {}, public=True)
        english = ab.traduire(french)
        for expected in (
            "LIVE COMMENTATOR", "LIVE", "15-MINUTE SUMMARY", "Information, not an entry",
            "Candle rising", "Range:", "Trend:", "Timeframes:", "Vs confirmed direction LONG", "W1 context:", "Roles:", "Next:",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, english)
        for french_label in ("COACH COMMENTATEUR", "BILAN 15 MIN", "Bougie en hausse",
                             "Écart :", "Tendance :", "Unités :", "Prochaine :"):
            with self.subTest(french_label=french_label):
                self.assertNotIn(french_label, english)

        activation = (
            "🎙 COACH COMMENTATEUR ACTIVÉ — BTC\n"
            "🔎 Surveillance continue : je cherche une configuration d'entrée confirmée, sans inventer de signal.\n"
            "🕯 Commentaire aux clôtures 15 min utiles ; aucune Entry/SL/TP sans confirmation Pine.\n"
            "📍 Dès qu'une position est ouverte par ALIGN, je poursuis son suivi.\n"
            "⏹ Pour arrêter : le bouton sous mes messages."
        )
        translated_activation = ab.traduire(activation)
        self.assertIn("LIVE COMMENTATOR ACTIVATED", translated_activation)
        self.assertNotIn("Surveillance continue", translated_activation)
        self.assertNotIn("Commentaire aux clôtures", translated_activation)


    def test_live_coach_explains_wick_direction_and_uses_only_closed_mtf(self):
        cases = (
            (
                {"o": 100.0, "h": 105.0, "l": 99.0, "c": 101.0, "t": 2000},
                "👁 Mèche haute dominante : pression vendeuse possible — rejet non établi sans résistance identifiée",
                "no confirmed resistance rejection",
            ),
            (
                {"o": 100.0, "h": 101.0, "l": 95.0, "c": 99.0, "t": 2000},
                "👁 Mèche basse dominante : pression acheteuse possible — rejet non établi sans support identifié",
                "no confirmed support rejection",
            ),
            (
                {"o": 100.0, "h": 104.0, "l": 96.0, "c": 100.0, "t": 2000},
                "👁 Mèches des deux côtés : indécision",
                "Wicks on both sides: indecision",
            ),
        )
        with patch.object(ab, "prochaine_cloture_bougie", return_value=3000):
            for candle, french_label, english_label in cases:
                market = {
                    "m1": [{"c": candle["c"]}],
                    "confirme": 0,
                    "dirs_cloturees": [1] * 8 + [-1] * 3,
                    "dirs": [-1] * 11,
                    "sqzs": [0] * 11,
                }
                french = ab.texte_coach_live("BTC", candle, market, {}, public=True)
                english = ab.traduire(french)
                with self.subTest(french_label=french_label):
                    self.assertIn(french_label, french)
                    self.assertIn(english_label, english)
                    self.assertIn("Biais de contexte : LONG dominant • 8/11", french)

            missing = {
                "m1": [{"c": 101.0}],
                "confirme": 0,
                "dirs": [1] * 11,
                "sqzs": [0] * 11,
            }
            unavailable = ab.texte_coach_live(
                "BTC", {"o": 100.0, "h": 101.0, "l": 99.0, "c": 100.5, "t": 2000},
                missing, {}, public=True
            )
            self.assertIn("UT clôturées : indisponibles", unavailable)
            self.assertIn("aucun biais LONG/SHORT déduit", unavailable)
            self.assertNotIn("11/11", unavailable)

    def test_pine_wait_status_uses_candidate_scores_without_authorizing_entry(self):
        cases = (
            ({"available": False, "signal": "WAIT", "long_score": 68, "short_score": 0},
             "biais candidat LONG", "Score candidat LONG : 68/100"),
            ({"available": False, "signal": "WAIT", "long_score": 0, "short_score": 74},
             "biais candidat SHORT", "Score candidat SHORT : 74/100"),
            ({"available": False, "signal": "WAIT", "long_score": 0, "short_score": 0},
             "aucun biais LONG/SHORT confirmé", "aucune configuration M15"),
        )
        for plan, expected_title, expected_reason in cases:
            title, reason = ab.statut_attente_pine(plan)
            with self.subTest(plan=plan):
                self.assertIn(expected_title, title)
                self.assertIn(expected_reason, reason)
                if "aucun biais" in title:
                    self.assertIn("Aucune entrée autorisée", reason)
                else:
                    self.assertIn("aucune entrée", reason.lower())

    def test_plan_indicateur_preserves_wait_signal_and_candidate_scores(self):
        market = {
            "tv_indicator_mtf": {
                "activeTimeframe": "M15",
                "snapshots": {
                    "M15": {
                        "fresh": True,
                        "robotFresh": True,
                        "robotV12": {
                            "signal": "WAIT",
                            "verdict": "À SURVEILLER : confirmation manquante",
                            "long_score": 0,
                            "short_score": 74,
                        },
                    }
                },
            }
        }
        plan = ab.plan_indicateur(market)
        self.assertIs(plan["available"], False)
        self.assertEqual(plan["signal"], "WAIT")
        self.assertEqual(plan["short_score"], 74)
        title, reason = ab.statut_attente_pine(plan)
        self.assertIn("biais candidat SHORT", title)
        self.assertIn("Score candidat SHORT : 74/100", reason)
        english = ab.traduire(title + "\n" + reason)
        self.assertIn("candidate SHORT bias", english)
        self.assertIn("No plan confirmed", english)

    def test_pine_wait_status_distinguishes_incomplete_data_and_confirmed_direction(self):
        title, reason = ab.statut_attente_pine({"available": False, "signal": "SHORT"})
        self.assertIn("signal SHORT", title)
        self.assertIn("Entrée bloquée", reason)

        title, reason = ab.statut_attente_pine({"available": False, "reason": "snapshot M15 périmé"})
        self.assertIn("données Pine v25 absentes ou périmées", title)
        self.assertIn("snapshot M15 périmé", reason)

        title, reason = ab.statut_attente_pine({"available": True, "confirmed": False, "direction": 1})
        self.assertIn("CONFIRMATION MTF PINE EN ATTENTE", title)
        self.assertIn("Configuration LONG M15 détectée", reason)
        self.assertIn("Aucune entrée autorisée", reason)
        english = ab.traduire(title + "\\n" + reason)
        self.assertIn("LONG M15 setup detected", english)
        self.assertIn("Wait for MTF confirmation and the closed trigger", english)

    def test_position_followup_allows_levels_only_for_exact_active_position_owner(self):
        position = {"fini": False, "e": 100.0, "sl": 95.0}
        trade = {"qui": {"101": position}}
        # Suivi manuel explicite : le membre est dans trade["qui"], même sans abonnement auto/radar.
        state = {"auto": {"BTC": []}, "bot_off": [], "BTC": {"trade": trade}}
        old = {
            "chat": getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_chat_id", None),
            "market": getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_market", None),
            "trade": getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_position_trade", None),
            "position": getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_position_record", None),
            "closure": getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_position_closure", False),
        }
        with patch.object(ab, "TOKEN", "test-token"), \
             patch.object(ab, "TELEGRAM_PULL_MODE", True), \
             patch.object(ab, "DERNIER_ETAT", state), \
             patch.object(ab, "http_json", return_value={"ok": True, "result": {"message_id": 51}}) as request:
            result = ab._telegram_envoyer_commentaire_coach_prive(
                state, "101", "BTC", "⚠️ BTC\n🛑 Stop 95", trade=trade, position=position
            )
            self.assertTrue(result.get("ok"))
            self.assertEqual(request.call_count, 1)
            wrong_chat = ab._telegram_envoyer_commentaire_coach_prive(
                state, "202", "BTC", "⚠️ BTC\n🛑 Stop 95", trade=trade, position=position
            )
            other_trade = {"qui": {"101": position}}
            wrong_trade = ab._telegram_envoyer_commentaire_coach_prive(
                state, "101", "BTC", "⚠️ BTC\n🛑 Stop 95", trade=other_trade, position=position
            )
            self.assertTrue(wrong_chat.get("blocked_by_pull_mode"))
            self.assertTrue(wrong_trade.get("blocked_by_pull_mode"))
            state["bot_off"] = ["101"]
            stopped = ab._telegram_envoyer_commentaire_coach_prive(
                state, "101", "BTC", "⚠️ BTC\n🛑 Stop 95", trade=trade, position=position
            )
            state["bot_off"] = []
            state["quiet"] = ["101"]
            quiet = ab._telegram_envoyer_commentaire_coach_prive(
                state, "101", "BTC", "⚠️ BTC\n🛑 Stop 95", trade=trade, position=position
            )
            self.assertTrue(stopped.get("blocked_by_pull_mode"))
            self.assertTrue(quiet.get("blocked_by_pull_mode"))
        self.assertEqual(getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_chat_id", None), old["chat"])
        self.assertEqual(getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_commentary_market", None), old["market"])
        self.assertEqual(getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_position_trade", None), old["trade"])
        self.assertEqual(getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_position_record", None), old["position"])
        self.assertEqual(getattr(ab.TELEGRAM_PULL_CONTEXT, "coach_position_closure", False), old["closure"])

    def test_position_closure_is_allowed_once_for_the_exact_finished_trade_owner(self):
        position = {"fini": True, "e": 100.0, "sl": 95.0}
        trade = {"qui": {"101": position}}
        state = {"BTC": {"trade": trade}, "auto": {"BTC": []}, "bot_off": ["101"]}
        message = "🏁 CLÔTURE CONFIRMÉE — TP — BTC\nEntrée 100\nSortie confirmée 110"
        with patch.object(ab, "TOKEN", "test-token"), \
             patch.object(ab, "TELEGRAM_PULL_MODE", True), \
             patch.object(ab, "DERNIER_ETAT", state), \
             patch.object(ab, "http_json", return_value={"ok": True, "result": {"message_id": 52}}) as request:
            result = ab._telegram_envoyer_commentaire_coach_prive(
                state, "101", "BTC", message, trade=trade, position=position, fermeture=True
            )
            self.assertTrue(result.get("ok"))
            self.assertEqual(request.call_count, 1)
            denied_non_closure = ab._telegram_envoyer_commentaire_coach_prive(
                state, "101", "BTC", "Entrée 100 / SL 95 / TP 110",
                trade=trade, position=position, fermeture=True
            )
            state["quiet"] = ["101"]
            denied_quiet = ab._telegram_envoyer_commentaire_coach_prive(
                state, "101", "BTC", message, trade=trade, position=position, fermeture=True
            )
            self.assertTrue(denied_non_closure.get("blocked_by_pull_mode"))
            self.assertTrue(denied_quiet.get("blocked_by_pull_mode"))

    def test_candle_close_push_requires_exact_veille_cloture_opt_in(self):
        state = {"veille_cloture": {"BTC": {"101": {"tf": "15m"}}}}
        with patch.object(ab, "TOKEN", "test-token"), \
             patch.object(ab, "TELEGRAM_PULL_MODE", True), \
             patch.object(ab, "DERNIER_ETAT", state), \
             patch.object(ab, "coach_actif", return_value=True), \
             patch.object(ab, "marche_autorise", return_value=True), \
             patch.object(ab, "autorise", return_value=False), \
             patch.object(ab, "http_json", return_value={"ok": True, "result": {"message_id": 53}}) as request:
            ok = ab._telegram_envoyer_veille_cloture(state, "101", "BTC", "🕯 Clôture 15 min : biais inchangé")
            denied = ab._telegram_envoyer_veille_cloture(state, "101", "BTC", "Entry 100 / SL 95 / TP 110")
            wrong_user = ab._telegram_envoyer_veille_cloture(state, "202", "BTC", "🕯 Clôture 15 min : biais inchangé")
        self.assertTrue(ok.get("ok"))
        self.assertTrue(denied.get("blocked_by_pull_mode"))
        self.assertTrue(wrong_user.get("blocked_by_pull_mode"))
        self.assertEqual(request.call_count, 1)

    def test_radar_send_edit_delete_are_scoped_to_opted_in_user_and_exact_message(self):
        state = {"radar_mem": {"101": {"mid": 42}}}
        with patch.object(ab, "TOKEN", "test-token"), \
             patch.object(ab, "TELEGRAM_PULL_MODE", True), \
             patch.object(ab, "DERNIER_ETAT", state), \
             patch.object(ab, "coach_actif", side_effect=lambda etat, cid, m: str(cid) == "101" and m == "BTC"), \
             patch.object(ab, "autorise", return_value=False), \
             patch.object(ab, "http_json", return_value={"ok": True, "result": {"message_id": 54}}) as request:
            sent = ab._telegram_envoyer_radar(state, "101", "sendMessage", text="📡 RADAR BTC — proche, alignement pas encore atteint")
            denied_levels = ab._telegram_envoyer_radar(state, "101", "sendMessage", text="Entry 100 / SL 95 / TP 110")
            edited = ab._telegram_envoyer_radar(state, "101", "editMessageText", message_id=42, text="📡 RADAR BTC — mise à jour")
            deleted = ab._telegram_envoyer_radar(state, "101", "deleteMessage", message_id=42)
            denied_wrong_id = ab._telegram_envoyer_radar(state, "101", "editMessageText", message_id=99, text="📡 RADAR BTC")
            denied_other_chat = ab._telegram_envoyer_radar(state, "202", "sendMessage", text="📡 RADAR BTC")
        self.assertTrue(sent.get("ok"))
        self.assertTrue(denied_levels.get("blocked_by_pull_mode"))
        self.assertTrue(edited.get("ok"))
        self.assertTrue(deleted.get("ok"))
        self.assertTrue(denied_wrong_id.get("blocked_by_pull_mode"))
        self.assertTrue(denied_other_chat.get("blocked_by_pull_mode"))
        self.assertEqual(request.call_count, 3)



    def test_jauge_private_position_vip_channel_and_exact_message_scope(self):
        position = {"fini": False, "sl": 95.0}
        cle = {"jauge": {}, "trade": {"qui": {"101": position}}}
        state = {"BTC": cle, "canal": "-100", "auto": {"BTC": ["101", "202"]}}
        with patch.object(ab, "TOKEN", "test-token"), \
             patch.object(ab, "TELEGRAM_PULL_MODE", True), \
             patch.object(ab, "DERNIER_ETAT", state), \
             patch.object(ab, "coach_actif", side_effect=lambda etat, cid, m: str(cid) in {"101", "202"} and m == "BTC"), \
             patch.object(ab, "marche_autorise", side_effect=lambda etat, cid, m: str(cid) in {"101", "202"} and m == "BTC"), \
             patch.object(ab, "autorise", return_value=False), \
             patch.object(ab, "http_json", return_value={"ok": True, "result": {"message_id": 61}}) as request:
            private_position = ab._telegram_envoyer_jauge(
                state, "BTC", "101", cle, "sendMessage",
                text="📊 BTC\n🎯 TP1 110\n🛑 Ton stop 95", disable_notification="true"
            )
            cle["jauge"]["101"] = 61
            edited = ab._telegram_envoyer_jauge(
                state, "BTC", "101", cle, "editMessageText", message_id=61,
                text="📊 BTC\n🎯 TP1 110\n🛑 Ton stop 95"
            )
            wrong_id = ab._telegram_envoyer_jauge(
                state, "BTC", "101", cle, "editMessageText", message_id=62, text="📊 BTC mise à jour"
            )
            non_vip_levels = ab._telegram_envoyer_jauge(
                state, "BTC", "202", cle, "sendMessage", text="📊 BTC\n🎯 TP1 110\n🛑 SL 95"
            )
            vip_channel = ab._telegram_envoyer_jauge(
                state, "BTC", "-100", cle, "sendMessage", text="📊 BTC\n🎯 TP1 110"
            )
            cleanup = ab._telegram_envoyer_jauge(
                state, "BTC", "101", cle, "deleteMessage", nettoyage=True, message_id=61
            )
            other_chat = ab._telegram_envoyer_jauge(
                state, "BTC", "303", cle, "sendMessage", text="📊 BTC prochaine position"
            )
        self.assertTrue(private_position.get("ok"))
        self.assertTrue(edited.get("ok"))
        self.assertTrue(wrong_id.get("blocked_by_pull_mode"))
        self.assertTrue(non_vip_levels.get("blocked_by_pull_mode"))
        self.assertTrue(vip_channel.get("ok"))
        self.assertTrue(cleanup.get("ok"))
        self.assertTrue(other_chat.get("blocked_by_pull_mode"))
        self.assertEqual(request.call_count, 4)

    def test_maj_jauge_uses_scoped_helper_and_does_not_mark_failed_edit_as_sent(self):
        cle = {"jauge": {}, "jauge_txt": {}, "jauge_t": {}}
        state = {"BTC": cle}
        with patch.object(ab, "marche_autorise", return_value=True), \
             patch.object(ab, "coach_actif", return_value=True), \
             patch.object(ab, "en_position", return_value=False), \
             patch.object(ab, "jauge", return_value="📊 BTC — zone en préparation"), \
             patch.object(ab.time, "time", return_value=1000), \
             patch.object(ab, "_telegram_envoyer_jauge", side_effect=[
                 {"ok": True, "result": {"message_id": 71}},
                 {"ok": False, "blocked_by_pull_mode": True},
             ]) as send:
            ab.maj_jauge(state, "BTC", {}, cle, {"101"})
            self.assertEqual(cle["jauge"].get("101"), 71)
            cle["jauge_txt"]["101"] = "ancienne jauge"
            cle["jauge_t"]["101"] = 0
            ab.maj_jauge(state, "BTC", {}, cle, {"101"})
        self.assertEqual(send.call_count, 2)
        self.assertEqual(send.call_args_list[0].args[:5], (state, "BTC", "101", cle, "sendMessage"))
        self.assertEqual(send.call_args_list[1].args[:5], (state, "BTC", "101", cle, "editMessageText"))
        self.assertEqual(cle["jauge_txt"]["101"], "ancienne jauge")
        self.assertEqual(cle["jauge_t"]["101"], 0)

    def test_jauge_operation_success_handles_telegram_noop_and_missing_message(self):
        self.assertTrue(ab._telegram_jauge_operation_ok({"ok": True}, "editMessageText"))
        self.assertTrue(ab._telegram_jauge_operation_ok({"ok": False, "description": "message is not modified"}, "editMessageText"))
        self.assertTrue(ab._telegram_jauge_operation_ok({"ok": False, "description": "message to delete not found"}, "deleteMessage"))
        self.assertFalse(ab._telegram_jauge_operation_ok({"ok": False, "blocked_by_pull_mode": True}, "editMessageText"))
        import inspect
        source = inspect.getsource(ab.maj_jauge)
        self.assertIn("_telegram_envoyer_jauge", source)
        self.assertNotIn("telegram(", source)



if __name__ == "__main__":
    unittest.main()
