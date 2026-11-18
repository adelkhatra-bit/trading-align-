#!/usr/bin/env python3
"""Failure-to-issue coordinator for ALIGN. It never assigns agents or changes code."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
EXPECTED_REPO = "adelkhatra-bit/trading-align-"
LABEL = "align-repair"
IGNORED_PRS = {401, 448, 451}
MAX_ATTEMPTS = 2
SHA_MARKER = re.compile(r"<!-- ALIGN_REPAIR_SHA=([0-9a-f]{40}) -->")
ATTEMPT_MARKER = re.compile(r"<!-- ALIGN_REPAIR_ATTEMPT=(\d+) -->")
RUN_MARKER = re.compile(r"<!-- ALIGN_REPAIR_RUN=(\d+) -->")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GH_TOKEN", "")


def request_json(path: str, method: str = "GET", payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "ALIGN-Auto-Repair-Coordinator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
        return json.loads(raw.decode("utf-8")) if raw else None


def event_target(event: dict) -> dict | None:
    run = event.get("workflow_run")
    if not isinstance(run, dict) or run.get("conclusion") != "failure":
        return None
    sha = str(run.get("head_sha") or "").lower()
    branch = str(run.get("head_branch") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        return None
    prs = run.get("pull_requests") or []
    pr_numbers = sorted({
        int(item["number"]) for item in prs
        if isinstance(item, dict) and str(item.get("number", "")).isdigit()
    })
    if pr_numbers and any(number in IGNORED_PRS for number in pr_numbers):
        return None
    if not pr_numbers and branch != "main":
        return None
    return {
        "sha": sha,
        "branch": branch,
        "pr_numbers": pr_numbers,
        "run_id": int(run.get("id") or 0),
        "run_name": str((run.get("name") or "workflow")[:180]),
        "run_url": str(run.get("html_url") or ""),
        "head_branch": branch,
    }


def summarize_failed_jobs(jobs_payload: dict) -> str:
    lines = []
    for job in jobs_payload.get("jobs") or []:
        if job.get("conclusion") != "failure":
            continue
        failed_steps = [
            str(step.get("name") or "step")
            for step in job.get("steps") or []
            if step.get("conclusion") == "failure"
        ]
        suffix = "; étapes en échec : " + ", ".join(failed_steps[:8]) if failed_steps else ""
        lines.append(f"- {job.get('name') or 'job'}{suffix}")
    return "\n".join(lines) if lines else "- Échec du workflow signalé par GitHub; détail des jobs indisponible."


def all_issues() -> list[dict]:
    found = []
    for page in range(1, 11):
        query = urllib.parse.urlencode({"state": "all", "per_page": 100, "page": page})
        batch = request_json(f"/repos/{EXPECTED_REPO}/issues?{query}")
        if not isinstance(batch, list):
            raise RuntimeError("GitHub returned an invalid issues response.")
        found.extend(item for item in batch if "pull_request" not in item)
        if len(batch) < 100:
            return found
    raise RuntimeError("Issue pagination exceeded the 1000-item safety limit.")


def find_issue_for_sha(issues: list[dict], sha: str) -> dict | None:
    marker = f"<!-- ALIGN_REPAIR_SHA={sha} -->"
    return next((item for item in issues if marker in (item.get("body") or "")), None)


def ensure_label() -> None:
    labels = request_json(f"/repos/{EXPECTED_REPO}/labels?per_page=100")
    if any(item.get("name") == LABEL for item in (labels or [])):
        return
    try:
        request_json(
            f"/repos/{EXPECTED_REPO}/labels", method="POST",
            payload={"name": LABEL, "color": "D4C5F9", "description": "Échec CI ALIGN à diagnostiquer et réparer sous contrôle humain"},
        )
    except urllib.error.HTTPError as exc:
        if exc.code != 422:
            raise


def comments_for_issue(number: int) -> list[dict]:
    comments = []
    for page in range(1, 11):
        query = urllib.parse.urlencode({"per_page": 100, "page": page})
        batch = request_json(f"/repos/{EXPECTED_REPO}/issues/{number}/comments?{query}")
        if not isinstance(batch, list):
            raise RuntimeError("GitHub returned an invalid issue-comments response.")
        comments.extend(batch)
        if len(batch) < 100:
            return comments
    raise RuntimeError("Repair issue comment pagination exceeded its safety limit.")


def next_attempt(issue: dict, comments: list[dict]) -> int:
    values = [int(x) for x in ATTEMPT_MARKER.findall(issue.get("body") or "")]
    for item in comments:
        values.extend(int(x) for x in ATTEMPT_MARKER.findall(item.get("body") or ""))
    return max(values, default=0) + 1


def repair_issue_body(target: dict, failure_summary: str, attempt: int) -> str:
    prs = ", ".join(f"#{n}" for n in target["pr_numbers"]) or "main"
    return f"""## Échec CI ALIGN — diagnostic requis

