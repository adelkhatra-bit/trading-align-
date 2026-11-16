import os
import unittest


class AffichageTPGraphiqueV25(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pine", "ALIGN_MTF_PRO_v25.pine")
        with open(chemin, encoding="utf-8") as f:
            cls.pine = f.read()

    def test_tp1_et_tp2_sont_traces_des_qu_un_plan_est_actif(self):
        bloc = self.pine[self.pine.index("// ═════════ LIGNES DU PLAN (TP1, TP2, STOP)"):self.pine.index("// ═════════ BARRE (en bas")]
        self.assertIn("if voirPlan and dirPlan != 0", bloc)
        self.assertIn("lTP1 := line.new(x1, tp1", bloc)
        self.assertIn("lTP2 := line.new(x1, tp2", bloc)
        self.assertIn('eTP1 := label.new(x1, tp1, "TP1 "', bloc)
        self.assertIn('eTP2 := label.new(x1, tp2, "TP2 "', bloc)

    def test_option_apres_tp1_accentue_les_lignes_existantes_sans_doublons(self):
        bloc = self.pine[self.pine.index("// Les deux objectifs restent visibles"):self.pine.index("// ═════════ LIGNES BLANCHES")]
        self.assertIn("line.set_width(lTP2, 3)", bloc)
        self.assertNotIn("line.new(", bloc)

    def test_version_25_ne_change_pas_le_design_de_la_table(self):
        self.assertIn('indicator("ALIGN MTF PRO v25 (Inside)", shorttitle="ALIGN MTF v25",', self.pine)
        self.assertIn('animer   = input.bool(true, "Animation en temps réel", group=grpA)', self.pine)
        self.assertIn('voirPlan = input.bool(true, "Afficher le plan (TP / SL)", group=grpA)', self.pine)


if __name__ == "__main__":
    unittest.main()
