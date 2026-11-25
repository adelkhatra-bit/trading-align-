#!/usr/bin/env python3
"""Enforce ALIGN's single repository identity and data-only live-data branch."""
from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "adelkhatra-bit/trading-align-"
ALLOWED_LIVE_DATA_FILES = {"live.json", "fermes.json"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("ALIGN_SOURCE_OF_TRUTH_FAILED: " + message)


def main() -> None:
    overlay = (ROOT / "docs/live/index.html").read_text(encoding="utf-8")
    canonical_url = (
        "https://raw.githubusercontent.com/"
        + REPOSITORY
        + "/live-data/live.json"
    )
    require(f'var SOURCE = "{canonical_url}";' in overlay,
            "live overlay must read live.json from the canonical repository")
    require("raw.githubusercontent.com/adelkhatra-bit/trading-auto/" not in overlay,
            "legacy repository URL remains in the live overlay")

    bot = (ROOT / "align-bot/align_bot.py").read_text(encoding="utf-8")
    require(
        'LIVE_DEPOT = os.environ.get("GITHUB_REPOSITORY") or "'
        + REPOSITORY
        + '"' in bot,
        "BOT publisher default repository is not canonical",
    )
    require(
        'LIVE_BRANCHE, LIVE_FICHIER = "live-data", "live.json"' in bot,
        "BOT publisher must write only the canonical live-data/live.json path",
    )

    url = (
        "https://api.github.com/repos/"
        + REPOSITORY
        + "/git/trees/live-data?recursive=1"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ALIGN-source-of-truth-validation",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(url, headers=headers)
    with urlopen(request, timeout=15) as response:
        tree = json.loads(response.read().decode("utf-8"))

    require(tree.get("truncated") is False, "live-data tree response is truncated")
    entries = tree.get("tree")
    require(isinstance(entries, list), "live-data tree is missing")
    paths = {entry.get("path") for entry in entries}
    require("live.json" in paths, "live-data/live.json is missing")
    unexpected = sorted(path for path in paths if path not in ALLOWED_LIVE_DATA_FILES)
    require(not unexpected, "non-data files found on live-data: " + ", ".join(unexpected))
    require(all(entry.get("type") == "blob" for entry in entries),
            "live-data may contain only root data files")

    print(
        "ALIGN_SOURCE_OF_TRUTH_OK "
        + "repository=" + REPOSITORY
        + " live_data_files=" + ",".join(sorted(paths))
    )


if __name__ == "__main__":
    main()