- Dépôt : `{EXPECTED_REPO}`
- Branche : `{target['head_branch']}`
- SHA : `{target['sha']}`
- PR associée : {prs}
- Workflow : {target['run_name']}
- Run : [{target['run_id']}]({target['run_url']})
- Tentative de réparation : {attempt}/{MAX_ATTEMPTS}

### Étapes en échec
{failure_summary}

### Consignes à l'agent (assignation humaine par défaut)
1. Diagnostiquer uniquement les fichiers liés à cet échec.
2. Proposer un correctif minimal sur une branche dédiée et une PR brouillon.
3. Exécuter les tests ciblés puis la suite de régression concernée.
4. Ne jamais merger ni déployer. Ne modifier ni Pine, ni le design, ni les animations, ni les signaux ou le trading sans mission explicite.
5. Préserver `live-data/live.json` et ne jamais afficher de secrets.
6. Un seul agent à la fois; maximum deux tentatives sur ce SHA. Si les preuves manquent, rendre un rapport et attendre l'humain.

L'assignation à Copilot cloud agent reste manuelle par défaut. Aucun agent n'est lancé par ce workflow.
 
<!-- ALIGN_REPAIR_SHA={target['sha']} -->
<!-- ALIGN_REPAIR_ATTEMPT={attempt} -->
<!-- ALIGN_REPAIR_RUN={target['run_id']} -->
"""


def main() -> int:
    if REPO != EXPECTED_REPO or not TOKEN:
        raise RuntimeError("Repository scope mismatch or missing Actions token.")
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path:
        print("No GitHub event payload; nothing to do.")
        return 0
    with open(event_path, encoding="utf-8") as handle:
        event = json.load(handle)
    target = event_target(event)
    if target is None:
        print("No eligible failed ALIGN run; no issue created.")
        return 0

    jobs = request_json(f"/repos/{EXPECTED_REPO}/actions/runs/{target['run_id']}/jobs?per_page=100")
    summary = summarize_failed_jobs(jobs if isinstance(jobs, dict) else {})
    issues = all_issues()
    existing = find_issue_for_sha(issues, target["sha"])
    ensure_label()

    if existing:
        comments = comments_for_issue(int(existing["number"]))
        run_marker = f"<!-- ALIGN_REPAIR_RUN={target['run_id']} -->"
        if run_marker in (existing.get("body") or "") or any(run_marker in (c.get("body") or "") for c in comments):
            print(f"Duplicate failure ignored for SHA {target['sha']} and run {target['run_id']}.")
            return 0
        attempt = next_attempt(existing, comments)
        if attempt > MAX_ATTEMPTS:
            print(f"Repair attempt limit reached for SHA {target['sha']}; no further action.")
            return 0
        body = (
            f"Nouvel échec lié au même SHA — tentative {attempt}/{MAX_ATTEMPTS}.\n\n"
            f"- Workflow : {target['run_name']}\n"
            f"- Run : [{target['run_id']}]({target['run_url']})\n\n"
            f"### Étapes en échec\n{summary}\n\n"
            f"<!-- ALIGN_REPAIR_ATTEMPT={attempt} -->\n"
            f"<!-- ALIGN_REPAIR_RUN={target['run_id']} -->"
        )
        request_json(f"/repos/{EXPECTED_REPO}/issues/{existing['number']}/comments", "POST", {"body": body})
        print(f"Updated existing repair issue #{existing['number']} for SHA {target['sha']} (attempt {attempt}).")
        return 0

    body = repair_issue_body(target, summary, 1)
    created = request_json(
        f"/repos/{EXPECTED_REPO}/issues", "POST",
        {"title": f"[ALIGN AUTO-REPAIR] {target['run_name']} — {target['sha'][:12]}",
         "body": body, "labels": [LABEL]},
    )
    print(f"Created repair issue #{created.get('number')} for SHA {target['sha']}; attempt 1/{MAX_ATTEMPTS}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        print(f"GitHub API request failed with HTTP {exc.code}.", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"ALIGN repair coordinator failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
