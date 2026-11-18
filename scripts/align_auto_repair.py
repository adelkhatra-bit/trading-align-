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
BOT_LOGIN = "github-actions[bot]"
SHA_MARKER = re.compile(r"<!-- ALIGN_REPAIR_SHA=([0-9a-f]{40}) -->")
ATTEMPT_MARKER = re.compile(r"<!-- ALIGN_REPAIR_ATTEMPT=(\d+) -->")
RUN_MARKER = re.compile(r"<!-- ALIGN_REPAIR_RUN=(\d+) -->")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GH_TOKEN", "")
COPILOT_TOKEN = os.environ.get("COPILOT_GITHUB_TOKEN", "")


def request_json(path: str, method: str = "GET", payload: dict | None = None, token: str | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN if token is None else token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "ALIGN-Auto-Repair-Coordinator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read()
        return json.loads(raw.decode("utf-8")) if raw else None


def is_actions_bot(item: dict | None) -> bool:
    user = item.get("user") if isinstance(item, dict) else None
    return isinstance(user, dict) and user.get("login") == BOT_LOGIN


def event_target(event: dict) -> dict | None:
    run = event.get("workflow_run")
    if not isinstance(run, dict) or run.get("conclusion") not in {"failure", "timed_out"}:
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
        if job.get("conclusion") not in {"failure", "timed_out"}:
            continue
        failed_steps = [
            str(step.get("name") or "step")
            for step in job.get("steps") or []
            if step.get("conclusion") in {"failure", "timed_out"}
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



def request_graphql(query: str) -> dict:
    data = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=data, method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {COPILOT_TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "GraphQL-Features": "issues_copilot_assignment_api_support,coding_agent_model_selection",
            "Content-Type": "application/json",
            "User-Agent": "ALIGN-Auto-Repair-Coordinator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def assign_copilot_if_available(issue_number: int, issues: list[dict]) -> bool:
    """Assign only when the user-owned token exists, Copilot is enabled, and no agent is active."""
    if not COPILOT_TOKEN:
        return False
    for issue in issues:
        if issue.get("state") != "open":
            continue
        assignees = issue.get("assignees") or []
        if any(item.get("login") == "copilot-swe-agent[bot]" for item in assignees):
            print("Copilot assignment skipped: another ALIGN repair issue already has an active Copilot agent.")
            return False

    query = """query {
      repository(owner: "adelkhatra-bit", name: "trading-align-") {
        suggestedActors(capabilities: [CAN_BE_ASSIGNED], first: 100) {
          nodes { login }
        }
      }
    }"""
    try:
        result = request_graphql(query)
        nodes = (((result or {}).get("data") or {}).get("repository") or {}).get("suggestedActors", {}).get("nodes") or []
        if not any(item.get("login") == "copilot-swe-agent" for item in nodes):
            print("Copilot cloud agent is not available as an assignable actor; issue left for manual assignment.")
            return False
        instructions = (
            "Work only in adelkhatra-bit/trading-align- on a dedicated branch based on main. "
            "Diagnose the supplied failing SHA/run, make the smallest targeted fix, add focused regression tests, "
            "and open a draft pull request. Never merge or deploy. Do not modify Pine, indicator design, animations, "
            "signal strategy, Entry/SL/TP, broker execution, or live-data/live.json. Never expose secrets. "
            "Preserve all existing ALIGN and Claude-era behavior. Stop and report if evidence is insufficient."
        )
        request_json(
            f"/repos/{EXPECTED_REPO}/issues/{issue_number}/assignees",
            method="POST",
            payload={
                "assignees": ["copilot-swe-agent[bot]"],
                "agent_assignment": {
                    "target_repo": EXPECTED_REPO,
                    "base_branch": "main",
                    "custom_instructions": instructions,
                },
            },
            token=COPILOT_TOKEN,
        )
        print(f"Copilot cloud agent assigned to repair issue #{issue_number}.")
        return True
    except urllib.error.HTTPError as exc:
        print(f"Copilot automatic assignment unavailable (HTTP {exc.code}); issue remains available for manual assignment.")
        return False
    except Exception as exc:
        print(f"Copilot automatic assignment unavailable ({type(exc).__name__}); issue remains available for manual assignment.")
        return False

def find_issue_for_sha(issues: list[dict], sha: str) -> dict | None:
    marker = f"<!-- ALIGN_REPAIR_SHA={sha} -->"
    return next((item for item in issues if is_actions_bot(item) and marker in (item.get("body") or "")), None)


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
    values = []
    if is_actions_bot(issue):
        values.extend(int(x) for x in ATTEMPT_MARKER.findall(issue.get("body") or ""))
    for item in comments:
        if is_actions_bot(item):
            values.extend(int(x) for x in ATTEMPT_MARKER.findall(item.get("body") or ""))
    return max(values, default=0) + 1


def has_run_marker(issue: dict, comments: list[dict], marker: str) -> bool:
    if is_actions_bot(issue) and marker in (issue.get("body") or ""):
        return True
    return any(is_actions_bot(item) and marker in (item.get("body") or "") for item in comments)


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
        if has_run_marker(existing, comments, run_marker):
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
    issue_number = int(created.get("number") or 0)
    print(f"Created repair issue #{issue_number} for SHA {target['sha']}; attempt 1/{MAX_ATTEMPTS}.")
    if issue_number:
        assign_copilot_if_available(issue_number, issues)
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
