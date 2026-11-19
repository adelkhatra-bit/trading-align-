"""Regression for consent guards on spontaneous live announcements."""
import datetime
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import align_bot as ab


class LiveAnnouncementConsentGuardTest(unittest.TestCase):
    def test_refused_paused_and_prospect_chats_receive_no_live_announcement(self):
        day = datetime.datetime.now(ab.PARIS).strftime("%Y-%m-%d")
        state = {
            "bot_off": ["11"],
            "quiet": ["44"],
            "prospects": ["33"],
            "notif_spontanee": {},
        }
        sent = []
        with patch.object(ab, "_envoi_sur", side_effect=lambda cid, **kw: sent.append(str(cid)) or {"ok": True}), \
             patch.object(ab, "clavier_live", return_value=None), \
             patch.object(ab, "notif_du_jour_libre", return_value=True), \
             patch.object(ab, "marquer_notif_du_jour"):
            ab.live_annoncer_debut(state, {"11", "22", "33", "44"})
        self.assertEqual(sent, ["22"])


if __name__ == "__main__":
    unittest.main()
