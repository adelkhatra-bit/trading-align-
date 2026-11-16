"""Demande d'Adel 15/11 : fenêtre « ALIGN EN DIRECT » (gain réel) seulement après la moitié du chemin vers le TP1 et avec de vraies positions."""
import os, sys, unittest, unittest.mock
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


def r_(p):
    return {"m1": [{"c": p}]}


class Pnl(unittest.TestCase):
    def setUp(self):
        self.pub = []
        ab._LIVE_DERNIER.clear()
        self.p = [unittest.mock.patch.object(ab, "live_publier", side_effect=lambda t: self.pub.append(t) or True)]
        for x in self.p:
            x.start()

    def tearDown(self):
        for x in self.p:
            x.stop()

    def cle(self):
        return {"trade": {"e": 100.0, "tp1": 110.0, "d": 1}}

    def test_affiche_le_vrai_pnl_des_l_ouverture_pas_apres_50_pourcent(self):
        robot = unittest.mock.Mock(profit_ouvert=lambda e, m: 12.0)
        with unittest.mock.patch.object(ab, "auto_trade", robot), unittest.mock.patch.object(ab, "topstep_trade", None):
            self.assertEqual(ab.live_pnl({}, "BTC", self.cle(), r_(101), now=1000), 12.0)
        self.assertEqual(self.pub, ["CMD:pnl:+12.00:BTC"])

    def test_montre_le_vrai_gain_puis_s_eteint(self):
        etat = {}
        robot = unittest.mock.Mock(profit_ouvert=lambda e, m: 42.5)
        with unittest.mock.patch.object(ab, "auto_trade", robot), unittest.mock.patch.object(ab, "topstep_trade", None):
            self.assertEqual(ab.live_pnl(etat, "BTC", self.cle(), r_(106), now=1000), 42.5)
            ab.live_pnl(etat, "BTC", {}, r_(106), now=1100)
        self.assertEqual(self.pub, ["CMD:pnl:+42.50:BTC", "CMD:pnl:off:BTC"])

    def test_jamais_de_chiffre_invente(self):
        robot = unittest.mock.Mock(profit_ouvert=lambda e, m: None)       # mode test : aucune vraie position
        with unittest.mock.patch.object(ab, "auto_trade", robot), unittest.mock.patch.object(ab, "topstep_trade", None):
            self.assertIsNone(ab.live_pnl({}, "BTC", self.cle(), r_(108), now=1000))
        self.assertEqual(self.pub, [])


if __name__ == "__main__":
    unittest.main()
