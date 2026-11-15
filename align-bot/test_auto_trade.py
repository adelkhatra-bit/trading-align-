import unittest, unittest.mock
import auto_trade as at


class TestAutoTrade(unittest.TestCase):
    def test_risque_75_dollars_btc(self):
        # BTC : contrat 1, SL à 400 $ → SL élargi 500 $ → 75 / 500 = 0,15 lot
        self.assertEqual(at.volume(64000, 63600, 1), 0.15)

    def test_gold_contrat_100(self):
        self.assertEqual(at.volume(4000, 3995, 100), 0.12)

    def test_sl_trop_large_pas_de_position(self):
        self.assertEqual(at.volume(64000, 54000, 1), 0.0)

    def test_sl_elargi_dans_le_bon_sens(self):
        self.assertLess(at.sl_elargi(100, 90), 90)
        self.assertGreater(at.sl_elargi(100, 110), 110)

    def test_garde_fou_perte_du_jour(self):
        etat = {}
        self.assertTrue(at.garde_fou(etat, "A", 10000)[0])
        self.assertFalse(at.garde_fou(etat, "A", 9640)[0])
        self.assertFalse(at.garde_fou(etat, "A", 10000)[0])   # reste coupé jusqu'au lendemain

    def test_garde_fou_perte_totale(self):
        etat = {}
        self.assertFalse(at.garde_fou(etat, "B", 9240)[0])
        self.assertTrue(etat["auto_coupe_total"]["B"])

    def test_marche_eteint_aucun_ordre(self):
        r = at.executer({"auto_marches": {"BTC": False}}, {"marche": "BTC", "sens": "LONG", "e": 1, "sl": 0.5, "tp": 2})
        self.assertFalse(r[0]["ok"])

    def test_mode_test_par_defaut_n_envoie_rien(self):
        rep = {"account-information": {"equity": 10000}, "positions": [], "specification": {"contractSize": 1},
               "current-price": {"bid": 64010, "ask": 64012}, "/symbols": ["BTCUSD", "XAUUSD"]}
        def faux(meth, chemin, corps=None):
            self.assertNotEqual(meth, "POST")
            return next(v for k, v in rep.items() if chemin.endswith(k))
        with unittest.mock.patch.object(at, "TOKEN", "x"), unittest.mock.patch.object(at, "COMPTES", ["c1"]), \
             unittest.mock.patch.object(at, "REEL", False), unittest.mock.patch.object(at, "_api", side_effect=faux), \
             unittest.mock.patch.object(at.time, "sleep"):
            r = at.executer({"auto_marches": {"BTC": True}}, {"marche": "BTC", "sens": "SHORT", "e": 64000, "sl": 64400, "tp": 63000},
                            journal=lambda *_: None)
        self.assertTrue(r[0]["ok"] and r[0]["test"])
        self.assertEqual(r[0]["ordre"]["actionType"], "ORDER_TYPE_SELL")
        self.assertEqual(r[0]["ordre"]["stopLoss"], 64510.0)   # même distance que le graphique (×1,25), posée sur le prix MT5
        self.assertEqual(r[0]["ordre"]["takeProfit"], 63010.0)

    def test_position_opposee_refusee(self):
        rep = {"account-information": {"equity": 10000}, "positions": [{"symbol": "BTCUSD", "type": "POSITION_TYPE_BUY"}], "/symbols": ["BTCUSD"]}
        with unittest.mock.patch.object(at, "TOKEN", "x"), unittest.mock.patch.object(at, "COMPTES", ["c1"]), \
             unittest.mock.patch.object(at, "_api", side_effect=lambda m, c, b=None: next(v for k, v in rep.items() if c.endswith(k))), \
             unittest.mock.patch.object(at.time, "sleep"):
            r = at.executer({"auto_marches": {"BTC": True}}, {"marche": "BTC", "sens": "SHORT", "e": 1, "sl": 2, "tp": 0},
                            journal=lambda *_: None)
        self.assertEqual(r[0]["raison"], "position opposée interdite")


class TestSymboles(unittest.TestCase):
    def test_nasdaq_trouve_le_nom_du_serveur(self):
        with unittest.mock.patch.object(at, "_api", return_value=["US100", "XAUUSD"]):
            self.assertEqual(at.symbole({}, "c", "NASDAQ"), "US100")


if __name__ == "__main__":
    unittest.main()
