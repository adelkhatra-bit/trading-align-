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
        delay, status, retry_after = align_bot._live_outbox_retry_policy(
            self.http_error(429, 45), 1
        )
        self.assertEqual((delay, status, retry_after), (45, 429, 45))

    def test_permanent_403_is_not_retried(self):
        delay, status, retry_after = align_bot._live_outbox_retry_policy(
            self.http_error(403), 1
        )
        self.assertIsNone(delay)
        self.assertEqual(status, 403)
        self.assertIsNone(retry_after)

    def test_transient_503_uses_bounded_exponential_backoff(self):
        delay, status, retry_after = align_bot._live_outbox_retry_policy(
            self.http_error(503), 1
        )
        self.assertEqual((delay, status, retry_after), (10, 503, None))

    def test_network_error_uses_bounded_exponential_backoff(self):
        delay, status, retry_after = align_bot._live_outbox_retry_policy(
            URLError("timeout"), 2
        )
        self.assertEqual((delay, status, retry_after), (20, None, None))

    def test_retry_after_is_capped_at_one_day(self):
        delay, status, retry_after = align_bot._live_outbox_retry_policy(
            self.http_error(429, 200000), 1
        )
        self.assertEqual((delay, status, retry_after), (86400, 429, 200000))


if __name__ == "__main__":
    unittest.main()
