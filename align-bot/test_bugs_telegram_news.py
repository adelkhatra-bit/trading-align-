"""Régressions : file Telegram après 429, calendrier inconnu, retours à la ligne des messages."""
import os
import sys
import time
import urllib.parse
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class TelegramPullAuthorization(unittest.TestCase):
    def setUp(self):
        self.old_mode = ab.TELEGRAM_PULL_MODE
        self.old_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "chat_id", None)
        self.old_private = getattr(ab.TELEGRAM_PULL_CONTEXT, "private", False)
        self.old_news_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "news_chat_id", None)
        self.old_state = ab.DERNIER_ETAT
        ab.TELEGRAM_PULL_MODE = True
        ab.DERNIER_ETAT = None

    def tearDown(self):
        ab.TELEGRAM_PULL_MODE = self.old_mode
        ab.TELEGRAM_PULL_CONTEXT.chat_id = self.old_chat
        ab.TELEGRAM_PULL_CONTEXT.private = self.old_private
        ab.TELEGRAM_PULL_CONTEXT.news_chat_id = self.old_news_chat
        ab.DERNIER_ETAT = self.old_state

    def test_private_reply_allowed_only_for_requesting_chat(self):
        ab.TELEGRAM_PULL_CONTEXT.chat_id = "42"
        ab.TELEGRAM_PULL_CONTEXT.private = True
        self.assertTrue(ab._telegram_sortant_autorise(
            "sendMessage", {"chat_id": "42", "text": "Réponse à ta demande"}
        ))
        self.assertFalse(ab._telegram_sortant_autorise(
            "sendMessage", {"chat_id": "43", "text": "Réponse à ta demande"}
        ))


    def test_scoped_urgent_news_allowed_only_to_marked_market_channel(self):
        ab.TELEGRAM_PULL_CONTEXT.chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.private = False
        ab.TELEGRAM_PULL_CONTEXT.news_chat_id = "-100123"
        ab.DERNIER_ETAT = {"canaux_marche": {"BTC": "-100123", "GOLD": "-100456"}}
        news = "🚨 NEWS DE DERNIÈRE MINUTE\n📰 Headline\nDYOR"
        self.assertTrue(ab._telegram_sortant_autorise("sendMessage", {"chat_id": "-100123", "text": news}))
        self.assertFalse(ab._telegram_sortant_autorise("sendMessage", {"chat_id": "-100456", "text": news}))
        self.assertFalse(ab._telegram_sortant_autorise("sendMessage", {"chat_id": "-100123", "text": "Statut du marché"}))
        self.assertFalse(ab._telegram_sortant_autorise("editMessageText", {"chat_id": "-100123", "text": news}))
        ab.TELEGRAM_PULL_CONTEXT.news_chat_id = None
        self.assertFalse(ab._telegram_sortant_autorise("sendMessage", {"chat_id": "-100123", "text": news}))


    def test_news_urgentes_transmet_uniquement_au_canal_selectionne_et_restaure_contexte(self):
        import json
        ab.TELEGRAM_PULL_CONTEXT.news_chat_id = "contexte-preexistant"
        etat = {"news_urg_t": 0, "canaux_marche": {"BTC": "-100123", "GOLD": "-100456"}}
        decision = json.dumps({"decision": "ALERTE", "idx": 0, "markets": ["BTC"], "impact": "HIGH", "direction": "BEARISH"})
        appels = []
        def telegram_simule(methode, **params):
            autorise = ab._telegram_sortant_autorise(methode, params)
            appels.append((methode, params.get("chat_id"), params.get("text", ""),
                           getattr(ab.TELEGRAM_PULL_CONTEXT, "news_chat_id", None), autorise))
            return {"ok": autorise}
        with mock.patch.object(ab, "TOKEN", "token-test"), \
             mock.patch.object(ab, "DERNIER_ETAT", etat), \
             mock.patch.object(ab, "titres_urgents", return_value=["Fed rate decision affects Bitcoin"]), \
             mock.patch.object(ab, "ia", return_value=decision), \
             mock.patch.object(ab, "telegram", side_effect=telegram_simule), \
             mock.patch.object(ab, "live_publier", return_value=True):
            resultat = ab.news_urgentes(etat, maintenant=1000, lire=lambda _url: "<rss/>")
        self.assertTrue(resultat.startswith("🚨 NEWS DE DERNIÈRE MINUTE"))
        self.assertEqual(len(appels), 1)
        methode, canal, texte, contexte, autorise = appels[0]
        self.assertEqual((methode, canal, contexte), ("sendMessage", "-100123", "-100123"))
        self.assertTrue(texte.startswith("🚨 NEWS DE DERNIÈRE MINUTE"))
        self.assertTrue(autorise)
        self.assertEqual(ab.TELEGRAM_PULL_CONTEXT.news_chat_id, "contexte-preexistant")

    def test_unsolicited_status_message_remains_blocked(self):
        ab.TELEGRAM_PULL_CONTEXT.chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.private = False
        self.assertFalse(ab._telegram_sortant_autorise(
            "sendMessage", {"chat_id": "42", "text": "Statut du marché"}
        ))


    def test_confirmed_entry_reaches_explicit_market_alert_subscriber(self):
        ab.TELEGRAM_PULL_CONTEXT.chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.private = False
        state = {
            "auto": {"BTC": ["42"], "GOLD": []},
            "marches_par_chat": {"42": ["BTC"]},
            "quiet": [],
            "bot_off": [],
        }
        entry_btc = "🟢 BTC - LONG\n📍 Entrée 65000\n🛑 SL 64000\n🎯 TP1 67000"
        entry_gold = "🟢 GOLD - LONG\n📍 Entrée 4000\n🛑 SL 3980\n🎯 TP1 4040"
        with mock.patch.object(ab, "DERNIER_ETAT", state):
            self.assertTrue(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": "42", "text": entry_btc}
            ))
            self.assertFalse(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": "42", "text": entry_gold}
            ))
            self.assertFalse(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": "43", "text": entry_btc}
            ))
            self.assertFalse(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": "42", "text": "📊 BTC : attente de confirmation"}
            ))
            state["quiet"] = ["42"]
            self.assertFalse(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": "42", "text": entry_btc}
            ))
            state["quiet"] = []
            state["bot_off"] = ["42"]
            self.assertFalse(ab._telegram_sortant_autorise(
                "sendMessage", {"chat_id": "42", "text": entry_btc}
            ))

    def test_validated_entry_only_reaches_requested_user_and_configured_market_channel(self):
        ab.TELEGRAM_PULL_CONTEXT.chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.private = False
        state = {
            "recherche_positions_active": ["42"],
            "canaux_marche": {"BTC": "-100123"},
        }
        entry = "J'ENTRE MAINTENANT — BTC"
        with mock.patch.object(ab, "DERNIER_ETAT", state):
            self.assertTrue(ab._telegram_sortant_autorise("sendMessage", {"chat_id": "42", "text": entry}))
            self.assertTrue(ab._telegram_sortant_autorise("sendMessage", {"chat_id": "-100123", "text": entry}))
            self.assertFalse(ab._telegram_sortant_autorise("sendMessage", {"chat_id": "43", "text": entry}))
            self.assertFalse(ab._telegram_sortant_autorise("sendMessage", {"chat_id": "-100999", "text": entry}))
            self.assertFalse(ab._telegram_sortant_autorise("sendMessage", {"chat_id": "-100123", "text": "Point de marché BTC"}))


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


