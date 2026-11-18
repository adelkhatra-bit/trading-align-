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


if __name__ == "__main__":
    unittest.main()
