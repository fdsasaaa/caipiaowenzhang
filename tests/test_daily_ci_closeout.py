from copy import deepcopy

import pytest

from engine.daily_ci_closeout import CloseoutError, REQUIRED_JOBS, closeout


REPO = "owner/content"
SHA = "a" * 40
BRANCH = "automation/daily-website-ready-2026-09-05"


class FakeGitHub:
    def __init__(self):
        self.run = {
            "id": 123, "path": ".github/workflows/test.yml", "event": "workflow_dispatch",
            "status": "completed", "conclusion": "success", "head_sha": SHA,
            "head_branch": BRANCH, "run_attempt": 1,
            "repository": {"full_name": REPO}, "head_repository": {"full_name": REPO},
        }
        self.jobs = {"total_count": 2, "jobs": [
            {"name": name, "status": "completed", "conclusion": "success",
             "run_id": 123, "head_sha": SHA, "run_attempt": 1}
            for name in REQUIRED_JOBS
        ]}
        self.pr = {
            "state": "open", "draft": False, "merged": False, "changed_files": 3,
            "head": {"sha": SHA, "ref": BRANCH, "repo": {"full_name": REPO}},
            "base": {"ref": "main", "repo": {"full_name": REPO}},
        }
        self.files = [
            {"filename": "articles/public_release/manifests/DAILY-20260905.json", "status": "added"},
            {"filename": "artifacts/daily_website_ready/2026-09-05.json", "status": "added"},
            {"filename": "registry/articles.jsonl", "status": "modified"},
        ]
        self.writes = []
        self.pr_reads = 0
        self.move_after_verification = False
        self.merge_allowed = True

    def api(self, endpoint, method="GET", payload=None):
        if method != "GET":
            self.writes.append((endpoint, method, payload))
            if method == "PUT":
                assert payload == {"sha": SHA, "merge_method": "squash"}
                return {"merged": self.merge_allowed, "sha": "b" * 40,
                        "message": "required checks are still pending"}
            return {}
        if endpoint.endswith("/jobs?per_page=100&filter=latest"):
            return deepcopy(self.jobs)
        if endpoint.endswith("/files?per_page=100"):
            return deepcopy(self.files)
        if endpoint.endswith("/actions/runs/123"):
            return deepcopy(self.run)
        assert endpoint.endswith("/pulls/117")
        self.pr_reads += 1
        result = deepcopy(self.pr)
        if self.move_after_verification and self.pr_reads > 1:
            result["head"]["sha"] = "c" * 40
        return result


def finish(client):
    return closeout(client, REPO, 123, 117, SHA, sleep=lambda _: None)


def test_success_relays_only_verified_jobs_and_requires_confirmed_exact_head_merge():
    client = FakeGitHub()
    result = finish(client)
    assert result == {"status": "merged", "pr": 117, "sha": "b" * 40}
    assert [write[2]["context"] for write in client.writes[:2]] == list(REQUIRED_JOBS)
    assert all(write[2]["state"] == "success" for write in client.writes[:2])
    assert client.writes[-1][1:] == ("PUT", {"sha": SHA, "merge_method": "squash"})


@pytest.mark.parametrize("field,value", [
    ("id", 999), ("path", ".github/workflows/unrelated.yml"), ("event", "pull_request"),
    ("status", "in_progress"), ("conclusion", "failure"), ("head_sha", "b" * 40),
    ("head_branch", "fix/unrelated"), ("repository", {"full_name": "other/repo"}),
    ("head_repository", {"full_name": "other/repo"}),
])
def test_unrelated_or_failed_source_never_writes_a_success_status(field, value):
    client = FakeGitHub()
    client.run[field] = value
    with pytest.raises(CloseoutError):
        finish(client)
    assert client.writes == []


@pytest.mark.parametrize("damage", ["missing", "duplicate", "failed", "old_attempt", "old_sha", "truncated"])
def test_missing_failed_duplicate_and_stale_matrix_evidence_is_rejected(damage):
    client = FakeGitHub()
    if damage == "missing":
        client.jobs["jobs"].pop()
        client.jobs["total_count"] = 1
    elif damage == "duplicate":
        client.jobs["jobs"].append(deepcopy(client.jobs["jobs"][0]))
        client.jobs["total_count"] = 3
    elif damage == "failed":
        client.jobs["jobs"][1]["conclusion"] = "failure"
    elif damage == "old_attempt":
        client.jobs["jobs"][1]["run_attempt"] = 2
    elif damage == "old_sha":
        client.jobs["jobs"][1]["head_sha"] = "c" * 40
    else:
        client.jobs["total_count"] = 100
    with pytest.raises(CloseoutError):
        finish(client)
    assert client.writes == []


@pytest.mark.parametrize("damage", ["head", "fork", "base", "draft", "closed", "code", "other_batch", "removed", "truncated"])
def test_unrelated_or_changed_pr_cannot_be_automerged(damage):
    client = FakeGitHub()
    if damage == "head":
        client.pr["head"]["sha"] = "d" * 40
    elif damage == "fork":
        client.pr["head"]["repo"]["full_name"] = "fork/repo"
    elif damage == "base":
        client.pr["base"]["ref"] = "other"
    elif damage == "draft":
        client.pr["draft"] = True
    elif damage == "closed":
        client.pr["state"] = "closed"
    elif damage == "code":
        client.files[0]["filename"] = ".github/workflows/test.yml"
    elif damage == "other_batch":
        client.files[0]["filename"] = "articles/public_release/manifests/DAILY-20260906.json"
    elif damage == "removed":
        client.files[0]["status"] = "removed"
    else:
        client.pr["changed_files"] = 101
    with pytest.raises(CloseoutError):
        finish(client)
    assert client.writes == []


def test_head_moving_after_verification_is_not_merged():
    client = FakeGitHub()
    client.move_after_verification = True
    with pytest.raises(CloseoutError, match="head moved"):
        finish(client)
    assert not any(method == "PUT" for _, method, _ in client.writes)


def test_merge_refusal_is_failure_not_a_successful_handoff():
    client = FakeGitHub()
    client.merge_allowed = False
    with pytest.raises(CloseoutError, match="did not result"):
        finish(client)
    assert len([w for w in client.writes if w[1] == "PUT"]) == 12


def test_already_merged_same_head_is_idempotent():
    client = FakeGitHub()
    client.pr.update(state="closed", merged=True, merge_commit_sha="e" * 40)
    assert finish(client)["status"] == "already_merged"
    assert client.writes == []
