"""Garde-fous de la porte de fusion automatique ALIGN (align-auto-merge.yml)."""
import re
import unittest
from pathlib import Path

WF = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "align-auto-merge.yml").read_text(encoding="utf-8")
BOUCLE = WF.split("for N in $PRS; do", 1)[1]


class PorteFusion(unittest.TestCase):
    def test_reagit_a_la_fin_des_deux_validations(self):
        self.assertIn('workflows: ["ALIGN MTF validation", "CI Integration Tests"]', WF)

    def test_liste_des_pr_paginee(self):
        self.assertRegex(WF, r'gh api --paginate "repos/\$REPO/pulls\?state=open&base=main')

    def test_une_seule_fusion_par_execution(self):
        apres_fusion = BOUCLE.split("fusionnée (SHA", 1)[1].split("else", 1)[0]
        self.assertIn("break", apres_fusion)

    def test_fusion_epinglee_au_sha_et_conditions_strictes(self):
        self.assertIn('-f merge_method=squash -f sha="$SHA"', WF)
        self.assertIn('[ "$OK_CHECKS" = "true" ] && [ "$OK_CODEX" = "yes" ] && [ "$STATE" = "clean" ]', WF)
        self.assertIn('.code_review.commit_sha == $s and .code_review.status == "completed" and .code_review.has_unresolved_findings == false', WF)
        self.assertIn('[ "$FRESH" != "main false $SHA" ]', WF)

    def test_jamais_de_contournement(self):
        for interdit in ("--admin", "bypass", "force", "--auto"):
            self.assertNotRegex(WF, re.escape(interdit) + r"\b" if interdit != "force" else r"--force")


if __name__ == "__main__":
    unittest.main()
