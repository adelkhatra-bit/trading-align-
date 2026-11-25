"""Le bot ne repart jamais à vide en silence si sa mémoire n'a pas été restaurée."""
import json
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

    def test_ancienne_memoire_v3_migre_vers_btc_gold_only_au_chargement(self):
        legacy_trade = {"d": -1, "e": 100.0, "sl": 105.0, "tp1": 90.0, "qui": {"22": {"fini": False}}}
        legacy = {
            "schema_version": 3,
            "chats": ["22", "23", "24", "25"],
            "NASDAQ": {"trade": legacy_trade, "memoire": [{"resultat": "ancien"}]},
            "marches_par_chat": {
                "22": ["NASDAQ", "GOLD"],
                "23": "NASDAQ",
                "24": "BOTH",
                "25": ["BTC", "NASDAQ"],
            },
            "auto": {"NASDAQ": ["22"], "GOLD": []},
            "auto_marches": {"NASDAQ": {"22": True}},
            "coach_live": {"NASDAQ": {"22": {"actif": True}}},
            "canaux_marche": {"NASDAQ": "-100123"},
            "canal_live": {"NASDAQ": {"message_id": 77}},
            "liens_marche": {"NASDAQ": "https://t.me/old"},
            "veille_cloture": {"NASDAQ": {"22": 123}},
            "pause_auto": {"NASDAQ": 1234567890},
        }
        with open(ab.ETAT_FICHIER, "w", encoding="utf-8") as f:
            json.dump(legacy, f)

        state = ab.charger_etat()

        self.assertEqual(state["schema_version"], 4)
        self.assertEqual(state["marches_actifs"], ["BTC", "GOLD"])
        self.assertNotIn("NASDAQ", state)
        self.assertEqual(state["marches_par_chat"]["22"], ["GOLD"])
        self.assertEqual(state["marches_par_chat"]["23"], [])
        self.assertEqual(state["marches_par_chat"]["24"], "BOTH")
        self.assertEqual(state["marches_par_chat"]["25"], ["BTC"])
        for table in ("auto", "auto_marches", "coach_live", "canaux_marche",
                      "canal_live", "liens_marche", "veille_cloture", "pause_auto"):
            self.assertNotIn("NASDAQ", state.get(table, {}), table)
        self.assertNotIn("archives_marches_retirees", state)

    def test_api_muette_compte_comme_deja_en_service(self):
        with mock.patch.object(ab, "_api_github", side_effect=OSError("réseau")):
            self.assertTrue(ab._bot_deja_en_service())
        err = ab.urllib.error.HTTPError("u", 404, "absent", {}, None)
        with mock.patch.object(ab, "_api_github", side_effect=err):
            self.assertFalse(ab._bot_deja_en_service())


if __name__ == "__main__":
    unittest.main()
