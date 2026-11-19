"""Le bot ne repart jamais à vide en silence si sa mémoire n'a pas été restaurée."""
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class MemoireAbsente(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.fichier = mock.patch.object(ab, "ETAT_FICHIER", os.path.join(self.dir.name, "state.json"))
        self.fichier.start()

    def tearDown(self):
        self.fichier.stop()
        self.dir.cleanup()

    def test_bot_deja_en_service_sans_memoire_arret_preventif(self):
        with mock.patch.dict(os.environ, {"ALIGN_EXIGER_MEMOIRE": "1", "ALIGN_ETAT_VIERGE_OK": ""}), \
             mock.patch.object(ab, "_bot_deja_en_service", return_value=True):
            with self.assertRaises(RuntimeError) as ctx:
                ab.charger_etat()
        self.assertIn("MÉMOIRE ALIGN ABSENTE", str(ctx.exception))

    def test_premier_demarrage_volontaire_autorise(self):
        with mock.patch.dict(os.environ, {"ALIGN_EXIGER_MEMOIRE": "1", "ALIGN_ETAT_VIERGE_OK": "1"}), \
             mock.patch.object(ab, "_bot_deja_en_service", return_value=True):
            self.assertEqual(ab.charger_etat()["schema_version"], ab.STATE_SCHEMA_VERSION)

    def test_jamais_tourne_demarre_a_vide(self):
        with mock.patch.dict(os.environ, {"ALIGN_EXIGER_MEMOIRE": "1", "ALIGN_ETAT_VIERGE_OK": ""}), \
             mock.patch.object(ab, "_bot_deja_en_service", return_value=False):
            self.assertEqual(ab.charger_etat()["schema_version"], ab.STATE_SCHEMA_VERSION)

    def test_hors_production_inchange(self):
        with mock.patch.dict(os.environ, {"ALIGN_EXIGER_MEMOIRE": "0"}):
            self.assertEqual(ab.charger_etat()["schema_version"], ab.STATE_SCHEMA_VERSION)

    def test_api_muette_compte_comme_deja_en_service(self):
        with mock.patch.object(ab, "_api_github", side_effect=OSError("réseau")):
            self.assertTrue(ab._bot_deja_en_service())
        err = ab.urllib.error.HTTPError("u", 404, "absent", {}, None)
        with mock.patch.object(ab, "_api_github", side_effect=err):
            self.assertFalse(ab._bot_deja_en_service())


if __name__ == "__main__":
    unittest.main()
