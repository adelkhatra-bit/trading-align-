import datetime
import email.utils
import unittest
from email.message import Message
from urllib.error import HTTPError, URLError

import align_bot


class LiveOutboxRetryPolicyTests(unittest.TestCase):
    def http_error(self, status, retry_after=None):
        headers = Message()
        if retry_after is not None:
            headers["Retry-After"] = str(retry_after)
        return HTTPError("https://ntfy.sh/topic", status, "HTTP error", headers, None)

    def test_429_honors_retry_after_seconds(self):
        result = align_bot._live_outbox_retry_policy(self.http_error(429, 45), 1, 1000)
        self.assertEqual(result, (45, 429, 45))

    def test_429_honors_retry_after_http_date(self):
        retry_date = datetime.datetime.fromtimestamp(1060, datetime.timezone.utc)
        header = email.utils.format_datetime(retry_date, usegmt=True)
        result = align_bot._live_outbox_retry_policy(self.http_error(429, header), 1, 1000)
        self.assertEqual(result, (60, 429, 60))

    def test_permanent_403_is_not_retried(self):
        result = align_bot._live_outbox_retry_policy(self.http_error(403), 1, 1000)
        self.assertEqual(result, (None, 403, None))

    def test_transient_503_uses_bounded_exponential_backoff(self):
        result = align_bot._live_outbox_retry_policy(self.http_error(503), 1, 1000)
        self.assertEqual(result, (10, 503, None))

    def test_network_error_uses_bounded_exponential_backoff(self):
        result = align_bot._live_outbox_retry_policy(URLError("timeout"), 2, 1000)
        self.assertEqual(result, (20, None, None))

    def test_retry_after_is_capped_at_one_day(self):
        result = align_bot._live_outbox_retry_policy(self.http_error(429, 200000), 1, 1000)
        self.assertEqual(result, (86400, 429, 200000))

    def test_408_is_transient(self):
        result = align_bot._live_outbox_retry_policy(self.http_error(408), 1, 1000)
        self.assertEqual(result, (10, 408, None))


if __name__ == "__main__":
    unittest.main()
