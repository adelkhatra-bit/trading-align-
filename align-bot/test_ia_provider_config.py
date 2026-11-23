"""Regression checks for configured external AI provider model identifiers."""
import unittest

import align_bot as ab


class AIProviderModelConfig(unittest.TestCase):
    def test_ovh_mistral_uses_current_published_model_id(self):
        provider = next((p for p in ab.IA_FOURNISSEURS if p[0] == "OVH Mistral"), None)
        self.assertIsNotNone(provider)
        self.assertEqual(provider[2], "Mistral-Small-3.2-24B-Instruct-2506")


    def test_global_daily_cap_still_tries_free_provider_and_skips_paid_providers(self):
        from datetime import datetime
        from unittest.mock import patch
        jour = datetime.datetime.now(ab.PARIS).strftime("%Y-%m-%d")
        etat = {"ia_jour": {jour: ab.IA_MAX_JOUR}, "ia_cache": {}}
        free_provider = ("OVH Llama", "https://free.example/v1/chat/completions", "llama-free", "", False)
        paid_openai = ("OpenAI", "https://api.openai.com/v1/chat/completions", "paid-model", "key", True)
        paid_anthropic = ("Anthropic", "https://api.anthropic.com/v1/messages", "claude", "key", True)
        with patch.object(ab, "IA_FOURNISSEURS", [free_provider, paid_openai, paid_anthropic]), \\
             patch.object(ab, "_appel_ia", return_value="Analyse gratuite de test valide." ) as call, \\
             patch.dict("os.environ", {"ALIGN_AI_HEALTHY_PROVIDER": ""}):
            result = ab.ia(etat, "Analyse", {"symbol": "BTC"}, cle_cache=None)
        self.assertEqual(result, "Analyse gratuite de test valide.")
        self.assertEqual(call.call_count, 1)
        self.assertEqual(call.call_args.args[0], free_provider[1])
        self.assertEqual(etat["ia_dernier_fournisseur"], "OVH Llama")
        self.assertEqual(etat["ia_dernier_statut"], "CONNECTED")
        self.assertEqual(etat["ia_jour"][jour], ab.IA_MAX_JOUR + 1)


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
