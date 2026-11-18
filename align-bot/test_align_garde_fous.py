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
        self.assertRegex(texte, r"(?m)^  validate:", "le job « validate » (contrôle obligatoire) a disparu")
        self.assertIn('-p "test_*.py"', texte, "validate ne lance plus toute la suite de tests")


class GardeFousBridge(unittest.TestCase):
    def test_source_et_marches_canoniques(self):
        self.assertEqual(bridge.SOURCE, "ALIGN_MTF_PRO_V25")
        self.assertEqual(bridge.ALLOWED_SYMBOLS, {"BTCUSD", "XAUUSD", "NAS100"})

    def test_port_dedie_et_ports_interdits(self):
        self.assertTrue({3000, 4000, 5001} <= bridge.FORBIDDEN_PORTS, "anciens ports réautorisés")
        src = (ROOT / "align-bot" / "align_tv_bridge.py").read_text(encoding="utf-8")
        self.assertIn('os.environ.get("ALIGN_TV_BRIDGE_PORT", "4100")', src, "port par défaut du bridge modifié")

    def test_fraicheur_non_relachee(self):
        self.assertLessEqual(bridge.ACTIVE_MAX_AGE_MS, 30_000, "fraîcheur du prix relâchée")
        self.assertEqual(set(bridge.REQUIRED_TIMEFRAMES), {"M5", "M15", "H1", "H4", "D1", "W1"})


if __name__ == "__main__":
    unittest.main()
