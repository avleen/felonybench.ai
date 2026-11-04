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

if os.environ.get("FAKE_GH_FAIL_CALL") and " ".join(args).startswith(os.environ["FAKE_GH_FAIL_CALL"]):
    print("simulated failure", file=sys.stderr)
    sys.exit(1)

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


def _run_open_prs(sandbox: dict, fake_pr_list: str = "[]", fail_marker: str | None = None, fail_call: str | None = None, closed_pr_list: str = "[]"):
    env = os.environ.copy()
    env["PATH"] = f"{sandbox['bin_dir']}{os.pathsep}{env.get('PATH', '')}"
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(sandbox["work"]), env.get("PYTHONPATH")]))
    env["FAKE_GH_LOG"] = str(sandbox["gh_log"])
    env["FAKE_PR_LIST"] = fake_pr_list
    env["FAKE_CLOSED_PR_LIST"] = closed_pr_list
    if fail_marker:
        env["FAKE_GH_FAIL_MARKER"] = fail_marker
    if fail_call:
        env["FAKE_GH_FAIL_CALL"] = fail_call
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


def _invalid_revision_of_a_ready_pr(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    incident["sources"] = []
    _write_incident(sandbox["work"], incident)
    return sandbox, incident, json.dumps([{"number": 9, "headRefName": f"agent/{incident['id']}", "isDraft": False, "labels": []}])


def test_an_invalid_revision_is_a_draft_even_if_a_later_step_fails(tmp_path, make_incident):
    sandbox, incident, open_list = _invalid_revision_of_a_ready_pr(tmp_path, make_incident)

    assert _run_open_prs(sandbox, fake_pr_list=open_list, fail_call="pr comment").returncode == 1

    assert f"agent/{incident['id']}" in _remote_branches(sandbox["origin"])
    assert ["pr", "ready", "9", "--undo"] in _gh_calls(sandbox)


def test_an_invalid_revision_is_not_pushed_if_the_pr_cant_be_made_a_draft(tmp_path, make_incident):
    sandbox, incident, open_list = _invalid_revision_of_a_ready_pr(tmp_path, make_incident)

    assert _run_open_prs(sandbox, fake_pr_list=open_list, fail_call="pr ready 9 --undo").returncode == 1

    assert f"agent/{incident['id']}" not in _remote_branches(sandbox["origin"])


def test_a_ready_pr_stays_ready_if_it_cant_be_labelled(tmp_path, make_incident):
    # A retry skips the labels once the PR is a draft, so a draft must mean they were added.
    sandbox, incident, open_list = _invalid_revision_of_a_ready_pr(tmp_path, make_incident)

    assert _run_open_prs(sandbox, fake_pr_list=open_list, fail_call="pr edit 9 --add-label").returncode == 1

    assert ["pr", "ready", "9", "--undo"] not in _gh_calls(sandbox)
    assert f"agent/{incident['id']}" not in _remote_branches(sandbox["origin"])


def test_a_ready_pr_that_loses_its_only_news_source_is_awaiting_news(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    incident["sources"] = [s for s in incident["sources"] if s["kind"] != "news"]
    _write_incident(sandbox["work"], incident)
    labels = [{"name": "agent"}]
    open_list = json.dumps([{"number": 9, "headRefName": f"agent/{incident['id']}", "isDraft": False, "labels": labels}])

    assert _run_open_prs(sandbox, fake_pr_list=open_list).returncode == 0

    calls = _gh_calls(sandbox)
    assert ["pr", "ready", "9", "--undo"] in calls
    assert ["pr", "edit", "9", "--add-label", "awaiting-news"] in calls
    assert ["pr", "edit", "9", "--add-label", "needs-review"] not in calls


def test_a_draft_that_gets_news_but_is_low_confidence_becomes_ready_with_needs_review(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x", confidence="low")
    _write_incident(sandbox["work"], incident)
    labels = [{"name": "agent"}, {"name": "awaiting-news"}]
    open_list = json.dumps([{"number": 9, "headRefName": f"agent/{incident['id']}", "isDraft": True, "labels": labels}])

    assert _run_open_prs(sandbox, fake_pr_list=open_list).returncode == 0

    calls = _gh_calls(sandbox)
    assert ["pr", "ready", "9"] in calls
    assert ["pr", "edit", "9", "--add-label", "needs-review"] in calls
    assert ["pr", "edit", "9", "--remove-label", "awaiting-news"] in calls
    assert ["pr", "edit", "9", "--remove-label", "needs-review"] not in calls


def test_a_ready_pr_revised_to_low_confidence_gets_needs_review_and_stays_ready(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x", confidence="low")
    _write_incident(sandbox["work"], incident)
    open_list = json.dumps([{"number": 9, "headRefName": f"agent/{incident['id']}", "isDraft": False, "labels": [{"name": "agent"}]}])

    assert _run_open_prs(sandbox, fake_pr_list=open_list).returncode == 0

    calls = _gh_calls(sandbox)
    assert ["pr", "edit", "9", "--add-label", "needs-review"] in calls
    assert ["pr", "ready", "9", "--undo"] not in calls


def test_a_low_confidence_revision_is_labelled_even_if_a_later_step_fails(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x", confidence="low")
    _write_incident(sandbox["work"], incident)
    open_list = json.dumps([{"number": 9, "headRefName": f"agent/{incident['id']}", "isDraft": False, "labels": [{"name": "agent"}]}])

    assert _run_open_prs(sandbox, fake_pr_list=open_list, fail_call="pr comment").returncode == 1

    assert ["pr", "edit", "9", "--add-label", "needs-review"] in _gh_calls(sandbox)


def test_a_draft_awaiting_news_that_gets_another_error_stops_saying_so(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    incident["sources"] = []
    _write_incident(sandbox["work"], incident)
    labels = [{"name": "agent"}, {"name": "awaiting-news"}]
    open_list = json.dumps([{"number": 9, "headRefName": f"agent/{incident['id']}", "isDraft": True, "labels": labels}])

    assert _run_open_prs(sandbox, fake_pr_list=open_list).returncode == 0

    calls = _gh_calls(sandbox)
    assert ["pr", "edit", "9", "--add-label", "needs-review"] in calls
    assert ["pr", "edit", "9", "--remove-label", "awaiting-news"] in calls


def test_a_ready_pr_left_with_awaiting_news_is_repaired_on_its_next_update(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    labels = [{"name": "agent"}, {"name": "awaiting-news"}, {"name": "needs-review"}]
    open_list = json.dumps([{"number": 9, "headRefName": f"agent/{incident['id']}", "isDraft": False, "labels": labels}])

    assert _run_open_prs(sandbox, fake_pr_list=open_list).returncode == 0

    calls = _gh_calls(sandbox)
    assert ["pr", "edit", "9", "--remove-label", "awaiting-news"] in calls
    assert ["pr", "edit", "9", "--remove-label", "needs-review"] not in calls  # a person may have asked for it


def test_an_existing_pr_is_never_given_the_agent_label(tmp_path, make_incident):
    # The head branch name can match someone else's PR, and the label marks rejected agent proposals.
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    open_list = json.dumps([{"number": 9, "headRefName": f"agent/{incident['id']}", "isDraft": False, "labels": []}])

    assert _run_open_prs(sandbox, fake_pr_list=open_list).returncode == 0

    assert ["pr", "edit", "9", "--add-label", "agent"] not in _gh_calls(sandbox)


def test_a_fork_pr_with_the_same_branch_name_is_left_alone(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    open_list = json.dumps([{"number": 9, "headRefName": f"agent/{incident['id']}", "isDraft": True, "labels": [], "isCrossRepository": True}])

    assert _run_open_prs(sandbox, fake_pr_list=open_list).returncode == 0

    calls = _gh_calls(sandbox)
    assert _calls(calls, "pr", "create")
    assert not [c for c in calls if "9" in c]


def test_a_file_that_isnt_utf8_doesnt_cost_the_run_its_other_prs(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    (sandbox["work"] / "incidents" / "2026-06-02-openai-y.yaml").write_bytes(b"org: \xff\n")

    assert _run_open_prs(sandbox).returncode == 1

    assert len(_calls(_gh_calls(sandbox), "pr", "create")) == 1
    assert f"agent/{incident['id']}" in _remote_branches(sandbox["origin"])


def test_a_resubmitted_rejected_incident_is_flagged(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    closed = json.dumps([{"number": 55, "headRefName": f"agent/{incident['id']}", "mergedAt": None}])

    assert _run_open_prs(sandbox, closed_pr_list=closed).returncode == 0

    create = next(c for c in _gh_calls(sandbox) if c[:2] == ["pr", "create"])
    assert "#55" in create[create.index("--body") + 1]
    assert "needs-review" in create


def test_a_rejected_incident_keeps_needs_review_when_its_draft_becomes_ready(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    branch = f"agent/{incident['id']}"
    closed = json.dumps([{"number": 55, "headRefName": branch, "mergedAt": None}])
    labels = [{"name": "agent"}, {"name": "awaiting-news"}, {"name": "needs-review"}]
    draft = json.dumps([{"number": 9, "headRefName": branch, "isDraft": True, "labels": labels}])

    assert _run_open_prs(sandbox, fake_pr_list=draft, closed_pr_list=closed).returncode == 0

    calls = _gh_calls(sandbox)
    assert ["pr", "edit", "9", "--remove-label", "awaiting-news"] in calls
    assert ["pr", "edit", "9", "--remove-label", "needs-review"] not in calls


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


def test_a_file_of_yaml_aliases_fails_alone_without_expanding(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    levels = "".join(f"a{n}: &a{n} [*a{n - 1}, *a{n - 1}]\n" for n in range(1, 41))
    bomb = f"a0: &a0 [x, x]\n{levels}org: *a40\nsummary: *a40\n"
    (sandbox["work"] / "incidents" / "2026-06-02-openai-y.yaml").write_text(bomb)

    result = _run_open_prs(sandbox)
    assert result.returncode == 1
    assert "ComposerError" in result.stderr and "line 2" in result.stderr  # says where, not a memory address

    assert len(_calls(_gh_calls(sandbox), "pr", "create")) == 1


@pytest.mark.parametrize("content", [b"caf\xff\n", b"caf\x00e\n", b"caf" + b"\xff" * 64000])
def test_bad_notes_dont_cost_the_incident_its_pr(tmp_path, make_incident, content):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    notes = sandbox["work"] / ".agent-out"
    notes.mkdir(exist_ok=True)
    (notes / f"{incident['id']}.md").write_bytes(content)

    assert _run_open_prs(sandbox).returncode == 0

    create = _calls(_gh_calls(sandbox), "pr", "create")
    assert len(create) == 1
    assert "caf" in create[0][create[0].index("--body") + 1]


@pytest.mark.parametrize("change", [
    {"victims": [{"name": 5}]},
    {"victims": "foo"},
    {"id": None},
])
def test_an_invalid_incident_opens_a_draft_listing_its_errors(tmp_path, make_incident, change):
    sandbox = _make_sandbox(tmp_path)
    incident = {**make_incident(id="2026-06-01-openai-x"), **change}
    path = sandbox["work"] / "incidents" / "2026-06-01-openai-x.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(yaml.safe_dump(incident))

    assert _run_open_prs(sandbox).returncode == 0

    create = _calls(_gh_calls(sandbox), "pr", "create")
    assert len(create) == 1 and "--draft" in create[0]
    assert "❌ Failed" in create[0][create[0].index("--body") + 1]


def test_a_lone_surrogate_in_the_org_doesnt_cost_the_incident_its_pr(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x", org="\ud800x")
    (sandbox["work"] / "incidents" / "2026-06-01-openai-x.yaml").write_text(yaml.safe_dump(incident))

    assert _run_open_prs(sandbox).returncode == 0

    create = _calls(_gh_calls(sandbox), "pr", "create")
    assert create[0][create[0].index("--title") + 1].startswith("New felony: ?x")
    assert "--draft" in create[0]
    assert "surrogate" in create[0][create[0].index("--body") + 1]


def test_a_filename_that_isnt_utf8_only_costs_itself_its_pr(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    (sandbox["work"] / "incidents" / os.fsdecode(b"\xff.yaml")).write_text("id: x\n")

    result = _run_open_prs(sandbox)

    assert result.returncode == 1
    assert "Skipped" in result.stderr
    assert len(_calls(_gh_calls(sandbox), "pr", "create")) == 1


@pytest.mark.parametrize("empty", [None, "", "\0"])
def test_an_update_with_an_empty_id_is_titled_from_its_filename(tmp_path, make_incident, empty):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    _run_git(sandbox["work"], "add", "-A")
    _run_git(sandbox["work"], "commit", "-m", "seed")
    _run_git(sandbox["work"], "push", "origin", "main")
    incident["id"] = empty
    (sandbox["work"] / "incidents" / "2026-06-01-openai-x.yaml").write_text(yaml.safe_dump(incident))

    assert _run_open_prs(sandbox).returncode == 0

    create = _calls(_gh_calls(sandbox), "pr", "create")
    assert create[0][create[0].index("--title") + 1] == "Update: 2026-06-01-openai-x"


def test_notes_with_only_nuls_fall_back_to_the_summary(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x", summary="The summary.")
    _write_incident(sandbox["work"], incident)
    _write_notes(sandbox["work"], incident["id"], "\0\0\n")

    assert _run_open_prs(sandbox).returncode == 0

    create = _calls(_gh_calls(sandbox), "pr", "create")
    assert "> The summary." in create[0][create[0].index("--body") + 1]


def test_a_yaml_error_cant_forge_a_workflow_command_in_the_log(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    (sandbox["work"] / "incidents" / "2026-06-01-openai-x.yaml").write_text("::error title=x::forged: y: z\n")

    result = _run_open_prs(sandbox)

    assert result.returncode == 1
    assert "forged" in result.stderr
    assert not any(line.lstrip().startswith("::") for line in result.stderr.splitlines())


def test_an_update_with_no_id_is_titled_from_its_filename(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    _write_incident(sandbox["work"], incident)
    _run_git(sandbox["work"], "add", "-A")
    _run_git(sandbox["work"], "commit", "-m", "seed")
    _run_git(sandbox["work"], "push", "origin", "main")
    del incident["id"]
    (sandbox["work"] / "incidents" / "2026-06-01-openai-x.yaml").write_text(yaml.safe_dump(incident))

    assert _run_open_prs(sandbox).returncode == 0

    create = _calls(_gh_calls(sandbox), "pr", "create")
    assert create[0][create[0].index("--title") + 1] == "Update: 2026-06-01-openai-x"


def test_a_long_title_opens_a_pr_with_a_title_github_accepts(tmp_path, make_incident):
    sandbox = _make_sandbox(tmp_path)
    incident = make_incident(id="2026-06-01-openai-x")
    incident["victims"] = [{**incident["victims"][0], "name": f"Victim {n} " + "x" * 80} for n in range(9)]
    _write_incident(sandbox["work"], incident)

    assert _run_open_prs(sandbox).returncode == 0

    create = _calls(_gh_calls(sandbox), "pr", "create")
    assert len(create[0][create[0].index("--title") + 1]) == 256
