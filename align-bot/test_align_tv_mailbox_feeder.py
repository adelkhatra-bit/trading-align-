import unittest

import align_tv_bridge as bridge
import align_tv_mailbox_feeder as feeder
from test_align_tv_bridge import BASE_MS, valid_payload

INGEST = "i" * 40
READ = "r" * 40


class MailboxFeederTests(unittest.TestCase):
    """Le relais doit passer par le VRAI BridgeStore : aucune validation dupliquée."""

    def setUp(self):
        self.store = bridge.BridgeStore(INGEST, READ)

    def _ingest(self, payload):
        return self.store.ingest(payload, INGEST, now_ms=BASE_MS)

    def test_valid_mailbox_payload_reaches_bridge_and_is_readable(self):
        box = {"ok": True, "payload": valid_payload(BASE_MS, "BTCUSD")}
        res = feeder.relay_once(lambda s: box if s == "BTCUSD" else {"ok": False}, self._ingest)
        self.assertEqual(res["BTCUSD"], "ok")
        self.assertEqual(res["XAUUSD"], "empty")
        status, body = self.store.read("BTCUSD", now_ms=BASE_MS)
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

    def test_bridge_rejection_is_reported_not_hidden(self):
        stale = valid_payload(BASE_MS - 120_000, "BTCUSD")
        res = feeder.relay_once(lambda s: {"ok": True, "payload": stale}, self._ingest, symbols=("BTCUSD",))
        self.assertTrue(res["BTCUSD"].startswith("rejected:"))
        self.assertFalse(self.store.read("BTCUSD", now_ms=BASE_MS)[1]["ok"])

    def test_mailbox_network_error_never_fabricates_data(self):
        def boom(_):
            raise OSError("down")
        res = feeder.relay_once(boom, self._ingest, symbols=("NAS100",))
        self.assertEqual(res["NAS100"], "mailbox_error:OSError")
        self.assertFalse(self.store.read("NAS100", now_ms=BASE_MS)[1]["ok"])

    def test_mailbox_auth_failure_is_reported_not_called_empty(self):
        res = feeder.relay_once(lambda s: {"ok": False, "error": "unauthorized", "_http_status": 401},
                                self._ingest, symbols=("BTCUSD",))
        self.assertEqual(res["BTCUSD"], "mailbox_http_401")

    def test_local_bridge_down_does_not_stop_the_loop(self):
        box = {"ok": True, "payload": valid_payload(BASE_MS, "BTCUSD"), "_http_status": 200}

        def down(_payload):
            raise ConnectionRefusedError("bridge local arrêté")
        res = feeder.relay_once(lambda s: box, down, symbols=("BTCUSD", "XAUUSD"))
        self.assertEqual(res["BTCUSD"], "ingest_error:ConnectionRefusedError")
        self.assertEqual(res["XAUUSD"], "ingest_error:ConnectionRefusedError")

    def test_one_shot_failure_is_detected_but_empty_is_not(self):
        self.assertFalse(feeder.relay_failed({"BTCUSD": "ok", "XAUUSD": "empty"}))
        self.assertTrue(feeder.relay_failed({"BTCUSD": "ok", "NAS100": "mailbox_http_401"}))
        self.assertTrue(feeder.relay_failed({"BTCUSD": "ingest_error:URLError"}))
        self.assertTrue(feeder.relay_failed({"BTCUSD": "rejected:stale_or_future_snapshot"}))


if __name__ == "__main__":
    unittest.main()


class JetonLectureDerive(unittest.TestCase):
    def test_secret_direct_prioritaire(self):
        import align_tv_mailbox_feeder as f
        self.assertEqual(f.jeton_lecture({"ALIGN_TV_MAILBOX_TOKEN": "abc", "CLOUDFLARE_API_TOKEN": "x"}), "abc")

    def test_derive_du_jeton_cloudflare_stable_et_long(self):
        import align_tv_mailbox_feeder as f
        a = f.jeton_lecture({"CLOUDFLARE_API_TOKEN": "racine-test"})
        self.assertEqual(a, f.jeton_lecture({"CLOUDFLARE_API_TOKEN": "racine-test"}))
        self.assertEqual(len(a), 64)                       # ≥ 32 caractères exigés par le Worker
        self.assertNotIn("racine-test", a)
        self.assertNotEqual(a, f.jeton_lecture({"CLOUDFLARE_API_TOKEN": "autre"}))

    def test_rien_sans_secret(self):
        import align_tv_mailbox_feeder as f
        self.assertEqual(f.jeton_lecture({}), "")


class AgentUtilisateur(unittest.TestCase):
    def test_agent_identifie_jamais_python_urllib(self):
        import align_tv_mailbox_feeder as f
        self.assertTrue(f.USER_AGENT.startswith("ALIGN-relais/"))
        self.assertNotIn("Python-urllib", f.USER_AGENT)
