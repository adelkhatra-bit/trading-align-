import io
import unittest
import urllib.error
from unittest import mock

import metaapi_check as mc


class MetaApiRetryTests(unittest.TestCase):
    def test_retry_504_then_success(self):
        err = urllib.error.HTTPError("https://api.test", 504, "Gateway Timeout", {}, io.BytesIO(b""))
        api = mock.Mock(side_effect=[err, {"balance": 123}])
        delays = []
        result = mc.api_read_retry(api, "GET", "acct/account-information", sleep=delays.append)
        self.assertEqual(result, {"balance": 123})
        self.assertEqual(api.call_count, 2)
        self.assertEqual(delays, [1])

    def test_retry_transient_network_error(self):
        api = mock.Mock(side_effect=[urllib.error.URLError("temporary"), "ok"])
        delays = []
        result = mc.api_read_retry(api, "GET", "acct/positions", sleep=delays.append)
        self.assertEqual(result, "ok")
        self.assertEqual(delays, [1])

    def test_non_transient_http_error_not_retried(self):
        err = urllib.error.HTTPError("https://api.test", 401, "Unauthorized", {}, io.BytesIO(b""))
        api = mock.Mock(side_effect=err)
        with self.assertRaises(urllib.error.HTTPError):
            mc.api_read_retry(api, "GET", "acct/account-information", sleep=lambda _: None)
        self.assertEqual(api.call_count, 1)

    def test_retries_exhausted_propagates_error(self):
        err = urllib.error.HTTPError("https://api.test", 504, "Gateway Timeout", {}, io.BytesIO(b""))
        api = mock.Mock(side_effect=[err, err, err])
        delays = []
        with self.assertRaises(urllib.error.HTTPError):
            mc.api_read_retry(api, "GET", "acct/account-information", sleep=delays.append)
        self.assertEqual(api.call_count, 3)
        self.assertEqual(delays, [1, 2])


if __name__ == "__main__":
    unittest.main()
