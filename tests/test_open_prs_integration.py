"""End-to-end test of scripts/open_prs.py against a sandboxed git remote.

Builds a throwaway bare "origin" repo and a clone ("work") containing just the
files open_prs.py needs (scripts/, rubric/, schema/, incidents/, .gitignore),
then runs `python -m scripts.open_prs` as a subprocess with a fake `gh` on
PATH. No network access and the real project repo is never touched.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

if shutil.which("git") is None:
    pytest.skip("git is not available", allow_module_level=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

FAKE_GH_SOURCE = """
import json
import os
import sys

args = sys.argv[1:]

if len(args) >= 2 and args[0] == "pr" and args[1] == "list":
    state = args[args.index("--state") + 1]
    assert "--limit" in args, "gh pr list silently stops at 30 results without --limit"
    print(os.environ.get("FAKE_CLOSED_PR_LIST" if state == "closed" else "FAKE_PR_LIST", "[]"))
    sys.exit(0)

log_path = os.environ["FAKE_GH_LOG"]
with open(log_path, "a") as f:
    f.write(json.dumps(args) + "\\n")

if len(args) >= 2 and args[0] == "pr" and args[1] == "create":
    marker = os.environ.get("FAKE_GH_FAIL_MARKER")
    if marker and "--title" in args and marker in args[args.index("--title") + 1]:
        print("simulated transport failure", file=sys.stderr)
        sys.exit(1)

