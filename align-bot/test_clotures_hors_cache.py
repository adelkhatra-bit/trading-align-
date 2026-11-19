"""#556 : une clôture déjà publiée ne l'est jamais une 2e fois, même si state.json est restauré en retard."""
import base64
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class FauxDepot:
    """Branche live-data simulée : aucun appel réseau."""
    def __init__(self):
        self.fichiers, self.ecritures = {}, 0

    def __call__(self, chemin, methode="GET", corps=None):
        nom = chemin.split("/contents/")[1].split("?")[0]
        if methode == "GET":
            if nom not in self.fichiers:
                raise ab.urllib.error.HTTPError(chemin, 404, "absent", {}, None)
            return {"content": base64.b64encode(self.fichiers[nom].encode()).decode(), "sha": "s"}
        self.ecritures += 1
        self.fichiers[nom] = base64.b64decode(corps["content"]).decode()
        return {}


class CloturesHorsCache(unittest.TestCase):
    TR = {"d": -1, "e": 27736.85, "cree": 1794600000}

    def setUp(self):
        ab._FERMES_DISTANTS.update(charge=False, h=[])
        self.depot = FauxDepot()
        self.env = mock.patch.dict(os.environ, {"ALIGN_FERMES_LIVE_DATA": "1", "GITHUB_TOKEN": "x"})
        self.api = mock.patch.object(ab, "_api_github", self.depot)
        self.env.start(); self.api.start()

    def tearDown(self):
        self.api.stop(); self.env.stop()
        ab._FERMES_DISTANTS.update(charge=False, h=[])

    def test_memoire_restauree_en_retard_ne_republie_pas(self):
        etat_avant = {}
        self.assertFalse(ab.deja_cloture(etat_avant, "NASDAQ", self.TR))
        ab.noter_cloture(etat_avant, "NASDAQ", self.TR)
        # Nouveau worker : state.json ancien (la clôture n'y est pas), mémoire du processus vide.
        ab._FERMES_DISTANTS.update(charge=False, h=[])
        etat_restaure = {"fermes": []}
        self.assertTrue(ab.deja_cloture(etat_restaure, "NASDAQ", dict(self.TR)))
        self.assertFalse(ab.deja_cloture(etat_restaure, "BTC", self.TR))

    def test_fichier_public_sans_prix_ni_entree(self):
        ab.noter_cloture({}, "NASDAQ", self.TR)
        contenu = self.depot.fichiers[ab.FERMES_FICHIER]
        self.assertNotIn("27736", contenu)
        self.assertNotIn("NASDAQ", contenu)
        self.assertEqual(len(json.loads(contenu)["h"]), 1)

    def test_desactive_sans_drapeau_aucun_appel(self):
        with mock.patch.dict(os.environ, {"ALIGN_FERMES_LIVE_DATA": "0"}):
            ab.noter_cloture({}, "BTC", self.TR)
            self.assertFalse(ab.deja_cloture({}, "BTC", dict(self.TR, cree=1)))
        self.assertEqual(self.depot.ecritures, 0)

    def test_panne_reseau_ne_bloque_pas_la_cloture(self):
        def panne(*a, **k):
            raise OSError("réseau")
        with mock.patch.object(ab, "_api_github", panne):
            etat = {}
            ab.noter_cloture(etat, "GOLD", self.TR)          # ne lève pas
            self.assertTrue(ab.deja_cloture(etat, "GOLD", self.TR))   # la mémoire locale protège encore


if __name__ == "__main__":
    unittest.main()
