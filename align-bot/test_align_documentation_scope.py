"""Keep canonical ALIGN scope and post-cleanup architecture unambiguous."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AlignDocumentationScopeTests(unittest.TestCase):
    def test_source_of_truth_marks_legacy_platform_as_removed_from_main(self):
        source = (ROOT / "docs" / "ALIGN_SOURCE_DE_VERITE.md").read_text(encoding="utf-8")
        self.assertIn("retrait effectué sur main", source.lower())
        self.assertIn("PR #960, fusionnée le 25/11/2026", source)
        self.assertNotIn("pas encore retirés de main tant que la PR n'est pas fusionnée", source)
        self.assertNotIn("retrait proposé, non encore appliqué à main", source)
        self.assertNotIn("Leur retrait de main n'est pas effectif", source)

    def test_system_map_does_not_describe_pr960_as_pending(self):
        source = (ROOT / "docs" / "ALIGN_SYSTEM_MAP.md").read_text(encoding="utf-8")
        self.assertIn("PR #960, fusionnée le 25/11/2026", source)
        self.assertNotIn("Ils restent présents sur main tant que cette PR n'est pas fusionnée", source)
        self.assertNotIn("Retrait proposé par PR #960", source)

    def test_code_agent_and_runtime_ai_are_separate_in_canonical_guidance(self):
        source = (ROOT / "docs" / "ALIGN_SOURCE_DE_VERITE.md").read_text(encoding="utf-8")
        self.assertIn("Séparation entre IA de marché et agents de code", source)
        self.assertIn("Aucun relais Copilot CLI/cloud-agent", source)
        self.assertIn("L'IA runtime du BOT sert uniquement aux commentaires de marché", source)


if __name__ == "__main__":
    unittest.main()
