"""Tests offline des logs du poller Telegram ALIGN."""
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import align_bot as ab


class TelegramObservabiliteLogs(unittest.TestCase):
    def capture(self, fn, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            result = fn(*args)
        return out.getvalue().strip(), result

    def test_nonempty_batch_logs_counts(self):
        updates = [{"message": {}}, {"callback_query": {"data": "next:yes"}},
                   {"callback_query": {"data": "son:piece"}}]
        output, result = self.capture(ab._log_telegram_batch, updates, 1, 100, 101)
        self.assertEqual(output, "TELEGRAM_GETUPDATES_BATCH updates=3 callbacks=2")
        self.assertEqual(result, (0, 100))
        out_empty, state_empty = self.capture(ab._log_telegram_batch, [], result[0], result[1], 400)
        self.assertEqual(out_empty, "TELEGRAM_GETUPDATES_EMPTY_SUMMARY empty_batches=1 interval_seconds=300")
        self.assertEqual(state_empty, (0, 400))

    def test_empty_batches_are_silent_until_five_minutes_then_summarized(self):
        out1, state1 = self.capture(ab._log_telegram_batch, [], 0, 100, 399)
        self.assertEqual(out1, "")
        self.assertEqual(state1, (1, 100))
        out2, state2 = self.capture(ab._log_telegram_batch, [], state1[0], state1[1], 400)
        self.assertEqual(out2, "TELEGRAM_GETUPDATES_EMPTY_SUMMARY empty_batches=2 interval_seconds=300")
        self.assertEqual(state2, (0, 400))
        out3, state3 = self.capture(ab._log_telegram_batch, [], state2[0], state2[1], 699)
        self.assertEqual(out3, "")
        self.assertEqual(state3, (1, 400))
        out4, state4 = self.capture(ab._log_telegram_batch, [], state3[0], state3[1], 700)
        self.assertEqual(out4, "TELEGRAM_GETUPDATES_EMPTY_SUMMARY empty_batches=2 interval_seconds=300")
        self.assertEqual(state4, (0, 700))

    def test_callback_ack_logs_data_and_actual_ok_result(self):
        cb = {"id": "cb-17", "data": "marketsmenu:BTC" + chr(10) + "more"}
        out = io.StringIO()
        with patch.object(ab, "telegram", return_value={"ok": True}) as mocked_telegram, redirect_stdout(out):
            ab._ack_callback_rapide(cb, "ack")
        self.assertIn("TELEGRAM_CALLBACK_ACK callback_id=cb-17 data='marketsmenu:BTC more' result=ok", out.getvalue())
        self.assertIn("answerCallbackQuery", str(mocked_telegram.call_args))
        self.assertIn("cb-17", ab.CALLBACKS_ACKNOWLEDGED)

    def test_callback_ack_logs_failed_result_when_telegram_returns_not_ok(self):
        cb = {"id": "cb-19", "data": "next:no"}
        out = io.StringIO()
        with patch.object(ab, "telegram", return_value={"ok": False, "description": "bad query"}), redirect_stdout(out):
            ab._ack_callback_rapide(cb, "ack")
        self.assertIn("TELEGRAM_CALLBACK_ACK callback_id=cb-19 data='next:no' result=failed", out.getvalue())

    def test_callback_ack_logs_failed_result_when_request_raises(self):
        cb = {"id": "cb-18", "data": "next:yes"}
        out = io.StringIO()
        with patch.object(ab, "telegram", side_effect=RuntimeError("timeout")), redirect_stdout(out):
            ab._ack_callback_rapide(cb, "ack")
        self.assertIn("TELEGRAM_CALLBACK_ACK callback_id=cb-18 data='next:yes' result=failed", out.getvalue())
        self.assertIn("callback ack timeout", out.getvalue())


class TelegramPollerLifecycle(unittest.TestCase):
    def run_tracee(self):
        out = io.StringIO()
        with redirect_stdout(out):
            ab.boucle_polling_telegram_tracee({}, {})
        return out.getvalue().strip().splitlines()

    def test_started_then_normal_stop(self):
        ab.TELEGRAM_POLL_STOP.clear()
        with patch.object(ab, "boucle_polling_telegram", return_value=None):
            lignes = self.run_tracee()
        self.assertEqual(lignes, ["TELEGRAM_POLLER_STARTED", "TELEGRAM_POLLER_STOPPED reason=normal"])

    def test_stop_requested_reason(self):
        ab.TELEGRAM_POLL_STOP.set()
        try:
            with patch.object(ab, "boucle_polling_telegram", return_value=None):
                lignes = self.run_tracee()
        finally:
            ab.TELEGRAM_POLL_STOP.clear()
        self.assertEqual(lignes[-1], "TELEGRAM_POLLER_STOPPED reason=stop_requested")

    def test_exception_logged_then_reraised(self):
        ab.TELEGRAM_POLL_STOP.clear()
        out = io.StringIO()
        with patch.object(ab, "boucle_polling_telegram", side_effect=RuntimeError("boom")):
            with redirect_stdout(out):
                with self.assertRaises(RuntimeError):
                    ab.boucle_polling_telegram_tracee({}, {})
        self.assertIn("TELEGRAM_POLLER_STOPPED reason=exception", out.getvalue())


if __name__ == "__main__":
    unittest.main()
