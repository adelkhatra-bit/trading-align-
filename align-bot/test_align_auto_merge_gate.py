"""Tests garantissant la suppression de la fusion automatique ALIGN."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
AUTO_MERGE = WORKFLOWS / "align-auto-merge.yml"


class PorteFusion(unittest.TestCase):
    def test_workflow_de_fusion_automatique_absent(self):
        self.assertFalse(AUTO_MERGE.exists(), "Le workflow de merge automatique doit être supprimé.")

    def test_aucun_workflow_ne_declenche_de_fusion_de_pr(self):
        signatures_interdites = (
            "gh pr merge",
            "pulls/$N/merge",
            "enable_auto_merge",
        )
        for workflow in WORKFLOWS.glob("*.yml"):
            contenu = workflow.read_text(encoding="utf-8")
            for signature in signatures_interdites:
                self.assertNotIn(signature, contenu, f"Fusion automatique détectée dans {workflow.name}: {signature}")


if __name__ == "__main__":
    unittest.main()
