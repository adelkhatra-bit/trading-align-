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

    def test_visible_chart_acquires_owner_before_publishing_and_polling(self):
        initial = self.js.rindex("  ecouter();\\n  pingEcran();")
        owner = self.js.index("if (estProprietaireEcran()) {", initial)
        publish = self.js.index("publierEtatCoach(voixActive);", owner)
        poll = self.js.index("ecouterDialoguesCoach();", publish)
        self.assertLess(initial, owner)
        self.assertLess(owner, publish)
        self.assertLess(publish, poll)

    def test_voice_state_is_shared_between_tabs_and_only_owner_publishes(self):
        self.assertIn("function estProprietaireEcran()", self.js)
        self.assertIn("const owner = enabled ? prendreLeaseHeartbeat() : (forceOwner || estProprietaireEcran());", self.js)
        self.assertIn("if (!owner) return false;", self.js)
        self.assertIn("window.addEventListener('storage', event => {", self.js)
        self.assertIn("event.key !== 'alignVoixActive'", self.js)
        self.assertIn("voixActive = event.newValue === '1';", self.js)
        self.assertIn("!estProprietaireEcran() || coachPollTimer", self.js)
        self.assertIn("!estProprietaireEcran() || !['ia', 'marche', 'coach'].includes(item.source)", self.js)

    def test_hidden_non_owner_tab_cannot_disable_active_tab_voice(self):
        start = self.js.index("function gererVisibilite()")
        end = self.js.index("document.addEventListener('visibilitychange', gererVisibilite);", start)
        hidden = self.js[start:end]
        self.assertIn("const etaitProprietaire = estProprietaireEcran();", hidden)
        self.assertIn("if (etaitProprietaire) {", hidden)
        self.assertIn("publierEtatCoach(false, true);", hidden)
        self.assertNotIn("publierEtatCoach(false);", hidden)

    def test_french_male_voice_map_accepts_supported_windows_and_chrome_aliases(self):
        self.assertIn("t: { fr: /\\b(?:paul|henri|pierre|david|thomas|remy|rémy|male)\\b/i", self.js)
        self.assertIn("denise", self.js.lower())
        self.assertIn("thomas", self.js.lower())

    def test_french_female_voice_map_accepts_windows_denise_and_eloise(self):
        self.assertIn("l: { fr: /\\b(?:hortense|julie|audrey|charlotte|amelie|amélie|denise|eloise|éloïse|female)\\b/i", self.js)

    def test_voice_retry_does_not_depend_only_on_voiceschanged(self):
        self.assertIn("function programmerRepriseVoix()", self.js)
        self.assertIn("const delais = [250, 750, 1500, 3000, 6000];", self.js)
        self.assertIn("const langue = item && item.en ? 'en' : 'fr';", self.js)
        self.assertIn("voixRetryTimers.push(setTimeout(tenter, 0));", self.js)
        self.assertIn("programmerRepriseVoix();", self.js)

    def test_voice_button_reports_missing_voices_and_synthesis_errors(self):
        self.assertIn("function mettreEtatVoix()", self.js)
        self.assertIn("⚠️ VOIX FR INCOMPLÈTE", self.js)
        self.assertIn("utterance.onerror = event => {", self.js)
        self.assertIn("event && event.error", self.js)
        self.assertIn("Synthèse démarrée :", self.js)

    def test_ai_commentary_from_ntfy_is_connected_to_the_speech_engine(self):
        self.assertIn("const source = new EventSource('https://ntfy.sh/' + SUJET + '/sse');", self.js)
        self.assertIn("if (txt.startsWith('IA:')) { recuIA(txt.slice(3)); return; }", self.js)
        self.assertIn("const dureeFR = parlerLive(fr);", self.js)
        self.assertIn("publierEtatCoach(true)", self.js)

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
        self.assertIn("function publierDialogueCoachPair(speaker1, text1, speaker2, text2, market, text1EN, text2EN)", self.page)
        self.assertIn('type: "ALIGN_SHOW", action: "PAIR"', self.page)
        self.assertIn("var premier = dernierHoteCoach", self.page)
        self.assertIn("var textes = changement.textes;", self.page)
        self.assertIn("textes[0].en, textes[1].en", self.page)
        self.assertIn("if (nom !== \"BTC\" && nom !== \"GOLD\") continue;", self.page)
        self.assertIn("parler(premier, textes[0].fr)", self.page)
        self.assertIn("parler(second, textes[1].fr)", self.page)
        self.assertIn("parler(premier, textes[0].en)", self.page)
        self.assertIn("parler(second, textes[1].en)", self.page)

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
        self.assertIn("duration1EN: duration1EN", self.page)
        self.assertIn("duration2EN: duration2EN", self.page)
        self.assertIn("function parlerLive(item, forcer = false, apresLecture = null)", self.js)
        self.assertIn("utterance.onend = () => terminerLecture(true);", self.js)
        self.assertIn("if (continuer && typeof apresLecture === 'function') apresLecture();", self.js)
        self.assertIn("{ texte: show.text1, speaker: show.speaker1, en: false }", self.js)
        self.assertIn("{ texte: show.text2, speaker: show.speaker2, en: false }", self.js)
        self.assertIn("{ texte: show.text1EN, speaker: show.speaker1EN || show.speaker1, en: true }", self.js)
        self.assertIn("{ texte: show.text2EN, speaker: show.speaker2EN || show.speaker2, en: true }", self.js)
        self.assertIn("jouer(index + 1)", self.js)
        self.assertIn("coachPairTimers.push(setTimeout(() => jouer(index + 1), 500));", self.js)
        self.assertNotIn("pause + 500", self.js)
        self.assertIn("setInterval(echange, 30000)", self.page)
        self.assertIn('fetch(WORKER_SHOW_URL + "/show/publish?message="', self.page)

    def test_dialogue_is_only_spoken_on_the_chart_matching_its_market(self):
        self.assertIn("const marcheDialogue = String(show.market || '').toUpperCase();", self.js)
        self.assertIn("if (!['BTC', 'GOLD'].includes(marcheDialogue) || marcheDialogue !== codeMarche()) return;", self.js)
        self.assertIn("codeMarche() !== marcheDialogue", self.js)

    def test_duet_continuation_survives_delayed_browser_voice_loading(self):
        self.assertIn("voixEnAttente = { item, apresLecture };", self.js)
        self.assertIn("const item = attente.item;", self.js)
        self.assertIn("parlerLive(item, true, attente.apresLecture)", self.js)
        self.assertIn("if (!voixActive || !attente || !attente.item) return;", self.js)

    def test_synthesis_error_does_not_block_the_remaining_duet_replies(self):
        self.assertIn("utterance.onerror = event => {", self.js)
        self.assertIn("terminerLecture(true);", self.js)
        self.assertIn("if (continuer && typeof apresLecture === 'function') apresLecture();", self.js)
        self.assertIn("coachDialogueActive = true;", self.js)
        self.assertIn("coachDialogueActive = false;", self.js)
        self.assertIn("if (coachDialogueActive && item.source !== 'coach') return 0;", self.js)



    def test_missing_browser_voice_does_not_leave_coach_priority_lock_stuck(self):
        self.assertIn("if (item.source === 'coach') coachDialogueActive = true;", self.js)
        self.assertIn("if (item.source === 'coach' && dureeFR <= 0) coachDialogueActive = false;", self.js)
        self.assertIn("const duree = parlerLive(", self.js)
        self.assertIn("if (duree <= 0) coachDialogueActive = false;", self.js)
        self.assertIn("if (!['t', 'l'].includes(item.speaker)) { coachDialogueActive = false; return; }", self.js)
        self.assertIn("if (!vivant || !voixActive || codeMarche() !== marcheDialogue) { coachDialogueActive = false; return; }", self.js)

    def test_coach_duet_contains_separate_french_and_english_lines(self):
        self.assertIn("var anglaisPremiere;", self.page)
        self.assertIn("var secondeEN =", self.page)
        self.assertIn("return [{ fr: premiere, en: anglaisPremiere }, { fr: seconde, en: secondeEN }]", self.page)
        self.assertIn("function publierDialogueCoachPair(speaker1, text1, speaker2, text2, market, text1EN, text2EN)", self.page)
        self.assertIn("speaker1EN: speaker1, text1EN: text1EN", self.page)
        self.assertIn("speaker2EN: speaker2, text2EN: text2EN", self.page)
        self.assertIn("textes[0].en, textes[1].en", self.page)

    def test_coach_duet_translation_is_required_before_publishing(self):
        self.assertIn('!["BTC", "GOLD"].includes(marche)', self.page)
        self.assertIn('typeof text1EN !== "string"', self.page)
        self.assertIn('typeof text2EN !== "string"', self.page)
        worker = (ROOT.parent / "cloud" / "align-tv-mailbox" / "worker.js").read_text(encoding="utf-8")
        self.assertIn('!["BTC", "GOLD"].includes(payload.market)', worker)
        self.assertIn('typeof payload.text1EN !== "string"', worker)
        self.assertIn('typeof payload.text2EN !== "string"', worker)

    def test_voice_relay_rejects_empty_or_unknown_market_for_duet(self):
        worker = (ROOT.parent / "cloud" / "align-tv-mailbox" / "worker.js").read_text(encoding="utf-8")
        self.assertIn('![\"BTC\", \"GOLD\"].includes(payload.market)', worker)


if __name__ == "__main__":
    unittest.main()