class TelegramOutboxScopedRetry(unittest.TestCase):
    def setUp(self):
        self.old_mode = ab.TELEGRAM_PULL_MODE
        self.old_token = ab.TOKEN
        self.old_state = ab.DERNIER_ETAT
        self.old_news_chat = getattr(ab.TELEGRAM_PULL_CONTEXT, "news_chat_id", None)
        self.old_current_state = ab._ETAT_COURANT.get("etat")
        self.old_current_chats = ab._ETAT_COURANT.get("chats")
        self.old_retry = dict(ab.TELEGRAM_RETRY_UNTIL)
        ab.TELEGRAM_PULL_MODE = True
        ab.TOKEN = "test-token"
        ab.TELEGRAM_RETRY_UNTIL.clear()
        ab.TELEGRAM_PULL_CONTEXT.chat_id = None
        ab.TELEGRAM_PULL_CONTEXT.private = False
        ab.TELEGRAM_PULL_CONTEXT.news_chat_id = None
        self.state = {"canaux_marche": {"BTC": "-100123"}, "telegram_outbox": []}
        ab.DERNIER_ETAT = self.state
        ab._ETAT_COURANT["etat"] = self.state
        ab._ETAT_COURANT["chats"] = set()

    def tearDown(self):
        ab.TELEGRAM_PULL_MODE = self.old_mode
        ab.TOKEN = self.old_token
        ab.DERNIER_ETAT = self.old_state
        ab.TELEGRAM_PULL_CONTEXT.news_chat_id = self.old_news_chat
        ab.TELEGRAM_RETRY_UNTIL.clear()
        ab.TELEGRAM_RETRY_UNTIL.update(self.old_retry)
        if self.old_current_state is None:
            ab._ETAT_COURANT.pop("etat", None)
        else:
            ab._ETAT_COURANT["etat"] = self.old_current_state
        if self.old_current_chats is None:
            ab._ETAT_COURANT.pop("chats", None)
        else:
            ab._ETAT_COURANT["chats"] = self.old_current_chats

    def _queue_news_after_429(self):
        ab.TELEGRAM_PULL_CONTEXT.news_chat_id = "-100123"
        with mock.patch.object(ab, "http_json", side_effect=RuntimeError("HTTP Error 429: retry after 30")):
            ab._envoi_sur("-100123", text="🚨 NEWS DE DERNIÈRE MINUTE\n📰 Test news")
        self.assertEqual(len(self.state["telegram_outbox"]), 1)
        self.assertTrue(self.state["telegram_outbox"][0].get("news_urgente"))
        ab.TELEGRAM_PULL_CONTEXT.news_chat_id = None
        ab.TELEGRAM_RETRY_UNTIL.clear()
        self.state["telegram_outbox"][0]["next_t"] = 0

    def test_429_retry_preserves_configured_urgent_news_channel_scope(self):
        self._queue_news_after_429()
        sent = []

        def fake_http(url, data=None, **kwargs):
            sent.append((url, urllib.parse.parse_qs(data.decode("utf-8"))))
            return {"ok": True, "result": {"message_id": 56, "chat": {"id": -100123}}}

        with mock.patch.object(ab, "http_json", side_effect=fake_http):
            delivered = ab.traiter_file_telegram(self.state, maintenant=time.time() + 60)

        self.assertEqual(delivered, 1)
        self.assertEqual(len(sent), 1)
        self.assertTrue(sent[0][0].endswith("/sendMessage"))
        self.assertEqual(sent[0][1]["chat_id"], ["-100123"])
        self.assertEqual(self.state["telegram_outbox"], [])
        self.assertIsNone(ab.TELEGRAM_PULL_CONTEXT.news_chat_id)

    def test_429_retry_does_not_send_to_news_channel_removed_before_retry(self):
        self._queue_news_after_429()
        self.state["canaux_marche"].clear()
        sent = []

        def fake_http(url, data=None, **kwargs):
            sent.append(url)
            return {"ok": True, "result": {"message_id": 57}}

        with mock.patch.object(ab, "http_json", side_effect=fake_http):
            delivered = ab.traiter_file_telegram(self.state, maintenant=time.time() + 60)

        self.assertEqual(delivered, 0)
        self.assertEqual(sent, [])
        self.assertEqual(self.state["telegram_outbox"], [])


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