sys.exit(0)
"""


def _run_git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _make_sandbox(tmp_path: Path) -> dict:
    """Build a bare origin repo and a `work` clone seeded with project files."""
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    _run_git(tmp_path, "init", "--bare", "-b", "main", str(origin))
    _run_git(tmp_path, "clone", str(origin), str(work))
    _run_git(work, "config", "user.email", "agent@example.com")
    _run_git(work, "config", "user.name", "FelonyBench Agent")

    shutil.copytree(PROJECT_ROOT / "scripts", work / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(PROJECT_ROOT / "rubric", work / "rubric")
    shutil.copytree(PROJECT_ROOT / "schema", work / "schema")
    (work / "incidents").mkdir()
    shutil.copy(PROJECT_ROOT / "incidents" / ".gitkeep", work / "incidents" / ".gitkeep")
    shutil.copy(PROJECT_ROOT / "incidents" / "LICENSE.md", work / "incidents" / "LICENSE.md")
    shutil.copy(PROJECT_ROOT / ".gitignore", work / ".gitignore")

    _run_git(work, "add", "-A")
    _run_git(work, "commit", "-m", "seed sandbox repo")
    _run_git(work, "push", "origin", "HEAD:main")

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh_path = bin_dir / "gh"
    gh_path.write_text(f"#!{sys.executable}\n{FAKE_GH_SOURCE}")
    gh_path.chmod(0o755)

    gh_log = tmp_path / "gh_log.jsonl"

    return {"origin": origin, "work": work, "bin_dir": bin_dir, "gh_log": gh_log}


def _write_incident(work: Path, incident: dict) -> Path:
    path = work / "incidents" / f"{incident['id']}.yaml"
    path.write_text(yaml.safe_dump(incident, sort_keys=False))
    return path


def _write_notes(work: Path, incident_id: str, text: str) -> None:
    notes_dir = work / ".agent-out"
    notes_dir.mkdir(exist_ok=True)
    (notes_dir / f"{incident_id}.md").write_text(text)


def _run_open_prs(sandbox: dict, fake_pr_list: str = "[]", fail_marker: str | None = None, closed_pr_list: str = "[]"):
    env = os.environ.copy()
    env["PATH"] = f"{sandbox['bin_dir']}{os.pathsep}{env.get('PATH', '')}"
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(sandbox["work"]), env.get("PYTHONPATH")]))
    env["FAKE_GH_LOG"] = str(sandbox["gh_log"])
    env["FAKE_PR_LIST"] = fake_pr_list
    env["FAKE_CLOSED_PR_LIST"] = closed_pr_list
    if fail_marker:
        env["FAKE_GH_FAIL_MARKER"] = fail_marker
    return subprocess.run(
        [sys.executable, "-m", "scripts.open_prs"],
        cwd=sandbox["work"],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _gh_calls(sandbox: dict) -> list[list[str]]:
    if not sandbox["gh_log"].exists():
        return []
    return [json.loads(line) for line in sandbox["gh_log"].read_text().splitlines() if line.strip()]


def _calls(calls: list[list[str]], *prefix: str) -> list[list[str]]:
    return [c for c in calls if c[: len(prefix)] == list(prefix)]


def _arg(call: list[str], flag: str) -> str:
    return call[call.index(flag) + 1]


def _remote_branches(origin: Path) -> set[str]:
    out = subprocess.run(
        ["git", "--git-dir", str(origin), "branch", "--format=%(refname:short)"],
        check=True, capture_output=True, text=True,
    ).stdout
    return {line.strip() for line in out.splitlines() if line.strip()}


def test_new_valid_incident_opens_a_pr(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident()
    _write_incident(sandbox["work"], incident)
    _write_notes(sandbox["work"], incident["id"], "Investigated thoroughly and confirmed the sources.")

    result = _run_open_prs(sandbox)
    assert result.returncode == 0, result.stderr

    branch = f"agent/{incident['id']}"
    assert branch in _remote_branches(sandbox["origin"])

    commit_count = subprocess.run(
        ["git", "--git-dir", str(sandbox["origin"]), "rev-list", "--count", f"main..{branch}"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    assert commit_count == "1"

    changed = subprocess.run(
        ["git", "--git-dir", str(sandbox["origin"]), "diff", "--name-only", "main", branch],
        check=True, capture_output=True, text=True,
    ).stdout.split()
    assert changed == [f"incidents/{incident['id']}.yaml"]

    calls = _gh_calls(sandbox)
    creates = _calls(calls, "pr", "create")
    assert len(creates) == 1
    create = creates[0]
    assert _arg(create, "--title") == "New felony: OpenAI — Hugging Face"
    assert "--label" in create and "agent" in create
    body = _arg(create, "--body")
    assert "Investigated thoroughly and confirmed the sources." in body
    assert "✅" in body


def test_disallowed_path_refuses_without_touching_remote(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident()
    _write_incident(sandbox["work"], incident)
    (sandbox["work"] / "other.txt").write_text("not allowed")

    result = _run_open_prs(sandbox)
    assert result.returncode == 1

    assert _remote_branches(sandbox["origin"]) == {"main"}
    assert _gh_calls(sandbox) == []


def test_open_pr_gets_a_comment_not_a_new_pr(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident()
    _write_incident(sandbox["work"], incident)
    branch = f"agent/{incident['id']}"
    fake_pr_list = json.dumps([{"number": 7, "headRefName": branch}])

    result = _run_open_prs(sandbox, fake_pr_list=fake_pr_list)
    assert result.returncode == 0, result.stderr

    calls = _gh_calls(sandbox)
    assert _calls(calls, "pr", "create") == []
    comments = _calls(calls, "pr", "comment", "7")
    assert len(comments) == 1


def test_one_incident_failing_does_not_block_the_rest(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    failing = make_incident(id="2026-07-10-failco-widget-breach", org="FailCo")
    ok = make_incident()
    _write_incident(sandbox["work"], failing)
    _write_incident(sandbox["work"], ok)

    result = _run_open_prs(sandbox, fail_marker="FailCo")
    assert result.returncode == 1

    calls = _gh_calls(sandbox)
    creates = _calls(calls, "pr", "create")
    titles = [_arg(c, "--title") for c in creates]
    assert "New felony: OpenAI — Hugging Face" in titles

    branch = f"agent/{ok['id']}"
    assert branch in _remote_branches(sandbox["origin"])


def test_invalid_incident_gets_needs_review_label(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(sources=[])
    _write_incident(sandbox["work"], incident)

    result = _run_open_prs(sandbox)
    assert result.returncode == 0, result.stderr

    calls = _gh_calls(sandbox)
    creates = _calls(calls, "pr", "create")
    assert len(creates) == 1
    create = creates[0]
    labels = [create[i + 1] for i, a in enumerate(create) if a == "--label"]
    assert set(labels) == {"agent", "needs-review"}
    body = _arg(create, "--body")
    assert "❌" in body


def test_awaiting_news_draft_is_marked_ready_when_news_arrives(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident()  # has a news source, so it now validates cleanly
    _write_incident(sandbox["work"], incident)
    branch = f"agent/{incident['id']}"
    fake_pr_list = json.dumps([{"number": 9, "headRefName": branch, "isDraft": True, "labels": [{"name": "agent"}, {"name": "awaiting-news"}]}])

    result = _run_open_prs(sandbox, fake_pr_list=fake_pr_list)
    assert result.returncode == 0, result.stderr

    calls = _gh_calls(sandbox)
    assert len(_calls(calls, "pr", "ready", "9")) == 1
    assert ["pr", "edit", "9", "--remove-label", "awaiting-news"] in calls


def test_missing_news_opens_a_draft(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident()
    incident["sources"] = [s for s in incident["sources"] if s["kind"] != "news"]
    _write_incident(sandbox["work"], incident)

    result = _run_open_prs(sandbox)
    assert result.returncode == 0, result.stderr

    create = _calls(_gh_calls(sandbox), "pr", "create")
    assert len(create) == 1 and "--draft" in create[0]
    labels = [create[0][i + 1] for i, a in enumerate(create[0]) if a == "--label"]
    assert labels == ["agent", "awaiting-news"]


def test_invalid_incident_is_opened_as_a_draft(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(sources=[])
    _write_incident(sandbox["work"], incident)

    result = _run_open_prs(sandbox)
    assert result.returncode == 0, result.stderr

    create = _calls(_gh_calls(sandbox), "pr", "create")
    assert len(create) == 1 and "--draft" in create[0]


def _branch_files(sandbox: dict, branch: str) -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", "origin/main", f"origin/{branch}"],
        cwd=sandbox["work"], check=True, capture_output=True, text=True,
    ).stdout
    return out.split()


@pytest.mark.parametrize("bad_text", [
    "{",  # malformed YAML
    "",  # empty
    "- a\n- list\n",  # not a mapping
    "id: x\n",  # missing most fields
])
def test_a_bad_file_does_not_cost_other_incidents_their_prs(tmp_path, make_incident, bad_text):
    sandbox = _make_sandbox(tmp_path)
    (sandbox["work"] / "incidents" / "0000-bad.yaml").write_text(bad_text)
    good = make_incident(id="2026-06-01-openai-good")
    _write_incident(sandbox["work"], good)

    result = _run_open_prs(sandbox)

    created = [c for c in _gh_calls(sandbox) if c[:2] == ["pr", "create"]]
    assert any(f"agent/{good['id']}" in c for c in created), result.stderr


def test_each_pr_contains_only_its_own_incident(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    a = make_incident(id="2026-06-01-openai-a")
    b = make_incident(id="2026-06-02-openai-b")
    _write_incident(sandbox["work"], a)
    _write_incident(sandbox["work"], b)

    assert _run_open_prs(sandbox).returncode == 0

    subprocess.run(["git", "fetch", "origin"], cwd=sandbox["work"], check=True, capture_output=True)
    assert _branch_files(sandbox, f"agent/{a['id']}") == [f"incidents/{a['id']}.yaml"]
    assert _branch_files(sandbox, f"agent/{b['id']}") == [f"incidents/{b['id']}.yaml"]


def test_a_ready_pr_that_becomes_invalid_goes_back_to_draft(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    incident["sources"] = []
    _write_incident(sandbox["work"], incident)
    open_list = json.dumps([{"number": 9, "headRefName": f"agent/{incident['id']}", "isDraft": False, "labels": []}])

    assert _run_open_prs(sandbox, fake_pr_list=open_list).returncode == 0

    calls = _gh_calls(sandbox)
    assert ["pr", "ready", "9", "--undo"] in calls
    assert ["pr", "edit", "9", "--add-label", "needs-review"] in calls
    edit = next(c for c in calls if c[:3] == ["pr", "edit", "9"] and "--body" in c)
    assert "❌ Failed" in edit[edit.index("--body") + 1]


def test_a_resubmitted_rejected_incident_is_flagged(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    closed = json.dumps([{"number": 55, "headRefName": f"agent/{incident['id']}", "mergedAt": None}])

    assert _run_open_prs(sandbox, closed_pr_list=closed).returncode == 0

    create = next(c for c in _gh_calls(sandbox) if c[:2] == ["pr", "create"])
    assert "#55" in create[create.index("--body") + 1]
    assert "needs-review" in create


def test_a_merged_pr_does_not_count_as_rejected(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    closed = json.dumps([{"number": 55, "headRefName": f"agent/{incident['id']}", "mergedAt": "2026-01-01T00:00:00Z"}])

    assert _run_open_prs(sandbox, closed_pr_list=closed).returncode == 0

    create = next(c for c in _gh_calls(sandbox) if c[:2] == ["pr", "create"])
    assert "#55" not in create[create.index("--body") + 1]


def test_files_outside_the_incident_layout_are_reported_not_dropped(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    (sandbox["work"] / "incidents" / "notes.yml").write_text("a: 1\n")

    result = _run_open_prs(sandbox)

    assert result.returncode == 1
    assert "notes.yml" in result.stderr
