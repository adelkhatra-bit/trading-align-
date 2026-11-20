"""Tests garantissant l'absence de fusion automatique ALIGN et la politique manuelle."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
AUTO_MERGE = WORKFLOWS / "align-auto-merge.yml"
AGENTS = ROOT / "AGENTS.md"
SOURCE_OF_TRUTH = ROOT / "docs" / "ALIGN_SOURCE_DE_VERITE.md"

FORBIDDEN_MERGE_PATTERNS = (
    r"\\bgh\\s+pr\\s+merge\\b",
    r"/pulls/[^\\s\\"']+/merge\\b",
    r"\\benable_auto_merge\\b",
    r"enable-pull-request-automerge",
    r"\\b(?:octokit|github)\\.rest\\.pulls\\.merge\\b",
)


class PorteFusion(unittest.TestCase):
    def test_workflow_de_fusion_automatique_absent(self):
        self.assertFalse(AUTO_MERGE.exists(), "Le workflow de merge automatique doit être supprimé.")

    def test_aucun_workflow_ne_declenche_de_fusion_de_pr(self):
        workflows = list(WORKFLOWS.glob("*.yml")) + list(WORKFLOWS.glob("*.yaml"))
        for workflow in workflows:
            contenu = workflow.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_MERGE_PATTERNS:
                self.assertIsNone(
                    re.search(pattern, contenu, flags=re.IGNORECASE),
                    f"Mécanisme de fusion automatique détecté dans {workflow.name}: {pattern}",
                )

    def test_regles_agents_exigent_une_approbation_manuelle(self):
        agents = AGENTS.read_text(encoding="utf-8")
        self.assertIn("obtain explicit user approval", agents)
        self.assertIn("All merges require explicit owner approval", agents)
        self.assertNotIn("Owner-approved exception", agents)

    def test_source_de_verite_interdit_la_fusion_automatique(self):
        source = SOURCE_OF_TRUTH.read_text(encoding="utf-8")
        self.assertIn("Fusion manuelle uniquement", source)
        self.assertNotIn("Fusion automatique : prévue", source)

    def test_source_de_verite_ne_publie_pas_les_statuts_des_secrets(self):
        source = SOURCE_OF_TRUTH.read_text(encoding="utf-8")
        self.assertNotIn("État au 18/11/2026", source)
        self.assertNotIn("**absents**", source)


if __name__ == "__main__":
    unittest.main()
