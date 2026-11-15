import unittest, unittest.mock
import auto_trade as at


class TestAutoTrade(unittest.TestCase):
    def test_risque_1re_entree_50_dollars_btc(self):
        # BTC : contrat 1, SL à 400 $ → SL élargi 500 $ → 50 / 500 = 0,10 lot (la moitié du budget de 100 $)
        self.assertEqual(at.volume(64000, 63600, 1), 0.1)

    def test_gold_contrat_100(self):
        self.assertEqual(at.volume(4000, 3995, 100), 0.08)

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



class TestRachats(unittest.TestCase):
    """Stratégie d'Adel (15/11) : rachats sur repli, TOUTES les positions ensemble ≤ 100 $ de perte."""
    plan = {"sens": "LONG", "e": 100.0, "sl": 90.0, "tp": 120.0, "taille": 1.0, "pas": 0.01, "be": False, "rachats": 0}

    def pos(self, *x):
        return [{"openPrice": o, "stopLoss": 90.0, "volume": v} for o, v in x]

    def test_rachat_sur_repli(self):
        quoi, lots = at.decision(dict(self.plan), self.pos((100.0, 5.0)), 95.0)   # 5 lots × 10 $ = 50 $ de risque
        self.assertEqual(quoi, "rachat"); self.assertEqual(lots, 5.0)             # 25 $ / 5 $ = 5 lots

    def test_jamais_plus_de_100_dollars(self):
        pos = self.pos((100.0, 5.0), (95.0, 5.0), (96.0, 3.5))                   # 50 + 25 + 21 = 96 $
        quoi, lots = at.decision(dict(self.plan, rachats=2, dernier_rachat=99.0), pos, 94.0)
        self.assertEqual(quoi, "rachat"); self.assertLessEqual(at.risque_positions(pos, 1) + lots * 4, 100.0001)

    def test_pas_de_rachat_sans_repli_ni_sous_le_sl(self):
        self.assertEqual(at.decision(dict(self.plan), self.pos((100.0, 5.0)), 99.0), (None, None))
        self.assertEqual(at.decision(dict(self.plan), self.pos((100.0, 5.0)), 89.0), (None, None))

    def test_be_a_plus_1r(self):
        quoi, moy = at.decision(dict(self.plan), self.pos((100.0, 5.0), (95.0, 5.0)), 108.0)   # moyenne 97,5 → +10,5
        self.assertEqual(quoi, "be"); self.assertAlmostEqual(moy, 97.5)



class TestComptes(unittest.TestCase):
    def test_id_colle_deux_fois(self):
        u = "94844ff0-ddf5-4ec2-8f26-261addf6272c"
        self.assertEqual(at.lire_comptes(u + u), [u])
        self.assertEqual(at.lire_comptes(""), [])



class TestPrixFiable(unittest.TestCase):
    import datetime as _d
    N = _d.datetime(2026, 11, 15, 19, 0, tzinfo=_d.timezone.utc)

    def test_prix_fige_refuse(self):
        ok, r = at.prix_fiable({"time": "2026-11-15T10:00:00.000Z"}, 64900, 64900, self.N)
        self.assertFalse(ok); self.assertIn("figé", r)

    def test_ecart_trop_grand_refuse(self):
        ok, r = at.prix_fiable({"time": "2026-11-15T18:59:30Z"}, 68387, 64900, self.N)
        self.assertFalse(ok); self.assertIn("trop loin", r)

    def test_prix_frais_et_proche_ok(self):
        self.assertTrue(at.prix_fiable({"time": "2026-11-15T18:59:30Z"}, 64950, 64900, self.N)[0])


if __name__ == "__main__":
    unittest.main()
