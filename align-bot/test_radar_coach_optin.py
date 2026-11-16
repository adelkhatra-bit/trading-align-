"""Le radar Telegram ne doit jamais contourner le consentement Coach par marché."""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class RadarCoachOptIn(unittest.TestCase):
    def test_selection_de_deux_marches_sans_double_optin_ne_declenche_pas_le_radar(self):
        state = {
            "marches_par_chat": {"10": ["GOLD", "NASDAQ"]},
            "coach_optin": {"NASDAQ": ["10"]},
        }
        with patch.object(ab, "autorise", return_value=True):
            self.assertEqual(ab.destinataires_radar(state, {"10"}), [])

    def test_radar_respecte_optin_persistant_et_suivi_multi_ut(self):
        state = {
            "marches_par_chat": {
                "10": ["GOLD", "NASDAQ"],
                "20": ["GOLD", "NASDAQ"],
                "30": ["GOLD"],
                "40": ["GOLD"],
            },
            "coach_optin": {
                "GOLD": ["20", "40"],
                "NASDAQ": ["20"],
            },
            "veille_cloture": {
                "GOLD": {
                    "30": {"multi": True},
                    "40": {"multi": True},
                }
            },
        }
        with patch.object(ab, "autorise", return_value=True):
            self.assertEqual(ab.destinataires_radar(state, {"10", "20", "30", "40"}), ["20", "40"])


if __name__ == "__main__":
    unittest.main()
