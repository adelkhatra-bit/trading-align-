"""Regression tests for bounded market-data HTTP request budgets."""
import unittest
from unittest.mock import call, patch

import align_bot as ab


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b'{"ok": true}'


class MarketHttpBudgetTests(unittest.TestCase):
    def test_default_http_json_timeout_and_retries_remain_unchanged(self):
        with patch(
            "align_bot.urllib.request.urlopen",
            side_effect=[TimeoutError("first"), TimeoutError("second"), FakeResponse()],
        ) as request, patch("align_bot.time.sleep") as sleep:
            result = ab.http_json("https://example.invalid/data")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(request.call_count, 3)
        self.assertEqual([call.kwargs["timeout"] for call in request.call_args_list], [70, 70, 70])
        self.assertEqual(sleep.call_args_list, [call(2), call(4)])

    def test_single_attempt_short_timeout_does_not_retry(self):
        with patch(
            "align_bot.urllib.request.urlopen",
            side_effect=TimeoutError("market request timed out"),
        ) as request, patch("align_bot.time.sleep") as sleep:
            with self.assertRaises(TimeoutError):
                ab.http_json("https://example.invalid/market", timeout=12, attempts=1)

        self.assertEqual(request.call_count, 1)
        self.assertEqual(request.call_args.kwargs["timeout"], 12)
        sleep.assert_not_called()

    def test_kraken_ohlc_uses_short_market_request_budget(self):
        payload = {
            "error": [],
            "result": {
                "XBTUSD": [
                    [1700000000, "1.0", "1.2", "0.9", "1.1", "1.0", "100", "10"],
                    [1700000300, "1.1", "1.3", "1.0", "1.2", "1.1", "120", "12"],
                ],
                "last": 123,
            },
        }
        with patch("align_bot.http_json", return_value=payload) as request:
            rows = ab._kraken("XBTUSD", 5)

        self.assertEqual(request.call_args.args[0], "https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=5")
        self.assertEqual(request.call_args.kwargs, {"timeout": 12, "attempts": 1})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["c"], 1.1)


if __name__ == "__main__":
    unittest.main()
