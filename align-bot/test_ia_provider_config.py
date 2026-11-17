"""Regression checks for configured external AI provider model identifiers."""
import unittest

import align_bot as ab


class AIProviderModelConfig(unittest.TestCase):
    def test_ai_healthcheck_exports_the_provider_that_really_replied(self):
        from pathlib import Path
        source = (Path(__file__).parent / "ai_healthcheck.py").read_text(encoding="utf-8")
        self.assertIn('output = os.environ.get("GITHUB_OUTPUT")', source)
        self.assertIn(r"provider={provider or ''}\n", source)

    def test_ovh_mistral_uses_current_published_model_id(self):
        provider = next((p for p in ab.IA_FOURNISSEURS if p[0] == "OVH Mistral"), None)
        self.assertIsNotNone(provider)
        self.assertEqual(provider[2], "Mistral-Small-3.2-24B-Instruct-2506")


    def test_ai_provider_http_timeout_is_bounded(self):
        import json
        from unittest.mock import patch

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": "Réponse IA réelle de test."}}]}).encode()

        messages = [{"role": "user", "content": "test"}]
        with patch("align_bot.urllib.request.urlopen", return_value=FakeResponse()) as request:
            reply = ab._appel_ia(
                "https://api.groq.com/openai/v1/chat/completions",
                "model-test",
                "",
                messages,
            )
        self.assertIn("Réponse IA réelle", reply)
        self.assertEqual(request.call_args.kwargs["timeout"], 10)


if __name__ == "__main__":
    unittest.main()
