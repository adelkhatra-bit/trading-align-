#!/usr/bin/env python3
"""ALIGN Actions watchdog: safe transient validation retry + blocker reports.

Never reruns the Telegram production worker, broker integrations, or deployments.
Never edits source code, merges PRs, or publishes to live-data.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import io
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

API = "https://api.github.com"
REPO = os.environ["GITHUB_REPOSITORY"]
TOKEN = os.environ["GITHUB_TOKEN"]
EVENT_NAME = os.environ.get("GITHUB_EVENT_NAME", "")
EVENT_PATH = os.environ.get("GITHUB_EVENT_PATH", "")
SAFE_RETRY_WORKFLOWS = {"ALIGN MTF validation"}
TRANSIENT_PATTERNS = (
    r"temporary failure in name resolution",
    r"connection reset by peer",
    r"connection aborted",
    r"remote end closed connection",
    r"read timed out",
    r"connection timed out",
    r"network is unreachable",
    r"tls handshake timeout",
    r"\bHTTP(?:Error)?\s*(?:429|500|502|503|504)\b",
    r"rate limit exceeded",
)
BOT_WORKFLOW = "ALIGN MTF BOT (signaux BTC + Gold + NASDAQ Telegram)"


def api(path: str, method: str = "GET", payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "ALIGN-Workflow-Watchdog",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        raw = response.read()
        return json.loads(raw.decode("utf-8")) if raw else None


def parse_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def existing_report(run_id: int) -> bool:
    issues = api(f"/repos/{REPO}/issues?state=all&per_page=100")
    marker = f"<!-- [align-watchdog:run-{run_id}] -->"
    return any(marker in (item.get("body") or "") for item in issues if "pull_request" not in item)


def _job_names(jobs: list[dict]) -> list[str]:
    return sorted({str(job.get("name") or "unknown") for job in jobs})


def _failed_step_names(jobs: list[dict]) -> list[str]:
    failed = {"failure", "timed_out", "action_required"}
    names = set()
    for job in jobs:
        job_name = str(job.get("name") or "unknown")
        for step in job.get("steps") or []:
            if step.get("conclusion") in failed:
                step_name = str(step.get("name") or "unknown")
                names.add(f"{job_name}::{step_name}")
    return sorted(names)


def blocker_fingerprint(run: dict, jobs: list[dict]) -> str:
    identity = {
        "workflow": str(run.get("name") or "unknown"),
        "branch": str(run.get("head_branch") or "unknown"),
        "jobs": _job_names(jobs),
        "steps": _failed_step_names(jobs),
    }
    canonical = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def existing_blocker(run: dict, jobs: list[dict], fingerprint: str) -> dict | None:
    issues = api(f"/repos/{REPO}/issues?state=open&per_page=100")
    marker = f"<!-- [align-watchdog:blocker-{fingerprint}] -->"
    workflow_line = f"**Workflow:** {run.get('name', 'unknown')}"
    branch_line = f"**Branch:** {run.get('head_branch', 'unknown')}"
    job_names = _job_names(jobs)

    for item in issues:
        if "pull_request" in item:
            continue
        body = item.get("body") or ""
        if marker in body:
            return item
        # Compatibility with open per-run reports created before blocker fingerprints existed.
        if (
            item.get("state") == "open"
            and workflow_line in body
            and branch_line in body
            and job_names
            and all(f"- **{name}** —" in body for name in job_names)
        ):
            return item
    return None


def report(run: dict, reason: str, jobs: list[dict] | None = None) -> None:
    run_id = int(run["id"])
    if existing_report(run_id):
        print(f"WATCHDOG_REPORT_EXISTS run={run_id}")
        return

    failed = jobs or []
    fingerprint = blocker_fingerprint(run, failed)
    blocker = existing_blocker(run, failed, fingerprint)
    if blocker:
        print(
            f"WATCHDOG_BLOCKER_EXISTS issue={blocker.get('number', 'unknown')} "
            f"workflow={run.get('name', 'unknown')} branch={run.get('head_branch', 'unknown')}"
        )
        return

    job_lines = [
        f"- **{job.get('name', 'unknown')}** — {job.get('conclusion') or job.get('status')}"
        for job in failed
    ] or ["- No failed job detail available from the Actions API."]
    step_names = _failed_step_names(failed)
    step_lines = [f"- {name}" for name in step_names] or ["- No failed step detail available from the Actions API."]
    body = "\n".join([
        f"<!-- [align-watchdog:run-{run_id}] -->",
        f"<!-- [align-watchdog:blocker-{fingerprint}] -->",
        "## ALIGN workflow watchdog report",
        "",
        f"**Workflow:** {run.get('name', 'unknown')}",
        f"**Branch:** {run.get('head_branch', 'unknown')}",
        f"**Commit:** {run.get('head_sha', 'unknown')}",
        f"**Run:** #{run_id} — {run.get('html_url', '')}",
        f"**Attempt:** {run.get('run_attempt', 'unknown')}",
        "",
        f"**Detection:** {reason}",
        "",
        "### Jobs",
        *job_lines,
        "",
        "### Failed steps",
        *step_lines,
        "",
        "### Safety",
        "- The production Telegram worker is never automatically rerun.",
        "- No source file, secret, branch protection, PR, or deployment is modified.",
        "- Inspect the failing job logs, prepare a minimal fix on a dedicated branch, and require green tests before merge.",
    ])
    title = f"ALIGN watchdog: {run.get('name', 'workflow')} blocked/failed on {run.get('head_branch', 'unknown')}"
    api(f"/repos/{REPO}/issues", method="POST", payload={"title": title[:240], "body": body})
    print(f"WATCHDOG_ISSUE_CREATED run={run_id} blocker={fingerprint}")

def failed_jobs(run_id: int) -> list[dict]:
    payload = api(f"/repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100")
    return [
        job for job in payload.get("jobs", [])
        if job.get("conclusion") in {"failure", "timed_out", "action_required"}
    ]


def transient_failure(jobs: list[dict]) -> bool:
    patterns = [re.compile(pattern, re.IGNORECASE) for pattern in TRANSIENT_PATTERNS]
    for job in jobs:
        try:
            req = urllib.request.Request(
                f"{API}/repos/{REPO}/actions/jobs/{job['id']}/logs",
                headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {TOKEN}",
                    "User-Agent": "ALIGN-Workflow-Watchdog",
                },
            )
            with urllib.request.urlopen(req, timeout=25) as response:
                raw = response.read(8_000_000)
            # GitHub redirects job-log downloads to a ZIP archive.
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    log = "\n".join(
                        archive.read(name).decode("utf-8", errors="replace")
                        for name in archive.namelist()
                        if not name.endswith("/")
                    )
            except zipfile.BadZipFile:
                log = raw.decode("utf-8", errors="replace")
        except Exception as exc:
            print(f"WATCHDOG_LOG_UNAVAILABLE job={job.get('id')} error={type(exc).__name__}")
            continue
        if any(pattern.search(log) for pattern in patterns):
            return True
    return False

def handle_completed(run: dict) -> None:
    name = run.get("name", "")
    conclusion = run.get("conclusion")
    run_id = int(run["id"])
    if name == "ALIGN Workflow Watchdog" or conclusion not in {"failure", "timed_out", "action_required"}:
        return

    jobs = failed_jobs(run_id)
    attempt = int(run.get("run_attempt") or 1)
    if name in SAFE_RETRY_WORKFLOWS and name != BOT_WORKFLOW and attempt == 1 and transient_failure(jobs):
        api(f"/repos/{REPO}/actions/runs/{run_id}/rerun-failed-jobs", method="POST")
        print(f"WATCHDOG_SAFE_RETRY run={run_id} workflow={name} attempt=1")
        return

    reason = (
        "The first safe retry also failed; manual diagnosis is required."
        if name in SAFE_RETRY_WORKFLOWS and attempt >= 2
        else "Workflow failed or timed out; automatic source-code changes are intentionally disabled."
    )
    report(run, reason, jobs)


def inspect_stale_runs() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    for branch in ("main", "live-data"):
        query = urllib.parse.urlencode({"branch": branch, "status": "in_progress", "per_page": 100})
        payload = api(f"/repos/{REPO}/actions/runs?{query}")
        for run in payload.get("workflow_runs", []):
            name = run.get("name", "")
            if name == "ALIGN Workflow Watchdog":
                continue
            age_minutes = (now - parse_time(run["created_at"])).total_seconds() / 60
            threshold = 350 if name == BOT_WORKFLOW else 20
            if age_minutes >= threshold:
                report(
                    run,
                    f"Run has remained in progress for {age_minutes:.1f} minutes "
                    f"(watchdog threshold: {threshold} minutes). It was not cancelled.",
                )


def inspect_recent_failures() -> None:
    """Fallback scan: catch failed runs even when chained workflow_run events are not delivered."""
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)
    failures = {"failure", "timed_out", "action_required"}
    for branch in ("main", "live-data"):
        query = urllib.parse.urlencode({"branch": branch, "status": "completed", "per_page": 100})
        payload = api(f"/repos/{REPO}/actions/runs?{query}")
        for run in payload.get("workflow_runs", []):
            if run.get("name") == "ALIGN Workflow Watchdog":
                continue
            if run.get("conclusion") not in failures:
                continue
            if parse_time(run["created_at"]) < cutoff:
                continue
            handle_completed(run)


def main() -> int:
    if EVENT_NAME == "workflow_run":
        with open(EVENT_PATH, encoding="utf-8") as handle:
            event = json.load(handle)
        run = event.get("workflow_run") or {}
        if run.get("head_branch") not in {"main", "live-data"}:
            print("WATCHDOG_SKIP branch outside production/publication scope")
            return 0
        handle_completed(run)
    else:
        inspect_stale_runs()
        inspect_recent_failures()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        print(f"WATCHDOG_GITHUB_API_ERROR status={exc.code}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"WATCHDOG_ERROR type={type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1)
