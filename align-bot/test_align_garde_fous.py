"""Garde-fous ALIGN exécutés par « validate » (contrôle obligatoire de main).

Une PR — humaine ou IA — qui supprime la surveillance, désactive un workflow
critique ou détourne le bridge échoue ici, donc GitHub refuse sa fusion.
Ne couvre QUE ce qui n'était pas déjà testé (ordres réels :
test_broker_execution_safety ; bridge obligatoire : test_align_tv_bot_gate /
test_live_securite ; titre v25 : test_pine_v25_display).
"""
import re
import unittest
from pathlib import Path

import align_tv_bridge as bridge

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows"

CRITIQUES = {
    "align-bot.yml": "ALIGN MTF BOT (signaux BTC + Gold + NASDAQ Telegram)",
    "align-bot-validation.yml": "ALIGN MTF validation",
    "align-workflow-watchdog.yml": "ALIGN Workflow Watchdog",
    "align-auto-repair.yml": "ALIGN Auto Repair Coordinator",
}


class GardeFousWorkflows(unittest.TestCase):
    def test_workflows_critiques_presents_avec_leur_nom(self):
        for fichier, nom in CRITIQUES.items():
            chemin = WF / fichier
            self.assertTrue(chemin.exists(), f"workflow critique supprimé : {fichier}")
            self.assertIn(f"name: {nom}", chemin.read_text(encoding="utf-8"), f"nom modifié : {fichier}")

    def test_declencheurs_critiques_conserves(self):
        attendus = {
            "align-auto-repair.yml": [r"(?m)^  workflow_run:", r"types:\s*\[completed\]"],
            "align-workflow-watchdog.yml": [r"(?m)^  schedule:"],
            "align-bot.yml": [r"(?m)^  workflow_run:", r'workflows:\s*\["ALIGN MTF validation"\]', r"(?m)^  schedule:"],
            "align-bot-validation.yml": [r"(?m)^  pull_request:", r"(?m)^  push:"],
        }
        for fichier, motifs in attendus.items():
            texte = (WF / fichier).read_text(encoding="utf-8")
            entete = texte.split("\njobs:", 1)[0]
            for motif in motifs:
                self.assertRegex(entete, motif, f"déclencheur critique retiré dans {fichier} : {motif}")

    def test_aucun_workflow_critique_desactive(self):
        for fichier in CRITIQUES:
            texte = (WF / fichier).read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"^\s*if:\s*(false|\$\{\{\s*false\s*\}\})\s*$", texte, re.M),
                              f"job désactivé par « if: false » dans {fichier}")

    def test_watchdog_reste_planifie(self):
        texte = (WF / "align-workflow-watchdog.yml").read_text(encoding="utf-8")
        self.assertRegex(texte, r"schedule:\s*\n\s*- cron:", "le watchdog n'est plus planifié")

    def test_validate_lance_toute_la_suite(self):
        texte = (WF / "align-bot-validation.yml").read_text(encoding="utf-8")
        self.assertRegex(texte, r"(?m)^  pull_request:", "validate ne se déclenche plus sur les PR")
        job = re.search(r"(?ms)^  validate:\n(.*?)(?=^  \S|\Z)", texte)
        self.assertIsNotNone(job, "le job « validate » (contrôle obligatoire) a disparu")
        corps = job.group(1)
        self.assertNotRegex(corps, r"(?m)^    if:", "le job validate est conditionné (risque d'être sauté sur les PR)")
        self.assertIn('-p "test_*.py"', corps, "le job validate ne lance plus toute la suite de tests")
        # L'étape qui lance la suite ne doit pas pouvoir être sautée (pas de « if: » sur cette étape).
        etapes = re.split(r"(?m)^      - ", corps)
        suite = [e for e in etapes if '-p "test_*.py"' in e]
        self.assertTrue(suite, "étape de la suite complète introuvable")
        for etape in suite:
            self.assertNotRegex(etape, r"(?m)^        if:", "l'étape de la suite complète est conditionnée (peut être sautée)")
            self.assertNotRegex(etape, r"(?m)^        continue-on-error:\s*true", "l'étape de la suite complète tolère l'échec")


class GardeFousBridge(unittest.TestCase):
    def test_source_et_marches_canoniques(self):
        self.assertEqual(bridge.SOURCE, "ALIGN_MTF_PRO_V25")
        self.assertEqual(bridge.ALLOWED_SYMBOLS, {"BTCUSD", "XAUUSD", "NAS100"})

    def test_port_dedie_et_ports_interdits(self):
        self.assertTrue({3000, 4000, 5001} <= bridge.FORBIDDEN_PORTS, "anciens ports réautorisés")
        import inspect
        ecoute = inspect.getsource(bridge.main)
        self.assertIn('os.environ.get("ALIGN_TV_BRIDGE_PORT", "4100")', ecoute,
                      "le port d'écoute réel du bridge (main) n'est plus 4100")

    def test_fraicheur_non_relachee(self):
        self.assertGreater(bridge.ACTIVE_MAX_AGE_MS, 0, "fenêtre de fraîcheur nulle : le bridge rejetterait tout")
        self.assertLessEqual(bridge.ACTIVE_MAX_AGE_MS, 30_000, "fraîcheur du prix relâchée")
        self.assertEqual(set(bridge.REQUIRED_TIMEFRAMES), {"M5", "M15", "H1", "H4", "D1", "W1"})


if __name__ == "__main__":
    unittest.main()
