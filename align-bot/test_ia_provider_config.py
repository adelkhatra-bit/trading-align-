"""Regression checks for configured external AI provider model identifiers."""
import unittest
from pathlib import Path

import align_bot as ab


class AIProviderModelConfig(unittest.TestCase):
    def test_ovh_mistral_uses_current_published_model_id(self):
        provider = next((p for p in ab.IA_FOURNISSEURS if p[0] == "OVH Mistral"), None)
        self.assertIsNotNone(provider)
        self.assertEqual(provider[2], "Mistral-Small-3.2-24B-Instruct-2506")


    def test_global_daily_cap_still_tries_free_provider_and_skips_paid_providers(self):
        import datetime
        from unittest.mock import patch
        jour = datetime.datetime.now(ab.PARIS).strftime("%Y-%m-%d")
        etat = {"ia_jour": {jour: ab.IA_MAX_JOUR}, "ia_cache": {}}
        free_provider = ("OVH Llama", "https://free.example/v1/chat/completions", "llama-free", "", False)
        paid_openai = ("OpenAI", "https://api.openai.com/v1/chat/completions", "paid-model", "key", True)
        paid_anthropic = ("Anthropic", "https://api.anthropic.com/v1/messages", "claude", "key", True)
        with patch.object(ab, "IA_FOURNISSEURS", [free_provider, paid_openai, paid_anthropic]), \
             patch.object(ab, "_appel_ia", return_value="Analyse gratuite de test valide." ) as call, \
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

    def test_groq_uses_auto_service_tier_by_default(self):
        import json
        from unittest.mock import patch

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self):
                return json.dumps({"choices": [{"message": {"content": "Réponse IA Groq de test."}}]}).encode()

        with patch.dict("os.environ", {"GROQ_SERVICE_TIER": "auto"}), patch("align_bot.urllib.request.urlopen", return_value=FakeResponse()) as request:
            ab._appel_ia("https://api.groq.com/openai/v1/chat/completions", "model-test", "key",
                         [{"role": "user", "content": "test"}])
        payload = json.loads(request.call_args.args[0].data.decode())
        self.assertEqual(payload["service_tier"], "auto")

    def test_groq_service_tier_can_be_pinned_to_on_demand(self):
        import json
        from unittest.mock import patch

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self):
                return json.dumps({"choices": [{"message": {"content": "Réponse IA Groq de test."}}]}).encode()

        with patch.dict("os.environ", {"GROQ_SERVICE_TIER": "on_demand"}), patch("align_bot.urllib.request.urlopen", return_value=FakeResponse()) as request:
            ab._appel_ia("https://api.groq.com/openai/v1/chat/completions", "model-test", "key",
                         [{"role": "user", "content": "test"}])
        payload = json.loads(request.call_args.args[0].data.decode())
        self.assertEqual(payload["service_tier"], "on_demand")

    def test_groq_auto_retries_on_demand_only_when_tier_is_unsupported(self):
        import io
        import json
        import urllib.error
        from unittest.mock import patch

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self):
                return json.dumps({"choices": [{"message": {"content": "Réponse IA Groq de test."}}]}).encode()

        unsupported = urllib.error.HTTPError(
            "https://api.groq.com/openai/v1/chat/completions", 400, "Bad Request", {},
            io.BytesIO(b'{"error":{"message":"service_tier auto is not supported for this account"}}'),
        )
        with patch.dict("os.environ", {"GROQ_SERVICE_TIER": "auto"}), patch("align_bot.urllib.request.urlopen", side_effect=[unsupported, FakeResponse()]) as request:
            reply = ab._appel_ia("https://api.groq.com/openai/v1/chat/completions", "model-test", "key",
                                 [{"role": "user", "content": "test"}])
        self.assertIn("Réponse IA Groq", reply)
        self.assertEqual(request.call_count, 2)
        tiers = [json.loads(call_.args[0].data.decode())["service_tier"] for call_ in request.call_args_list]
        self.assertEqual(tiers, ["auto", "on_demand"])

    def test_non_groq_openai_compatible_provider_does_not_receive_groq_tier(self):
        import json
        from unittest.mock import patch

        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self):
                return json.dumps({"choices": [{"message": {"content": "Réponse OVH de test valide."}}]}).encode()

        with patch("align_bot.urllib.request.urlopen", return_value=FakeResponse()) as request:
            ab._appel_ia("https://oai.endpoints.kepler.ai.cloud.ovh.net/v1/chat/completions", "model-test", "",
                         [{"role": "user", "content": "test"}])
        payload = json.loads(request.call_args.args[0].data.decode())
        self.assertNotIn("service_tier", payload)


    def test_manual_ai_healthcheck_fails_when_no_external_provider_responds(self):
        workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ai-check.yml"
        content = workflow.read_text(encoding="utf-8")
        self.assertIn("run: python3 ai_healthcheck.py", content)
        self.assertNotIn("continue-on-error:", content)
        validation = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "align-bot-validation.yml"
        validation_content = validation.read_text(encoding="utf-8")
        self.assertIn(".github/workflows/ai-check.yml", validation_content)


if __name__ == "__main__":
    unittest.main()
