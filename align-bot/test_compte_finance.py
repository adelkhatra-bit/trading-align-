"""Demande d'Adel 15/11 : message compte financé COURT + boutons (affiliation) + « En savoir plus » pour le texte long."""
import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class CompteFinance(unittest.TestCase):
    def test_court_et_complet(self):
        t = ab.texte_compte_finance_court()
        self.assertLessEqual(len(t.split("\n")), 8)
        for k in (ab.TOPSTEP_CODE, ab.FUNDEDNEXT_CODE, "DÉMO", "DYOR", "parrainage"):
            self.assertIn(k, t)

    def test_boutons(self):
        l = json.loads(ab.markup_compte_finance())["inline_keyboard"]
        textes = [b["text"] for r in l for b in r]
        self.assertIn("🏦 Topstep -15 %", textes); self.assertIn("🟢 FundedNext -5 %", textes)
        self.assertTrue(l[-1][0]["url"].endswith("?start=financeplus"))


if __name__ == "__main__":
    unittest.main()
