"""Tests offline des logs d'observabilite du lecteur Telegram."""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class TelegramObservabiliteLogs(unittest.TestCase):
    def capture(self, fn, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            fn(*args)
        return out.getvalue().strip()

    def test_getupdates_batch_logs_update_and_callback_counts(self):
        updates = [{"message": {}}, {"callback_query": {"data": "next:yes"}},
                   {"callback_query": {"data": "son:piece"}}]
        self.assertEqual(self.capture(ab._log_telegram_batch, updates),
                         "TELEGRAM_GETUPDATES_BATCH updates=3 callbacks=2")

    def test_callback_ack_logs_data_and_success_result(self):
        cb = {"id": "cb-17", "data": "marketsmenu:BTC" + chr(10) + "more"}
        self.assertEqual(self.capture(ab._log_callback_ack, cb, {"ok": True, "result": True}),
                         "TELEGRAM_CALLBACK_ACK callback_id=cb-17 data='marketsmenu:BTC more' result=ok")

    def test_callback_ack_logs_failed_result(self):
        cb = {"id": "cb-18", "data": "next:yes"}
        self.assertEqual(self.capture(ab._log_callback_ack, cb, {"ok": False, "description": "timeout"}),
                         "TELEGRAM_CALLBACK_ACK callback_id=cb-18 data='next:yes' result=failed")

    def test_rollover_log_identifies_newer_queued_run(self):
        runs = [{"id": 100, "status": "in_progress"},
                {"id": 101, "status": "queued"},
                {"id": 102, "status": "completed"}]
        line = self.capture(ab._log_releve_trigger, runs, 100)
        self.assertIn("newer_run_id=101", line)
        self.assertIn("status=queued", line)



if __name__ == "__main__":
    unittest.main()
