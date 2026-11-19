"""Régressions : file Telegram après 429, calendrier inconnu, retours à la ligne des messages."""
import os
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class FileTelegram(unittest.TestCase):
    def item(self, prive):
        return {"key": "k", "chat_id": "42", "method": "sendMessage", "prive": prive,
                "params": {"chat_id": "42", "text": "Réponse à ton bouton"}, "tries": 0, "next_t": 0}

    def test_message_bloque_par_le_mode_pull_n_est_pas_compte_comme_envoye(self):
        etat = {"telegram_outbox": [self.item(False)]}
        with mock.patch.object(ab, "telegram", return_value={"ok": False, "blocked_by_pull_mode": True}):
            self.assertEqual(ab.traiter_file_telegram(etat, maintenant=10), 0)
        self.assertEqual(etat["telegram_outbox"], [])

    def test_reponse_privee_rejouee_dans_son_contexte_prive(self):
        vu = {}
        def faux(methode, **p):
            vu["ctx"] = (ab.TELEGRAM_PULL_CONTEXT.chat_id, ab.TELEGRAM_PULL_CONTEXT.private)
            return {"ok": True, "result": {"message_id": 1}}
        ab.TELEGRAM_PULL_CONTEXT.chat_id, ab.TELEGRAM_PULL_CONTEXT.private = "", False
        etat = {"telegram_outbox": [self.item(True)]}
        with mock.patch.object(ab, "telegram", side_effect=faux):
            self.assertEqual(ab.traiter_file_telegram(etat, maintenant=10), 1)
        self.assertEqual(vu["ctx"], ("42", True))
        self.assertEqual((ab.TELEGRAM_PULL_CONTEXT.chat_id, ab.TELEGRAM_PULL_CONTEXT.private), ("", False))

    def test_reponse_non_ok_reste_en_file(self):
        etat = {"telegram_outbox": [self.item(False)]}
        with mock.patch.object(ab, "telegram", return_value={"ok": False, "description": "Too Many Requests"}):
            self.assertEqual(ab.traiter_file_telegram(etat, maintenant=10), 0)
        self.assertEqual(len(etat["telegram_outbox"]), 1)
        self.assertEqual(etat["telegram_outbox"][0]["tries"], 1)


class CalendrierInconnu(unittest.TestCase):
    def test_calendrier_jamais_lu_bloque_comme_une_annonce(self):
        self.assertTrue(ab.annonce_proche({}, int(time.time())))

    def test_calendrier_trop_ancien_bloque(self):
        now = int(time.time())
        self.assertTrue(ab.annonce_proche({"cal": {"t": now - 7 * 3600, "ev": []}}, now))

    def test_calendrier_frais_sans_annonce_ne_bloque_pas(self):
        now = int(time.time())
        self.assertFalse(ab.annonce_proche({"cal": {"t": now - 600, "ev": []}}, now))

    def test_calendrier_frais_avec_annonce_proche_bloque(self):
        now = int(time.time())
        self.assertTrue(ab.annonce_proche({"cal": {"t": now - 600, "ev": [{"t": now + 300}]}}, now))

    def test_texte_news_dit_indisponible_si_trop_ancien(self):
        now = int(time.time())
        self.assertEqual(ab.news_txt({"cal": {"t": now - 7 * 3600, "ev": []}}), "📰 News : calendrier indisponible")


class RetoursALaLigne(unittest.TestCase):
    def test_aucun_antislash_n_litteral_dans_le_code_des_messages(self):
        import io, tokenize
        src = open(ab.__file__, encoding="utf-8").read()
        mauvais = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.STRING or tok.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
                if "\\\\n" in tok.string and not tok.string.lstrip("bfuBFU").startswith(("r'", 'r"', "R'", 'R"')):
                    mauvais.append(tok.start[0])
        self.assertEqual(mauvais, [], f"« \\\\n » affiché tel quel aux lignes {mauvais}")


if __name__ == "__main__":
    unittest.main()
