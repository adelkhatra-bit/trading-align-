"""v7.2 (demande d'Adel, 15/11) : résistance / support / FVG touché → détail dans la chaîne + indice SANS prix sur le live ;
coach contre-tendance : tentable, mais déconseillé, on attend le retrace dans le sens du marché."""
import re
import unittest
from unittest.mock import patch

import align_bot as ab


def _r(prev, h, l, c, niveaux=None, fvg=None):
    m1 = [{"t": 1, "o": prev, "h": prev, "l": prev, "c": prev}, {"t": 2, "o": prev, "h": h, "l": l, "c": c}]
    return {"m1": m1, "atr": 100.0, "niveaux": niveaux or [], "fvg": fvg or []}


class ResistanceFvg(unittest.TestCase):
    def test_resistance_touchee_une_seule_fois(self):
        out, cle = [], {}
        r = _r(64000.0, 64105.0, 63990.0, 64080.0, niveaux=[(64100.0, "1h")])
        with patch.object(ab, "live_publier", return_value=True) as lp:
            ab.resistance_fvg(out, "BTC", r, cle)
            ab.resistance_fvg(out, "BTC", r, cle)
        self.assertEqual(len(out), 1)
        self.assertIn("RÉSISTANCE TOUCHÉE", out[0])
        self.assertIn("1h", out[0])
        self.assertIn("Info, pas une entrée", out[0])
        bande = lp.call_args[0][0]
        self.assertIn("lien en bio", bande)
        self.assertIsNone(re.search(r"\d{3}", bande), "jamais de prix sur la bande")

    def test_support_touche_par_le_haut(self):
        out = []
        with patch.object(ab, "live_publier", return_value=True):
            ab.resistance_fvg(out, "BTC", _r(64200.0, 64210.0, 64095.0, 64120.0, niveaux=[(64100.0, "4h")]), {})
        self.assertEqual(len(out), 1)
        self.assertIn("SUPPORT TOUCHÉ", out[0])

    def test_fvg_touchee(self):
        out = []
        with patch.object(ab, "live_publier", return_value=True):
            ab.resistance_fvg(out, "BTC", _r(64000.0, 64060.0, 63990.0, 64040.0, fvg=[(64050.0, 64150.0, "15m", -1)]), {})
        self.assertEqual(len(out), 1)
        self.assertIn("FVG", out[0])

    def test_rien_si_loin(self):
        out = []
        with patch.object(ab, "live_publier", return_value=True) as lp:
            ab.resistance_fvg(out, "BTC", _r(63000.0, 63010.0, 62990.0, 63000.0, niveaux=[(64100.0, "1h")]), {})
        self.assertEqual(out, [])
        lp.assert_not_called()


class CoachContreTendance(unittest.TestCase):
    def test_explosion_contre_la_tendance_deconseillee(self):
        r = {"confirme": -1, "m1": [{"t": 1, "o": 1, "h": 1, "l": 1, "c": 64000.0}], "b15": []}
        for typ in ("acc", "casse"):
            t = ab.texte_ecran("BTC", typ, 1, 5, r, {})
            if t is None:
                continue
            self.assertIn("DÉCONSEILLE", t)
            self.assertIn("🔴 SHORT", t)

    def test_dans_le_sens_rien_de_plus(self):
        r = {"confirme": -1, "m1": [{"t": 1, "o": 1, "h": 1, "l": 1, "c": 64000.0}], "b15": []}
        t = ab.texte_ecran("BTC", "acc", -1, 5, r, {})
        if t is not None:
            self.assertNotIn("DÉCONSEILLE", t)


if __name__ == "__main__":
    unittest.main()
