import unittest
from unittest.mock import patch

import align_bot as ab


class ZoneConsumptionDirectionnelle(unittest.TestCase):
    """Regression coverage for directional mitigation percentages."""
    def b(self, high, low):
        return {"h": high, "l": low, "o": low, "c": high}

    def test_fvg_haussiere_est_mangee_depuis_le_haut(self):
        self.assertEqual(ab.zone_mangee_directionnelle([self.b(112, 105)], 100, 110, 1), 50)

    def test_fvg_baissiere_est_mangee_depuis_le_bas(self):
        self.assertEqual(ab.zone_mangee_directionnelle([self.b(105, 98)], 100, 110, -1), 50)

    def test_order_block_haussier_et_baissier_utilisent_le_bord_d_arrivee(self):
        self.assertEqual(ab.zone_mangee_directionnelle([self.b(112, 107)], 100, 110, 1), 30)
        self.assertEqual(ab.zone_mangee_directionnelle([self.b(103, 98)], 100, 110, -1), 30)

    def test_revisites_ne_s_additionnent_pas(self):
        bars = [self.b(110, 108), self.b(110, 106), self.b(110, 107)]
        self.assertEqual(ab.zone_mangee_directionnelle(bars, 100, 110, 1), 40)

    def test_mèche_qui_traverse_entierement_compte_100_pourcent(self):
        self.assertEqual(ab.zone_mangee_directionnelle([self.b(112, 98)], 100, 110, 1), 100)
        self.assertEqual(ab.zone_mangee_directionnelle([self.b(112, 98)], 100, 110, -1), 100)

    def test_aucune_donnee_ou_sens_invalide(self):
        self.assertIsNone(ab.zone_mangee_directionnelle([], 100, 110, 1))
        self.assertIsNone(ab.zone_mangee_directionnelle([self.b(105, 95)], 100, 110, 0))

    def test_order_block_touche_annonce_sa_consumption(self):
        # OB baissier : le prix remonte depuis le bas dans la zone [100, 110].
        st = [None] * 8 + [110.0, 100.0, None, None]
        r = {
            "m1": [
                {"t": 1, "o": 95.0, "h": 96.0, "l": 94.0, "c": 95.0},
                {"t": 2, "o": 101.0, "h": 105.0, "l": 99.0, "c": 104.0},
            ],
            "b5": [self.b(105.0, 99.0)],
            "atr": 100.0,
            "struct_ut": {"5": st},
        }
        out = []
        with patch.object(ab, "live_publier", return_value=True):
            ab.resistance_fvg(out, "GOLD", r, {})
        self.assertEqual(len(out), 1)
        self.assertIn("ORDER BLOCK TOUCHÉ", out[0])
        self.assertIn("Zone mangée à 50 %", out[0])


class PineZoneConsumption(unittest.TestCase):
    def test_fvg_boxes_show_progressive_consumption(self):
        from pathlib import Path
        pine = (Path(__file__).parent / "pine" / "ALIGN_MTF_PRO_v24_3_PROPOSITION.pine").read_text(encoding="utf-8")
        self.assertIn("f_zone_pct(top, bottom, sens) =>", pine)
        self.assertIn('box.set_text(b, "FVG • " + str.tostring(pct) + "% consommée")', pine)
        self.assertIn("box.set_bgcolor(b, color.new(base, 85 - int(pct * 0.45)))", pine)

    def test_order_block_box_shows_its_consumption(self):
        from pathlib import Path
        pine = (Path(__file__).parent / "pine" / "ALIGN_MTF_PRO_v24_3_PROPOSITION.pine").read_text(encoding="utf-8")
        self.assertIn('text="ORDER BLOCK • " + str.tostring(pctOB) + "% consommé"', pine)
        self.assertIn("pctOB = f_zone_pct(obH_, obL_, sensOB)", pine)


if __name__ == "__main__":
    unittest.main()
