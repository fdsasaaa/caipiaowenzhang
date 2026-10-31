"""Verify dispatched CI and finish a daily content PR in the producing job."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from datetime import date

REQUIRED_JOBS = ("pytest (3.10)", "pytest (3.13)")


class CloseoutError(ValueError):
    pass


def validate_evidence(repository, run_id, expected_sha, run, jobs, pr, files):
    """Reject incomplete, stale, failed or unrelated evidence before any write."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise CloseoutError("Invalid repository")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise CloseoutError("Expected head must be a full commit SHA")
    if (run.get("id") != run_id or run.get("path") != ".github/workflows/test.yml"
            or run.get("event") != "workflow_dispatch"
            or run.get("status") != "completed" or run.get("conclusion") != "success"):
        raise CloseoutError("Source must be the successful dispatched test.yml run")
    if any(run.get(key, {}).get("full_name") != repository
           for key in ("repository", "head_repository")):
        raise CloseoutError("CI repository does not match")
    branch = run.get("head_branch", "")
    match = re.fullmatch(r"automation/daily-website-ready-(\d{4}-\d{2}-\d{2})", branch)
    if not match:
        raise CloseoutError("Source branch is not a dated daily production branch")
    day = date.fromisoformat(match[1])
    if (run.get("head_sha") != expected_sha or pr.get("head", {}).get("sha") != expected_sha
            or pr.get("head", {}).get("ref") != branch):
        raise CloseoutError("CI and PR must match the exact expected head")
    if (pr.get("base", {}).get("ref") != "main"
            or any(pr.get(side, {}).get("repo", {}).get("full_name") != repository
                   for side in ("head", "base")) or pr.get("draft") is not False):
        raise CloseoutError("PR must be non-draft, same-repository and target main")
    if pr.get("state") != "open" and not pr.get("merged"):
        raise CloseoutError("PR is closed without being merged")
    rows = jobs.get("jobs", [])
    if jobs.get("total_count") != len(rows):
        raise CloseoutError("Incomplete CI job evidence")
    for name in REQUIRED_JOBS:
        matching = [job for job in rows if job.get("name") == name]
        if len(matching) != 1:
            raise CloseoutError(f"Required CI job must occur exactly once: {name}")
        job = matching[0]
        if (job.get("conclusion") != "success" or job.get("status") != "completed"
                or job.get("run_id") != run_id or job.get("head_sha") != expected_sha
                or job.get("run_attempt") != run.get("run_attempt")):
            raise CloseoutError(f"CI job failed or belongs to another attempt: {name}")
    if pr.get("changed_files") != len(files) or not files:
        raise CloseoutError("Incomplete PR file evidence")
    batch = "DAILY-" + day.strftime("%Y%m%d")
    allowed = (
        r"articles/approved/[^/]+\.json",
        rf"articles/public_release/{batch}/[^/]+\.public-r1\.json",
        rf"articles/public_release/manifests/{batch}\.json",
        rf"artifacts/daily_website_ready/{day.isoformat()}\.json",
        r"registry/articles\.jsonl",
    )
    for item in files:
        if (item.get("status") not in {"added", "modified"}
                or not any(re.fullmatch(pattern, item.get("filename", "")) for pattern in allowed)):
            raise CloseoutError("Daily closeout only accepts dated content inventory files")
    required = {f"articles/public_release/manifests/{batch}.json",
                f"artifacts/daily_website_ready/{day.isoformat()}.json", "registry/articles.jsonl"}
    if not required.issubset({item["filename"] for item in files}):
        raise CloseoutError("Daily manifest, report, or registry update is missing")


class GitHubCLI:
    def api(self, endpoint, method="GET", payload=None):
        command = ["gh", "api", "--method", method, endpoint]
        if payload is not None:
            command.extend(["--input", "-"])
        result = subprocess.run(command, input=None if payload is None else json.dumps(payload),
                                text=True, capture_output=True, check=True)
        return json.loads(result.stdout)


def closeout(client, repository, run_id, pr_number, expected_sha, sleep=time.sleep):
    prefix = f"repos/{repository}"
    run = client.api(f"{prefix}/actions/runs/{run_id}")
    jobs = client.api(f"{prefix}/actions/runs/{run_id}/jobs?per_page=100&filter=latest")
    pr_path = f"{prefix}/pulls/{pr_number}"
    pr = client.api(pr_path)
    files = client.api(f"{pr_path}/files?per_page=100")
    validate_evidence(repository, run_id, expected_sha, run, jobs, pr, files)
    if pr.get("merged"):
        return {"status": "already_merged", "pr": pr_number, "sha": pr["merge_commit_sha"]}
    for name in REQUIRED_JOBS:
        client.api(f"{prefix}/statuses/{expected_sha}", "POST", {
            "state": "success", "context": name,
            "description": "Verified exact dispatched dual-version CI",
            "target_url": f"https://github.com/{repository}/actions/runs/{run_id}",
        })
    last_error = None
    for attempt in range(12):
        current = client.api(pr_path)
        if current.get("head", {}).get("sha") != expected_sha:
            raise CloseoutError("PR head moved after CI verification; merge refused")
        if current.get("merged"):
            return {"status": "merged", "pr": pr_number, "sha": current["merge_commit_sha"]}
        try:
            result = client.api(f"{pr_path}/merge", "PUT", {
                "sha": expected_sha, "merge_method": "squash",
            })
            if result.get("merged") is True and result.get("sha"):
                return {"status": "merged", "pr": pr_number, "sha": result["sha"]}
            last_error = result.get("message", "GitHub did not confirm the merge")
        except subprocess.CalledProcessError as error:
            last_error = error.stderr.strip()
        if attempt < 11:
            sleep(5)
    raise CloseoutError(f"Verified checks did not result in a protected merge: {last_error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--pr-url", required=True)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args()
    match = re.fullmatch(rf"https://github\.com/{re.escape(args.repository)}/pull/([1-9][0-9]*)", args.pr_url)
    if not match:
        parser.error("PR URL must belong to the requested GitHub repository")
    try:
        result = closeout(GitHubCLI(), args.repository, args.run_id, int(match[1]), args.expected_sha)
    except (CloseoutError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Daily closeout failed: {error}\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
