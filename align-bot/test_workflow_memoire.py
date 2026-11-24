"""La mémoire du bot (state.json) ne doit plus se perdre à chaque déploiement : attente de l'ancien worker, sauvegarde à clé unique."""
import pathlib
import unittest

WF = pathlib.Path(__file__).resolve().parent.parent / ".github" / "workflows" / "align-bot.yml"


class MemoireDuBot(unittest.TestCase):
    def setUp(self):
        self.t = WF.read_text(encoding="utf-8")

    def test_sauvegarde_a_cles_uniques_jamais_la_cle_fixe(self):
        start = self.t.index("Clé unique de sauvegarde de la mémoire")
        end = self.t.index("Sanitiser le journal du relais TradingView", start)
        save = self.t[start:end]
        self.assertNotIn("key: align-etat-${{ github.run_id }}\n", save)                 # clé fixe refusée à l'arrêt (cache immuable)
        self.assertIn("steps.cle_sauvegarde.outputs.a", save)
        self.assertIn("steps.cle_sauvegarde.outputs.b", save)                           # deuxième exemplaire
        self.assertEqual(save.count("actions/cache/save@v4"), 2)
        self.assertEqual(save.count("if: always()"), 3)                                 # clé + 2 sauvegardes, même sur annulation

    def test_relay_log_is_not_uploaded_as_a_post_job_artifact(self):
        # Keep diagnostics in the job output; avoid artifact finalization after GitHub
        # marks the job completed (403 "job is completed").
        self.assertNotIn("Archiver le journal du relais TradingView", self.t)
        self.assertNotIn("align-tv-relay-log-", self.t)
        self.assertIn("Sanitiser le journal du relais TradingView", self.t)

    def test_restauration_par_prefixe_et_attente_de_l_ancien_worker_avant(self):
        self.assertIn("restore-keys: align-etat-", self.t)                              # les nouvelles clés commencent par ce préfixe
        self.assertLess(self.t.index("Attendre la fin de l'ancien worker"), self.t.index("Récupérer la mémoire du robot"))

    def test_attente_bornee_et_fail_closed(self):
        bloc = self.t[self.t.index("Attendre la fin de l'ancien worker"):self.t.index("Récupérer la mémoire du robot")]
        # L'incertitude sur l'ancien worker ne doit jamais autoriser une mémoire potentiellement périmée.
        self.assertNotIn("continue-on-error: true", bloc)
        self.assertIn("< 900", bloc)                                                    # attente plafonnée à 4 minutes
        self.assertIn('x["id"] < me', bloc)                                           # n'attend que les workers plus anciens
        self.assertIn("except Exception as ex:", bloc)
        self.assertIn("raise SystemExit", bloc)                                      # erreur API = arrêt
        self.assertIn("time.time() - debut < 900", bloc)
        self.assertIn("délai de 900 s atteint", bloc)                                # expiration = arrêt

    def test_worker_checkout_exactement_le_commit_valide(self):
        checkout = self.t[self.t.index("uses: actions/checkout@v4"):self.t.index("name: Attendre la fin de l'ancien worker")]
        self.assertIn("ref: ${{ github.event.workflow_run.head_sha || github.sha }}", checkout)
        self.assertIn("WORKER_CHECKOUT_SHA=$ACTUAL_SHA", checkout)
        self.assertIn("EXPECTED_SHA", checkout)

    def test_worker_actif_jamais_annule_avant_sauvegarde(self):
        bloc = self.t[self.t.index("concurrency:"):self.t.index("jobs:")]
        self.assertIn("group: align-bot", bloc)
        self.assertIn("cancel-in-progress: false", bloc)
        self.assertNotIn("cancel-in-progress: true", bloc)

    def test_permissions_minimales(self):
        entete = self.t[self.t.index("permissions:"):self.t.index("concurrency:")]
        self.assertIn("actions: read", entete)
        self.assertIn("contents: write", entete)                                         # uniquement la branche live-data (test_live_securite)
        self.assertNotIn("actions: write", entete)


if __name__ == "__main__":
    unittest.main()
