"""Tests du consentement Telegram, des vrais TP et du show TradingView."""
import os, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class TelegramOptIn(unittest.TestCase):
    def test_no_private_messages_or_market_selection_by_default(self):
        state = {}
        self.assertFalse(ab.bot_on(state, "10"))
        self.assertFalse(ab.notifications_on(state, "10"))
        self.assertEqual(ab.marches_choisis(state, "10"), set())
        self.assertFalse(ab.marche_autorise(state, "10", "GOLD"))
        self.assertEqual(ab.destinataires_message(state, {"10"}, "🥇 GOLD — SIGNAL"), [])
        self.assertEqual(ab.destinataires_gratuits(state), [])

    def test_private_routing_requires_optin_and_selected_market(self):
        state = {"marches_par_chat": {"10": ["GOLD"], "11": ["BTC"]},
                 "telegram_optin_chats": ["10"]}
        self.assertEqual(ab.destinataires_message(state, {"10", "11"}, "🥇 GOLD — SIGNAL"), ["10"])
        self.assertEqual(ab.destinataires_message(state, {"10", "11"}, "🟠 BTC — SIGNAL"), [])

    def test_bot_automatic_mode_requires_selected_market_and_explicit_on(self):
        state = {}
        with mock.patch.object(ab, "_envoi_sur"):
            self.assertFalse(ab.regler_bot(state, "10", True))
        self.assertFalse(ab.bot_on(state, "10"))
        state["marches_par_chat"] = {"10": ["NASDAQ"]}
        with mock.patch.object(ab, "_envoi_sur"):
            self.assertTrue(ab.regler_bot(state, "10", True))
        self.assertTrue(ab.bot_on(state, "10"))
        self.assertTrue(ab.notifications_on(state, "10"))
        with mock.patch.object(ab, "_envoi_sur"):
            self.assertTrue(ab.regler_bot(state, "10", False))
        self.assertFalse(ab.bot_on(state, "10"))

    def test_legacy_auto_follow_does_not_send_until_user_revalidates(self):
        state = {"auto": {"GOLD": ["10"]}, "marches_par_chat": {"10": ["GOLD"]}}
        trade = {"e": 100.0, "sl": 98.0, "tp1": 104.0, "tp2": 108.0, "d": 1, "qui": {}}
        with mock.patch.object(ab, "_envoi_sur") as send:
            ab.entrer_inscrits(state, "GOLD", trade, chats=[])
        self.assertEqual(trade["qui"], {})
        send.assert_not_called()

    def test_legacy_live_coach_and_close_watch_are_silenced_without_optin(self):
        state = {
            "coach_live": {"GOLD": {"10": {"expire": 9999999999, "dernier_t": 0}}},
            "veille_cloture": {"GOLD": {"10": {"tf": "15m", "dernier_t": 0, "restants": 3}}},
        }
        r = {"b15": [{"t": 1, "o": 100, "h": 101, "l": 99, "c": 100}], "m1": []}
        with mock.patch.object(ab, "_envoi_sur") as send:
            ab.notifier_coach_live(state, "GOLD", r, {})
            ab.notifier_clotures(state, "GOLD", r, {})
        self.assertEqual(state["coach_live"]["GOLD"], {})
        self.assertEqual(state["veille_cloture"]["GOLD"], {})
        send.assert_not_called()

    def test_manual_analysis_is_one_shot_and_does_not_arm_future_messages(self):
        state = {}
        r = {"m1": [{"c": 100.0}]}
        with mock.patch.object(ab, "signature_analyse", return_value="sig"), \
             mock.patch.object(ab, "texte_apercu", return_value="analyse"), \
             mock.patch.object(ab, "markup_analyse", return_value="kb"), \
             mock.patch.object(ab, "autorise", return_value=True), \
             mock.patch.object(ab, "_envoi_sur", return_value={"ok": True, "result": {"message_id": 1}}), \
             mock.patch.object(ab, "armer_cloture") as arm:
            ab.envoyer_analyse_a(state, "10", "GOLD", r, {})
        arm.assert_not_called()


