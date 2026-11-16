"""Les notifications privées annexes doivent respecter le même opt-in Coach que les signaux."""
import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class CoachOptInExtraPushes(unittest.TestCase):
    def test_annonce_privee_du_live_reservee_aux_coachs_actifs(self):
        state = {"coach_optin": {"GOLD": ["10"]}}
        with patch.object(ab, "_envoi_sur") as send:
            ab.live_annoncer_debut(state, {"10", "20"})
        self.assertEqual([c.args[0] for c in send.call_args_list], ["10"])

    def test_prix_topstep_reserves_aux_coachs_du_marche(self):
        state = {
            "plateforme": {"10": "topstep", "20": "topstep"},
            "marches_par_chat": {"10": ["GOLD"], "20": ["GOLD"]},
            "coach_optin": {"GOLD": ["10"]},
        }
        broker = Mock()
        broker.prix_futures.return_value = 4000.0
        trade = {"d": 1, "e": 4000.0, "sl": 3990.0, "tp1": 4020.0}
        with patch.object(ab, "topstep_trade", broker), \
             patch.object(ab, "texte_prix_topstep", return_value="niveaux") as format_, \
             patch.object(ab, "_envoi_sur") as send:
            n = ab.prix_topstep_inscrits(state, "GOLD", trade, 4000.0)
        self.assertEqual(n, 1)
        format_.assert_called_once()
        self.assertEqual([c.args[0] for c in send.call_args_list], ["10"])


if __name__ == "__main__":
    unittest.main()
