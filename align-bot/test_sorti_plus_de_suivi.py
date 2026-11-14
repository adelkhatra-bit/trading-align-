import unittest
import align_bot as ab


class PlusDeSuiviApresSortie(unittest.TestCase):
    """Vu le 14/11 : Adel sorti à son stop perso, puis « mets-toi à BE » / « direction TP1 » quand même."""

    def etat(self, fini):
        return {"BTC": {"trade": {"d": -1, "e": 64991, "sl": 65300, "tp1": 63100,
                                  "qui": {"42": {"e": 64991, "sl": 65300, "d": -1, "fini": fini}}}}}

    def test_suivi_bloque_si_sorti(self):
        t = ab.taguer("🔒 METS-TOI À BE — 🟠 BTC\n🚦 🟢 ON RESTE EN POSITION", "BTC")
        self.assertTrue(ab.deja_sorti(self.etat(True), "42", t))
        self.assertTrue(ab.deja_sorti(self.etat(True), "42", ab.taguer("🎙 ÇA BOUGE !\n🎯 Direction TP1", "BTC")))

    def test_suivi_garde_si_encore_dedans(self):
        t = ab.taguer("🔒 METS-TOI À BE — 🟠 BTC", "BTC")
        self.assertFalse(ab.deja_sorti(self.etat(False), "42", t))
        self.assertFalse(ab.deja_sorti(self.etat(True), "7", t))          # pas inscrit : info générale gardée

    def test_resultats_toujours_envoyes(self):
        self.assertFalse(ab.deja_sorti(self.etat(True), "42", ab.taguer("🏁 TP2 TOUCHÉ · OBJECTIF FINAL ATTEINT — BTC", "BTC")))


if __name__ == "__main__":
    unittest.main()
