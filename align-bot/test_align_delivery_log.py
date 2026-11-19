"""Ensure the worker's generated-message metric never claims Telegram delivery."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parent / "align_bot.py").read_text(encoding="utf-8")


class DeliveryMetricLabelTests(unittest.TestCase):
    def test_log_reports_prepared_messages_not_delivered_signals(self):
        self.assertIn("message(s) préparé(s)", SOURCE)
        self.assertIn("livraisons non comptabilisées", SOURCE)
        self.assertNotIn("signal(s) envoyé(s) à", SOURCE)



if __name__ == "__main__":
    unittest.main()
