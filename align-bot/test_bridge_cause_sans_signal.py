"""Le journal doit donner la cause exacte d'un marché en « mode sans signal » (diagnostic, jamais Telegram)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class CauseSansSignalTests(unittest.TestCase):
    def test_aucun_snapshot_avec_dernier_refus(self):
        payload = {"ok": False, "snapshots": {}, "lastRejection": {"error": "stale_or_future_snapshot", "ageMs": 12_400}}
        detail = ab.detail_bridge_invalide(payload)
        self.assertIn("aucun snapshot reçu", detail)
        self.assertIn("dernier envoi refusé : stale_or_future_snapshot (il y a 12 s)", detail)

    def test_ut_active_perimee_et_ut_requises_perimees_ou_absentes(self):
        snaps = {tf: {"fresh": True} for tf in ("M5", "M15", "H1", "H4", "D1")}
        snaps["H1"] = {"fresh": False}
        payload = {"ok": False, "activeTimeframe": "M5", "activeTimeframeFresh": False,
                   "activeTimeframeAgeMs": 41_000, "snapshots": snaps, "lastRejection": None}
        detail = ab.detail_bridge_invalide(payload)
        self.assertIn("UT active M5 périmée (41 s)", detail)
        self.assertIn("UT absentes W1", detail)
        self.assertIn("UT périmées H1", detail)
        self.assertNotIn("refusé", detail)

    def test_reponse_illisible(self):
        self.assertEqual(ab.detail_bridge_invalide(None), "réponse illisible")

    def test_la_raison_publique_ne_change_pas(self):
        # « reason » est repris ailleurs dans le bot : seul « detail » porte le diagnostic.
        import inspect
        source = inspect.getsource(ab.fetch_tv_mtf)
        self.assertIn('"reason": "réponse bridge invalide"', source)
        self.assertIn('"detail": detail_bridge_invalide(payload)', source)


if __name__ == "__main__":
    unittest.main()
