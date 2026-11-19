"""v12.2.11 : le heartbeat de l'écran du live passe par GM_xmlhttpRequest (test de non-régression du transport)."""
import os
import unittest

JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "live", "align-bande-live.user.js")


class HeartbeatGmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(JS, encoding="utf-8") as f:
            cls.js = f.read()

    def test_entete_autorise_gm_xmlhttprequest_vers_ntfy(self):
        self.assertIn("// @grant        GM_xmlhttpRequest", self.js)
        self.assertIn("// @connect      ntfy.sh", self.js)
        self.assertNotIn("// @grant        none", self.js)

    def test_heartbeat_et_evenements_passent_par_envoyerecran(self):
        self.assertIn("function envoyerEcran(corps)", self.js)
        self.assertIn("GM_xmlhttpRequest({ method: 'POST'", self.js)
        self.assertIn("envoyerEcran('PING|LIVE_SCREEN|' + Date.now())", self.js)
        self.assertIn("envoyerEcran(['EVT', mk, typ, d, minutes", self.js)

    def test_repli_fetch_si_pas_de_gm(self):
        self.assertIn("typeof GM_xmlhttpRequest === 'function'", self.js)
        self.assertIn("fetch(url, { method: 'POST', body: corps", self.js)

    def test_api_tradingview_lue_via_unsafewindow(self):
        # Avec @grant le script est isolé : sans unsafeWindow, window.TradingViewApi est invisible et chart() renvoie null.
        self.assertIn("// @grant        unsafeWindow", self.js)
        self.assertIn("const PAGE = (typeof unsafeWindow !== 'undefined' && unsafeWindow) ? unsafeWindow : window;", self.js)
        self.assertIn("return PAGE.TradingViewApi.activeChart();", self.js)
        self.assertNotIn("return window.TradingViewApi.activeChart();", self.js)

    def test_chaines_historiques_conservees(self):
        self.assertIn("PING|LIVE_SCREEN|", self.js)
        self.assertIn("setInterval(pingEcran, 25000)", self.js)



class CodeEcranNonAffiche(unittest.TestCase):
    def test_menu_live_code_ecran_seulement_en_prive(self):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "align_bot.py"), encoding="utf-8") as f:
            src = f.read()
        self.assertIn("if int(cid) > 0:", src)  # code écran seulement en chat privé


if __name__ == "__main__":
    unittest.main()
