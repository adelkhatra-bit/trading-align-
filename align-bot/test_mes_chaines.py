"""« Mes chaînes » ne doit pas afficher « Question 2/2 » hors de l'accueil."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class MesChaines(unittest.TestCase):
    def texte(self, **kw):
        with mock.patch.object(ab, "_envoi_sur") as envoi:
            ab.accueil_marches({}, "42", **kw)
        return envoi.call_args.kwargs["text"]

    def test_bouton_mes_chaines_sans_numero_de_question(self):
        t = self.texte(questionnaire=False)
        self.assertNotIn("Question", t)
        self.assertIn("MES CHAÎNES", t)
        self.assertIn("Quel marché veux-tu suivre ?", t)

    def test_accueil_garde_la_question_2_sur_2(self):
        self.assertTrue(self.texte().startswith("❓ Question 2/2"))


if __name__ == "__main__":
    unittest.main()
