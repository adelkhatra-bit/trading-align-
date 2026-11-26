"""Regression tests for the integrated Thomas/Leïla live commentator duet."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
LIVE_JS = ROOT.parent / "docs" / "live" / "align-bande-live.user.js"
LIVE_PAGE = ROOT.parent / "docs" / "live" / "index.html"


class LiveDuetCommentators(unittest.TestCase):
    def setUp(self):
        self.js = LIVE_JS.read_text(encoding="utf-8")
        self.page = LIVE_PAGE.read_text(encoding="utf-8")

    def test_visible_chart_publishes_initial_voice_state_before_poll(self):
        publish = self.js.index("if (document.visibilityState === 'visible') publierEtatCoach(voixActive);")
        poll = self.js.index("  ecouterDialoguesCoach();")
        self.assertLess(publish, poll)

    def test_french_male_voice_map_accepts_supported_windows_david_voice(self):
        self.assertIn("t: { fr: /\\b(?:paul|henri|pierre|david)\\b/i", self.js)

    def test_runtime_state_is_initialized_before_first_coach_poll(self):
        vivant = self.js.index("let vivant = true;")
        first_use = self.js.index("if (!vivant || !item || !voixActive")
        first_poll = self.js.index("  ecouterDialoguesCoach();")
        self.assertLess(vivant, first_use)
        self.assertLess(vivant, first_poll)

    def test_two_hosts_are_present_and_dialogue_is_sent_to_the_voice_engine(self):
        self.assertIn('id="av-t"', self.page)
        self.assertIn('id="av-l"', self.page)
        self.assertIn('id="b-t"', self.page)
        self.assertIn('id="b-l"', self.page)
        self.assertIn("function publierDialogueCoachPair(speaker1, text1, speaker2, text2, market)", self.page)
        self.assertIn('type: "ALIGN_SHOW", action: "PAIR"', self.page)
        self.assertIn("var premier = dernierHoteCoach", self.page)
        self.assertIn("var texte1 = changement.textes[0], texte2 = changement.textes[1];", self.page)
        self.assertIn("publierDialogueCoachPair(premier, texte1, second, texte2, changement.market)", self.page)
        self.assertIn("if (nom !== \"BTC\" && nom !== \"GOLD\") continue;", self.page)
        self.assertIn("parler(premier, texte1)", self.page)
        self.assertIn("parler(second, texte2)", self.page)

    def test_tradingview_uses_explicit_male_and_female_voice_maps(self):
        self.assertIn("const VOIX_PAR_ROLE", self.js)
        self.assertIn("t: { fr:", self.js)
        self.assertIn("l: { fr:", self.js)
        self.assertIn("function choisirVoix(lang, speaker = 't')", self.js)
        self.assertIn("filtreRole.test(v.name)", self.js)
        self.assertIn("conseil financier", self.js)
        self.assertIn("const speaker = item.speaker === 'l' ? 'l' : 't';", self.js)
        self.assertIn("choisirVoix(anglais ? 'en' : 'fr', speaker)", self.js)

    def test_dialogue_audio_is_gated_by_the_existing_coach_voice_toggle(self):
        self.assertIn("if (!vivant || !item || !voixActive", self.js)
        self.assertIn("['ia', 'marche', 'coach'].includes(item.source)", self.js)
        self.assertIn("if (voixActive) jouerDialogueCoach(show)", self.js)
        self.assertIn("publierEtatCoach(true)", self.js)
        self.assertIn("publierEtatCoach(false)", self.js)
        self.assertIn("if (!anglais && item.source !== 'coach') {", self.js)

    def test_voice_events_move_the_matching_avatar_not_alternate_randomly(self):
        self.assertIn("type: 'ALIGN_VOICE', action, speaker:", self.js)
        self.assertIn("requeteWorkerShow('/show/voice?message='", self.js)
        self.assertIn("voice.speaker === 'l' ? 'l' : 't'", self.page)
        self.assertIn("voixHoteActif = speaker;", self.page)
        self.assertNotIn("voixHoteActif = voixHoteActif === 't' ? 'l' : 't';", self.page)

    def test_show_event_listener_is_closed_when_the_userscript_stops(self):
        self.assertIn("function ecouterDialoguesCoach()", self.js)
        self.assertIn("requeteWorkerShow('/show/state'", self.js)
        self.assertIn("coachPollTimer = setInterval(poll, 3000)", self.js)
        self.assertIn("arreterEcouteDialoguesCoach()", self.js)
        self.assertIn("WORKER_SHOW_URL + '/show/state'", self.page)
        self.assertNotIn("ntfy.sh", self.page)
        self.assertIn("document.visibilityState !== 'visible'", self.js)
        self.assertIn("ts <= dernierDialogueCoachTs", self.js)

    def test_show_page_reads_public_state_published_from_the_tradingview_bridge(self):
        self.assertIn("live-data/live.json", self.page)
        bot = (ROOT / "align_bot.py").read_text(encoding="utf-8")
        self.assertIn('if r.get("require_tv_bridge"):', bot)
        self.assertIn('bridge = r.get("tv_indicator_mtf") or {}', bot)
        self.assertIn("plan = plan_indicateur(r)", bot)
        self.assertIn('if not complet:', bot)
        self.assertIn('etat_l = "ferme" if statut == "ferme" else "perime"', bot)

    def test_voice_relay_is_separate_from_market_mailboxes_and_ntfy(self):
        worker = (ROOT.parent / "cloud" / "align-tv-mailbox" / "worker.js").read_text(encoding="utf-8")
        self.assertIn('idFromName("LIVE_SHOW")', worker)
        self.assertIn('url.pathname === "/show/publish"', worker)
        self.assertIn('url.pathname === "/show/state"', worker)
        self.assertIn('url.pathname === "/show/voice"', worker)
        self.assertIn('url.pathname === "/show/coach"', worker)
        self.assertNotIn("'-voix'", self.js)
        self.assertNotIn("ntfy.sh", self.page)

    def test_dialogue_pacing_waits_for_speech_completion_not_estimated_duration(self):
        self.assertIn("startAt: ts + 4000", self.page)
        self.assertIn("function parlerLive(item, forcer = false, apresLecture = null)", self.js)
        self.assertIn("utterance.onend = () => terminerLecture(true);", self.js)
        self.assertIn("if (continuer && typeof apresLecture === 'function') apresLecture();", self.js)
        self.assertIn("}, 500));", self.js)
        self.assertNotIn("pause + 500", self.js)
        self.assertIn("setInterval(echange, 30000)", self.page)
        self.assertIn('fetch(WORKER_SHOW_URL + "/show/publish?message="', self.page)

    def test_dialogue_is_only_spoken_on_the_chart_matching_its_market(self):
        self.assertIn("const marcheDialogue = String(show.market || '').toUpperCase();", self.js)
        self.assertIn("if (!marcheDialogue || marcheDialogue !== codeMarche()) return;", self.js)
        self.assertIn("codeMarche() !== marcheDialogue", self.js)

    def test_duet_continuation_survives_delayed_browser_voice_loading(self):
        self.assertIn("voixEnAttente = { item, apresLecture };", self.js)
        self.assertIn("const item = attente.item;", self.js)
        self.assertIn("parlerLive(item, true, attente.apresLecture)", self.js)
        self.assertIn("if (!voixActive || !attente || !attente.item) return;", self.js)

    def test_synthesis_error_never_starts_the_second_duet_speaker(self):
        self.assertIn("utterance.onerror = () => {", self.js)
        self.assertIn("terminerLecture(false);", self.js)
        self.assertIn("if (continuer && typeof apresLecture === 'function') apresLecture();", self.js)


    def test_coach_duet_contains_separate_french_and_english_lines(self):
        self.assertIn("function traduireDialogueCoach(text, market)", self.page)
        self.assertIn("text1EN:", self.page)
        self.assertIn("text2EN:", self.page)
        self.assertIn("speaker1: speaker1, text1: String(text1 || \"\")", self.page)
        self.assertIn("speaker2: speaker2, text2: String(text2 || \"\")", self.page)
        self.assertIn("speaker1: speaker2, text1: textes[0].en", self.page)
        self.assertIn("speaker2: speaker1, text2: textes[1].en", self.page)

    def test_coach_duet_translation_is_required_before_publishing(self):
        self.assertIn("if (!traduction || !traduction[0] || !traduction[1]) return;", self.page)
        self.assertIn("if (!market || ![\"BTC\", \"GOLD\"].includes(market)) return;", self.page)

    def test_voice_relay_rejects_empty_or_unknown_market_for_duet(self):
        worker = (ROOT.parent / "cloud" / "align-tv-mailbox" / "worker.js").read_text(encoding="utf-8")
        self.assertIn('![\"BTC\", \"GOLD\"].includes(payload.market)', worker)

if __name__ == "__main__":
    unittest.main()
