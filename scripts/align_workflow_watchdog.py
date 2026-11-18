#!/usr/bin/env python3
"""ALIGN Actions watchdog: safe transient validation retry + blocker reports.

Never reruns the Telegram production worker, broker integrations, or deployments.
Never edits source code, merges PRs, or publishes to live-data.
"""
from __future__ import annotations

import datetime as dt
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
RUNS_PER_PAGE = 100
MAX_RUNS_PER_QUERY = 1000


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
    marker = f"[align-watchdog:run-{run_id}]"
    return any(marker in (item.get("body") or "") for item in issues if "pull_request" not in item)


def report(run: dict, reason: str, jobs: list[dict] | None = None) -> None:
    run_id = int(run["id"])
    if existing_report(run_id):
        print(f"WATCHDOG_REPORT_EXISTS run={run_id}")
        return
    failed = jobs or []
    job_lines = [
        f"- **{job.get('name', 'unknown')}** — {job.get('conclusion') or job.get('status')}"
        for job in failed
    ] or ["- No failed job detail available from the Actions API."]
    body = "\n".join([
        f"<!-- [align-watchdog:run-{run_id}] -->",
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
        "### Safety",
        "- The production Telegram worker is never automatically rerun.",
        "- No source file, secret, branch protection, PR, or deployment is modified.",
        "- Inspect the failing job logs, prepare a minimal fix on a dedicated branch, and require green tests before merge.",
    ])
    title = f"ALIGN watchdog: {run.get('name', 'workflow')} blocked/failed (run {run_id})"
    api(f"/repos/{REPO}/issues", method="POST", payload={"title": title[:240], "body": body})
    print(f"WATCHDOG_ISSUE_CREATED run={run_id}")


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


def _api_time(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _scan_completed_window(
    branch: str,
    start: dt.datetime,
    end: dt.datetime,
    failures: set[str],
    seen_run_ids: set[int],
) -> None:
    """Scan one created-time window without silently crossing GitHub's 1,000-result cap."""
    query_base = {
        "branch": branch,
        "status": "completed",
        "created": f"{_api_time(start)}..{_api_time(end)}",
        "per_page": RUNS_PER_PAGE,
    }
    first_query = urllib.parse.urlencode({**query_base, "page": 1})
    first_payload = api(f"/repos/{REPO}/actions/runs?{first_query}")
    first_runs = first_payload.get("workflow_runs", [])
    total_count_value = first_payload.get("total_count")
    if total_count_value is None:
        if len(first_runs) >= RUNS_PER_PAGE:
            raise RuntimeError(
                f"WATCHDOG_SCAN_INCOMPLETE branch={branch}: GitHub omitted total_count "
                "for a full page; refusing to assume the 1,000-result cap was not reached."
            )
        total_count = len(first_runs)
    else:
        total_count = int(total_count_value)

    if total_count > MAX_RUNS_PER_QUERY:
        span_seconds = int((end - start).total_seconds())
        if span_seconds < 2:
            raise RuntimeError(
                f"WATCHDOG_SCAN_INCOMPLETE branch={branch}: {total_count} runs remain "
                "inside the smallest supported time window."
            )
        midpoint = start + dt.timedelta(seconds=span_seconds // 2)
        if midpoint <= start or midpoint >= end:
            raise RuntimeError(
                f"WATCHDOG_SCAN_INCOMPLETE branch={branch}: unable to subdivide "
                "a saturated GitHub Actions query."
            )
        print(
            f"WATCHDOG_SPLIT_WINDOW branch={branch} total={total_count} "
            f"start={_api_time(start)} end={_api_time(end)}"
        )
        _scan_completed_window(branch, start, midpoint, failures, seen_run_ids)
        _scan_completed_window(branch, midpoint, end, failures, seen_run_ids)
        return

    if total_count == 0:
        return

    page_count = (total_count + RUNS_PER_PAGE - 1) // RUNS_PER_PAGE
    for page in range(1, page_count + 1):
        if page == 1:
            runs = first_runs
        else:
            query = urllib.parse.urlencode({**query_base, "page": page})
            payload = api(f"/repos/{REPO}/actions/runs?{query}")
            runs = payload.get("workflow_runs", [])

        if not runs:
            raise RuntimeError(
                f"WATCHDOG_SCAN_INCOMPLETE branch={branch}: empty page {page} "
                f"before expected page {page_count}."
            )

        for run in runs:
            run_id = int(run.get("id") or 0)
            if not run_id or run_id in seen_run_ids:
                continue
            seen_run_ids.add(run_id)

            created_at = parse_time(run["created_at"])
            if created_at < start or created_at > end:
                continue
            if run.get("name") == "ALIGN Workflow Watchdog":
                continue
            if run.get("conclusion") in failures:
                handle_completed(run)


def inspect_recent_failures() -> None:
    """Fallback scan: cover the full 24-hour window, splitting saturated API ranges."""
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    cutoff = now - dt.timedelta(hours=24)
    failures = {"failure", "timed_out", "action_required"}
    for branch in ("main", "live-data"):
        _scan_completed_window(branch, cutoff, now, failures, set())


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