class PlanArrondi(unittest.TestCase):
    """Cas réel du 18/11 : bord de zone 63803,65 (arrondi JSON) contre 63803,6475 attendu."""
    def plan(self, signal, entry, sl, low, high):
        robot = {"signal": signal, "entry": entry, "sl": sl, "tp1": entry + (3 if signal == "LONG" else -3) * abs(entry - sl),
                 "planTimeframe": "M15", "entryTimeframe": "M5", "strategy": "DAY",
                 "entryZoneLow": low, "entryZoneHigh": high, "entryDecision": (low + high) / 2,
                 "entryBarTime": 900_000, "entryBarOpen": low, "entryBarHigh": high, "entryBarLow": low,
                 "entryBarClose": (low + high) / 2, "confirmed": True}
        r = {"tv_indicator_mtf": {"available": True, "activeTimeframe": "M5",
                                  "snapshots": {"M5": {"fresh": True, "price": entry, "confirmed": True, "robotV12": robot}}}}
        return ab.plan_indicateur(r)

    def test_bord_de_zone_arrondi_accepte_comme_par_le_bridge(self):
        # LONG : SL 63700, entrée 64114,59 → bord exact 63803,6475, envoyé arrondi 63803,64 (sous la limite)
        p = self.plan("LONG", 64114.59, 63700.0, 63803.64, 64200.0)
        self.assertTrue(p["available"], p.get("reason"))

    def test_bord_vraiment_trop_pres_du_stop_reste_refuse(self):
        p = self.plan("LONG", 64114.59, 63700.0, 63780.0, 64200.0)
        self.assertFalse(p["available"])
        self.assertIn("géométrie", p["reason"])


class RetoursALaLigne(unittest.TestCase):
    def test_aucun_antislash_n_litteral_dans_le_code_des_messages(self):
        import io, tokenize
        src = Path(ab.__file__).read_text(encoding="utf-8")
        mauvais = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.STRING or tok.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
                if "\\\\n" in tok.string and not tok.string.lstrip("bfuBFU").startswith(("r'", 'r"', "R'", 'R"')):
                    mauvais.append(tok.start[0])
        self.assertEqual(mauvais, [], f"« \\\\n » affiché tel quel aux lignes {mauvais}")


if __name__ == "__main__":
    unittest.main()
