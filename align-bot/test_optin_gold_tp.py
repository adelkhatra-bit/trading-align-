"""Consentement Telegram, analyse ponctuelle et publication des vrais TP Gold/NASDAQ."""
import os, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class TelegramOptIn(unittest.TestCase):
    def test_no_bot_or_private_notifications_by_default(self):
        state = {}
        self.assertFalse(ab.bot_on(state, "10"))
        self.assertFalse(ab.notifications_on(state, "10"))
        self.assertEqual(ab.marches_choisis(state, "10"), set())
        self.assertFalse(ab.marche_autorise(state, "10", "GOLD"))
        self.assertEqual(ab.destinataires_message(state, {"10"}, "🥇 GOLD — SIGNAL"), [])

    def test_follow_optin_only_delivers_the_selected_market(self):
        state = {"marches_par_chat": {"10": ["GOLD"]}, "telegram_optin_chats": ["10"]}
        self.assertEqual(ab.destinataires_message(state, {"10"}, "🥇 GOLD — SIGNAL"), ["10"])
        self.assertEqual(ab.destinataires_message(state, {"10"}, "🟠 BTC — SIGNAL"), [])

    def test_bot_automatic_mode_requires_market_selection_and_explicit_on(self):
        state = {}
        with mock.patch.object(ab, "_envoi_sur"):
            self.assertFalse(ab.regler_bot(state, "10", True))
        self.assertFalse(ab.bot_on(state, "10"))
        state["marches_par_chat"] = {"10": ["NASDAQ"]}
        with mock.patch.object(ab, "_envoi_sur"):
            ab.regler_bot(state, "10", True)
        self.assertTrue(ab.bot_on(state, "10"))
        self.assertTrue(ab.notifications_on(state, "10"))
        with mock.patch.object(ab, "_envoi_sur"):
            ab.regler_bot(state, "10", False)
        self.assertFalse(ab.bot_on(state, "10"))

    def test_private_messages_require_both_explicit_consent_and_market(self):
        state = {"marches_par_chat": {"10": "GOLD", "11": "BTC"},
                 "telegram_optin_chats": ["10"]}
        self.assertEqual(ab.destinataires_message(state, {"10", "11"}, "🥇 GOLD — SIGNAL"), ["10"])
        self.assertEqual(ab.destinataires_message(state, {"10", "11"}, "🟠 BTC — SIGNAL"), [])

    def test_manual_analysis_does_not_arm_automatic_notifications(self):
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

    def test_tradingview_chart_draws_both_tp1_and_tp2_from_plan_fields(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        dashboard = open(os.path.join(root, "dashboard.html"), encoding="utf-8").read()
        self.assertIn("positionLike.tp1", dashboard)
        self.assertIn("positionLike.tp2", dashboard)
        self.assertIn("title: 'TP1'", dashboard)
        self.assertIn("title: 'TP2'", dashboard)
        self.assertIn("'TP1: ' + formatPrice(livePosition.tp1", dashboard)
        self.assertIn("'TP2: ' + formatPrice(livePosition.tp2)", dashboard)

    def test_tradingview_popup_show_is_one_shot_and_needs_executable_signal(self):
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        popup_html = open(os.path.join(root, "tradingview-analyzer", "popup.html"), encoding="utf-8").read()
        popup_js = open(os.path.join(root, "tradingview-analyzer", "popup.js"), encoding="utf-8").read()
        self.assertIn('id="signalShowOverlay"', popup_html)
        self.assertIn("function showConfirmedSignal(", popup_js)
        self.assertIn("canEnter && _sigExecutable && !_sigConflict && !_sigDirConflict", popup_js)
        self.assertIn("state._lastSignalShowKey === key", popup_js)
        self.assertIn("setTimeout(closeConfirmedSignal, 5200)", popup_js)

    def test_no_directional_tp_is_published_when_h1_h4_conflict(self):
        dirs = [0] * 11
        dirs[7], dirs[9] = -1, 1
        txt = self._render("GOLD", dirs)
        self.assertIn("TP directionnels non validés", txt)
        self.assertNotIn("TP1 : 95", txt)
        self.assertNotIn("TP2 : 90", txt)


if __name__ == "__main__":
    unittest.main()
