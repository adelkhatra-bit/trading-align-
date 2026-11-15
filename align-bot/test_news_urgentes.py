"""Demande d'Adel 15/11 : news de dernière minute (RSS gratuit + vraie IA), jamais inventée, priorité sur la bande."""
import os, sys, unittest, unittest.mock, email.utils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab

T = 1_800_000_000


def rss(titre, age):
    d = email.utils.formatdate(T - age)
    return f"<rss><channel><item><title>{titre}</title><pubDate>{d}</pubDate></item></channel></rss>"


class News(unittest.TestCase):
    def test_titres_recents_et_importants(self):
        self.assertEqual(ab.titres_urgents(rss("Missile attack hits port", 600), T), ["Missile attack hits port"])
        self.assertEqual(ab.titres_urgents(rss("Missile attack hits port", 7200), T), [])      # trop vieux
        self.assertEqual(ab.titres_urgents(rss("Celebrity wedding", 60), T), [])             # sans impact

    def test_publie_si_l_ia_confirme(self):
        etat, envoyes, bande = {"canaux_marche": {"GOLD": -1}}, [], []
        with unittest.mock.patch.object(ab, "ia", lambda *a, **k: "Missile sur un port | Missile hits a port\nGold ↑ refuge\nResserre ton SL"), \
             unittest.mock.patch.object(ab, "TOKEN", "x"), unittest.mock.patch.object(ab, "_envoi_sur", lambda c, **k: envoyes.append(k["text"])), \
             unittest.mock.patch.object(ab, "live_publier", lambda t: bande.append(t)):
            t = ab.news_urgentes(etat, T, lire=lambda u: rss("Missile attack hits port", 300))
            self.assertIsNone(ab.news_urgentes(etat, T + 400, lire=lambda u: rss("Missile attack hits port", 300)))   # déjà vue
        self.assertIn("NEWS DE DERNIÈRE MINUTE", t); self.assertIn("DYOR", envoyes[0])
        self.assertTrue(bande[0].startswith("NEWS:Missile sur un port|"))

    def test_rien_si_l_ia_dit_aucun(self):
        with unittest.mock.patch.object(ab, "ia", lambda *a, **k: "AUCUN"), unittest.mock.patch.object(ab, "live_publier", lambda t: self.fail("bande")):
            self.assertIsNone(ab.news_urgentes({}, T, lire=lambda u: rss("Fed Powell speaks on rate cut", 120)))


if __name__ == "__main__":
    unittest.main()
