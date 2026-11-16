"""v7.4 (modèle d'Adel, 15/11) : le gratuit suit le bot jusqu'à son premier TP ; SL = une autre position offerte ;
après le TP, les positions arrivent en DIFFÉRÉ (le temps réel = VIP) ; petit « tu dors ? » une fois par jour."""
import time
import unittest
from unittest.mock import MagicMock, patch

import align_bot as ab


def _etat():
    return {"prospects": ["111"], "bienvenue": {"111": "BTC"}, "lien": "https://t.me/+x"}


def _tr():
    return {"d": 1, "e": 100.0, "cree": time.time() - 600, "qui": {"111": {"d": 1, "e": 100.0}}}


class EssaiGratuit(unittest.TestCase):
    tout = False

    def _fin(self, etat, sortie, motif, gain):
        with patch.object(ab, "telegram", MagicMock(return_value={})), patch.object(ab, "_envoi_sur", MagicMock()) as env, \
                patch.object(ab, "TOUT_GRATUIT", self.tout):
            try:
                ab.publier_resultat(etat, "BTC", _tr(), sortie, motif, gain)
            except Exception:
                pass                               # la partie chaînes peut dépendre d'autres réglages : seul le gratuit est testé ici
        return " ".join(str(c.kwargs.get("text", "")) for c in env.call_args_list)

    def test_sl_on_offre_une_autre_position(self):
        etat = _etat()
        txt = self._fin(etat, 99.0, "SL touché", -1.0)
        self.assertNotIn("111", etat.get("bienvenue", {}))
        self.assertNotIn("111", etat.get("essai_fini", []))
        self.assertNotIn("111", etat.get("bot_off", []))
        self.assertIn("autre position", txt)

    def test_tp_essai_valide(self):
        etat = _etat()
        txt = self._fin(etat, 101.0, "TP1 touché", 1.0)
        self.assertIn("111", etat.get("essai_fini", []))
        self.assertIn("111", etat.get("bot_off", []))
        self.assertIn("différé", txt)


class ToutGratuit(EssaiGratuit):
    """Décision d'Adel (15/11) : pour le moment tout est gratuit, le bot reste allumé après un TP."""
    tout = True

    def test_sl_on_offre_une_autre_position(self):
        etat = _etat()
        self._fin(etat, 99.0, "SL touché", -1.0)
        self.assertNotIn("111", etat.get("bot_off", []))

    def test_tp_essai_valide(self):
        etat = _etat()
        self._fin(etat, 101.0, "TP1 touché", 1.0)
        self.assertNotIn("111", etat.get("essai_fini", []))
        self.assertNotIn("111", etat.get("bot_off", []))
        self.assertNotIn("111", etat.get("bienvenue", {}))


class Differe(unittest.TestCase):
    def test_position_envoyee_en_differe(self):
        etat = {"lien": "https://t.me/+x", "auto": {"BTC": ["111"]}, "differe": [{"t": 5, "c": "111", "txt": "🟠 BTC position"}, {"t": 10 ** 12, "c": "222", "txt": "plus tard"}]}
        with patch.object(ab, "telegram", MagicMock(return_value={})) as tg:
            ab.envoyer_differes(etat, now=100, dodo=False)
        self.assertEqual(tg.call_count, 1)
        self.assertIn("EN DIFFÉRÉ", tg.call_args.kwargs["text"])
        self.assertIn("N'entre pas maintenant", tg.call_args.kwargs["text"])
        self.assertEqual([x["c"] for x in etat["differe"]], ["222"])

    def test_dodo_textes_differents(self):
        self.assertEqual(len(set(ab.DODO_TXT)), len(ab.DODO_TXT))


if __name__ == "__main__":
    unittest.main()
