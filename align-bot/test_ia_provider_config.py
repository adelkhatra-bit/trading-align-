"""Regression checks for configured external AI provider model identifiers."""
import os
import unittest

import align_bot as ab


class AIProviderModelConfig(unittest.TestCase):
    def test_ai_healthcheck_exports_the_provider_that_really_replied(self):
        from pathlib import Path
        source = (Path(__file__).parent / "ai_healthcheck.py").read_text(encoding="utf-8")
        self.assertIn('output = os.environ.get("GITHUB_OUTPUT")', source)
        self.assertIn('f.write(f"provider={provider or \'\'}\\n")', source)

    def test_ovh_mistral_uses_current_published_model_id(self):
        provider = next((p for p in ab.IA_FOURNISSEURS if p[0] == "OVH Mistral"), None)
        self.assertIsNotNone(provider)
        self.assertEqual(provider[2], "Mistral-Small-3.2-24B-Instruct-2506")


if __name__ == "__main__":
    unittest.main()
