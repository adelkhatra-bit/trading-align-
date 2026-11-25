import unittest

from ai_healthcheck import provider_order


class AiHealthcheckProviderOrderTests(unittest.TestCase):
    def test_configured_anthropic_is_checked_before_free_fallbacks(self):
        providers = [
            ("Gemini", "url", "model", "gemini-key", True),
            ("Groq", "url", "model", "groq-key", True),
            ("OVH Llama", "url", "model", "", False),
            ("Anthropic", "url", "model", "anthropic-key", True),
        ]
        ordered = provider_order(providers)
        self.assertEqual(ordered[0][0], "Anthropic")
        self.assertEqual([p[0] for p in ordered[1:]],
                         ["Gemini", "Groq", "OVH Llama"])

    def test_missing_anthropic_key_preserves_existing_provider_order(self):
        providers = [
            ("Gemini", "url", "model", "", True),
            ("Groq", "url", "model", "groq-key", True),
            ("Anthropic", "url", "model", "", True),
        ]
        self.assertEqual(provider_order(providers), providers)

    def test_provider_order_does_not_mutate_canonical_list(self):
        providers = [
            ("Groq", "url", "model", "groq-key", True),
            ("Anthropic", "url", "model", "anthropic-key", True),
        ]
        original = list(providers)
        provider_order(providers)
        self.assertEqual(providers, original)


if __name__ == "__main__":
    unittest.main()