class GoldNasdaqPlanDisplay(unittest.TestCase):
    def _render(self, market, dirs):
        r = {
            "m1": [{"c": 100.0}], "dirs": dirs, "dirPlan": -1,
            "plan_fige": {"d": -1, "e": 99.0, "sl": 101.0, "tp1": 95.0, "tp2": 90.0,
                          "n1": "pivot 15m", "n2": "pivot 1h"},
        }
        with mock.patch.object(ab, "alignement", return_value=(-1, 8)), \
             mock.patch.object(ab, "verdict", return_value=("🟡 PATIENCE", "H1/H4 attendent")), \
             mock.patch.object(ab, "profil_strategie", return_value={"mode": "SWING"}), \
             mock.patch.object(ab, "mouvement_recent_m1", return_value="M1 : mouvement"), \
             mock.patch.object(ab, "voyants_unites", return_value=["M1", "M3", "M5", "M15", "H1", "H4"]), \
             mock.patch.object(ab, "objectifs_marche", return_value=["objectifs probables"]), \
             mock.patch.object(ab, "zone_retournement_visee", return_value=[]):
            return ab.texte_apercu(market, r, {}, vip=False)

    def test_gold_displays_actual_tp1_tp2_when_h1_h4_agree(self):
        dirs = [0] * 11
        dirs[7] = dirs[9] = -1
        txt = self._render("GOLD", dirs)
        self.assertIn("PLAN INDICATIF — H1 + H4 CONFIRMÉS", txt)
        self.assertIn("TP1 : 95", txt)
        self.assertIn("TP2 : 90", txt)
        self.assertIn("attends « ENTRÉE AUTORISÉE »", txt)

    def test_nasdaq_displays_actual_tp1_tp2_when_h1_h4_agree(self):
        dirs = [0] * 11
        dirs[7] = dirs[9] = -1
        txt = self._render("NASDAQ", dirs)
        self.assertIn("TP1 : 95", txt)
        self.assertIn("TP2 : 90", txt)

    def test_no_directional_tp_is_published_when_h1_h4_conflict(self):
        dirs = [0] * 11
        dirs[7], dirs[9] = -1, 1
        txt = self._render("GOLD", dirs)
        self.assertIn("TP directionnels non validés", txt)
        self.assertNotIn("TP1 : 95", txt)
        self.assertNotIn("TP2 : 90", txt)

    def test_chart_draws_tp1_and_tp2_from_actual_plan_fields(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        dashboard = open(os.path.join(root, "dashboard.html"), encoding="utf-8").read()
        self.assertIn("positionLike.tp1", dashboard)
        self.assertIn("positionLike.tp2", dashboard)
        self.assertIn("title: 'TP1'", dashboard)
        self.assertIn("title: 'TP2'", dashboard)
        self.assertIn("'TP1: ' + formatPrice(livePosition.tp1", dashboard)
        self.assertIn("'TP2: ' + formatPrice(livePosition.tp2)", dashboard)

    def test_tradingview_popup_is_one_shot_and_only_for_executable_signal(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        popup_html = open(os.path.join(root, "tradingview-analyzer", "popup.html"), encoding="utf-8").read()
        popup_js = open(os.path.join(root, "tradingview-analyzer", "popup.js"), encoding="utf-8").read()
        self.assertIn('id="signalShowOverlay"', popup_html)
        self.assertIn("function showConfirmedSignal(", popup_js)
        self.assertIn("canEnter && _sigExecutable && !_sigConflict && !_sigDirConflict", popup_js)
        self.assertIn("state._lastSignalShowKey === key", popup_js)
        self.assertIn("setTimeout(closeConfirmedSignal, 5200)", popup_js)


if __name__ == "__main__":
    unittest.main()
